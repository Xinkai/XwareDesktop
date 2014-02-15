#define _GNU_SOURCE

#include <string.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <unistd.h>

const char* PROCMOUNTS = "/proc/mounts";
const char* XWARE_CONF_PATH = "/opt/xware_desktop/mounts";

int xdprint(const char* s) {
    size_t size = strlen(s);
    return write(1, s, size); // avoid using puts/printf, which come from stdio.h.
}

int fopen64(const char* path, const char* mode) {
    int (*new_fopen64) (const char* path, const char* mode);
    int result;

    new_fopen64 = dlsym(RTLD_NEXT, "fopen64");
    if (strcmp(PROCMOUNTS, path) == 0) {
        // feed xware a fake instead of the real /proc/mounts
        xdprint("\nXware Desktop: FOPEN64 on /proc/mounts\n");
        result = new_fopen64(XWARE_CONF_PATH, mode);
    } else {
        // pass on this API call
        result = new_fopen64(path, mode);
    }

    return result;
}

mode_t umask(mode_t mask) {
    mode_t (*new_umask) (mode_t mask);
    mode_t result;
    xdprint("\nXware Desktop: UMASK to 006\n");
    new_umask = dlsym(RTLD_NEXT, "umask");
    result = new_umask(006);
    return result;
}
