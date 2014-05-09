#define _GNU_SOURCE

#include <string.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits.h>

const char* PROC_MOUNTS = "/proc/mounts";
const char* XWARE_MOUNTS_PATH = "/opt/xware_desktop/mounts";

#define XD_PRINTF \
        int (*printf) (const char *__restrict __format, ...) = dlsym(RTLD_NEXT, "printf");

#define XD_PERROR \
        void (*perror) (const char *__s) = dlsym(RTLD_NEXT, "perror");

#define XD_SPRINTF \
        int (*sprintf) (char *__restrict __s, const char *__restrict __format, ...) = dlsym(RTLD_NEXT, "sprintf");

int fopen64(const char* path, const char* mode) {
    XD_PRINTF;

    int (*new_fopen64) (const char* path, const char* mode);
    int result;

    new_fopen64 = dlsym(RTLD_NEXT, "fopen64");
    if (strcmp(PROC_MOUNTS, path) == 0) {
        // feed xware a fake instead of the real /proc/mounts
        printf("\nXware Desktop: FOPEN64 on /proc/mounts");
        result = new_fopen64(XWARE_MOUNTS_PATH, mode);
    } else {
        // pass on this API call
        result = new_fopen64(path, mode);
    }

    return result;
}

mode_t umask(mode_t mask) {
    XD_PRINTF;

    mode_t (*new_umask) (mode_t mask);
    mode_t result;
    printf("Xware Desktop: UMASK %o to 006\n", mask);
    new_umask = dlsym(RTLD_NEXT, "umask");
    result = new_umask(006);
    return result;
}

int fchmod(const int fd, mode_t mode) {
    XD_PRINTF;
    XD_PERROR;
    XD_SPRINTF;

    int (*new_fchmod) (const int fd, mode_t mode);
    int result;

    new_fchmod = dlsym(RTLD_NEXT, "fchmod");
    mode_t new_mode;
    // find out what this fd points to
    struct stat fdstat;

    if (fstat(fd, &fdstat)) {
        new_mode = mode;
        perror("Xware Desktop: fstat inside fchmod");
        goto end;

    } else {
        // successfully get fd stat
        char fd_link_path[PATH_MAX];
        sprintf(fd_link_path, "/proc/self/fd/%u", fd);

        char fd_link_resolved_path[PATH_MAX] = {0};
        ssize_t tmp = readlink(fd_link_path, fd_link_resolved_path, PATH_MAX);
        if (tmp < 0) {
            new_mode = mode;
            perror("Xware Desktop: readlink");
            goto end;
        }

        if (tmp > PATH_MAX) {
            new_mode = mode;
            perror("Xware Desktop: readlink size insufficient");
            goto end;
        }

        if (S_ISREG(fdstat.st_mode)) {
            new_mode = mode & 0660;
            printf("Xware Desktop: FCHMOD on file (%o->%o)  %s\n", mode, new_mode, fd_link_resolved_path);
            goto end;

        } else if (S_ISDIR(fdstat.st_mode)) {
            new_mode = mode & 0771;
            printf("Xware Desktop: FCHMOD on dir (%o->%o)  %s\n", mode, new_mode, fd_link_resolved_path);
            goto end;

        } else {
            // for non-file, non-dir file-like objects like sockets, don't do anything
            new_mode = mode;
            goto end;
        }
    }

end:
    result = new_fchmod(fd, new_mode);
    return result;
}
