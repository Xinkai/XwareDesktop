#define _GNU_SOURCE

#include <string.h>
#include <dlfcn.h>

const char* PROCMOUNTS = "/proc/mounts";
const char* XWARE_CONF_PATH = "/opt/xware_desktop/mounts";

int fopen64(const char* path, const char* mode) {
    int (*new_fopen64) (const char* path, const char* mode);
    int result;

    new_fopen64 = dlsym(RTLD_NEXT, "fopen64");
    if (strcmp(PROCMOUNTS, path) == 0) {
        // feed xware a fake instead of the real /proc/mounts
        puts("\nXware Desktop: FOPEN64 on /proc/mounts");
        result = new_fopen64(XWARE_CONF_PATH, mode);
    } else {
        // pass on this API call
        result = new_fopen64(path, mode);
    }

    return result;
}
