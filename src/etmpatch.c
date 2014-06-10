#define _GNU_SOURCE

#include <string.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits.h>
#include <libgen.h>
#include <stdlib.h> // getenv
#include <errno.h>

const char* PROC_MOUNTS = "/proc/mounts";
char XWARE_MOUNTS_PATH[PATH_MAX] = {0};
int XWARE_MOUNTS_PATH_INITIALIZED = 0;

#define fd_stderr 2

#define XD_PRINTF \
        int (*printf) (const char *__restrict __format, ...) = dlsym(RTLD_NEXT, "printf");

#define XD_DPRINTF \
        int (*dprintf) (int __fd, const char *__restrict __fmt, ...) __attribute__ ((__format__ (__printf__, 2, 3))) = dlsym(RTLD_NEXT, "dprintf");

#define XD_PERROR \
        void (*perror) (const char *__s) = dlsym(RTLD_NEXT, "perror");

#define XD_SPRINTF \
        int (*sprintf) (char *__restrict __s, const char *__restrict __format, ...) = dlsym(RTLD_NEXT, "sprintf");

int __init_xware_mounts_path() {
    XD_DPRINTF;

    char* tmp = getenv("XWARE-DESKTOP-CHMNS");
    if (tmp) {
        strcpy(XWARE_MOUNTS_PATH, tmp);
        strcat(XWARE_MOUNTS_PATH, "/etc/mounts");
        XWARE_MOUNTS_PATH_INITIALIZED = 1;
        return 1;
    } else {
        if (errno != 0) {
            dprintf(fd_stderr, "getenv with errno %d", errno);
        }
        return 0;
    }
}

int __resolve(const char* symlink, char* result) {
    XD_PERROR;
    XD_DPRINTF;

    ssize_t tmp = readlink(symlink, result, PATH_MAX);
    if (tmp < 0) {
        perror("readlink");
        return 0;
    } else if (tmp > PATH_MAX) {
        dprintf(fd_stderr, "readlink size insufficient\n");
        return 0;
    }
    return 1;
}

int __resolve_fd(const int fd, char* result) {
    XD_SPRINTF;

    char symlink[PATH_MAX] = {0};
    sprintf(symlink, "/proc/self/fd/%u", fd);
    return __resolve(symlink, result);
}

int fopen64(const char* path, const char* mode) {
    XD_PRINTF;

    int (*real_fopen64) (const char* path, const char* mode);
    int result;

    real_fopen64 = dlsym(RTLD_NEXT, "fopen64");
    if (strcmp(PROC_MOUNTS, path) == 0) {
        // feed xware a fake instead of the real /proc/mounts
        printf("\nXware Desktop: FOPEN64 on /proc/mounts");
        if (!XWARE_MOUNTS_PATH_INITIALIZED) {
            printf("\nXware Desktop: FAKE MOUNTS INIT...");
            __init_xware_mounts_path();
            printf("set to %s", XWARE_MOUNTS_PATH);
        }
        result = real_fopen64(XWARE_MOUNTS_PATH, mode);
    } else {
        // pass on this API call
        result = real_fopen64(path, mode);
    }

    return result;
}

mode_t umask(mode_t mask) {
    XD_PRINTF;

    printf("Xware Desktop: denied umask(%o)\n", mask);
    return 0;
}

int fchmod(const int fd, mode_t mode) {
    XD_PRINTF;

    char filename[PATH_MAX] = {0};
    int ok = __resolve_fd(fd, filename);
    if (ok) {
        printf("Xware Desktop: denied fchmod(%s(%d), %o)\n", filename, fd, mode);
    } else {
        printf("Xware Desktop: denied fchmod(fd, %o), but cannot resolve\n", mode);
    }

    return 0;
}

int chmod(const char* path, mode_t mode) {
    XD_PRINTF;

    printf("Xware Desktop: denied chmod(%s, %d)\n", path, mode);
    return 0;
}
