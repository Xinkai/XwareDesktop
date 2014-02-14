#define _GNU_SOURCE
#include <dirent.h>
#include <fcntl.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <libgen.h>
#include <unistd.h>
#include <grp.h>
#include <pwd.h>
#include <libmount/libmount.h>

#define NOSTYLE       "\033[0m"
#define BOLD          "\033[1;38m"
#define RED            "\033[0;31m"
#define GREEN       "\033[0;32m"

// global variables
const char* PROBENAME = "XwareDesktopPermissionProbe";

gid_t xware_gid = -1;
uid_t xware_uid = -1;
gid_t grpList1[NGROUPS_MAX];

int matchAll(struct libmnt_fs* a, void* b) {
    // match all fs
    return 1;
}

int checkWritePermission(const char* path) {
    char probepath[PATH_MAX];
    strcpy(probepath, path);
    unsigned long destDirPathLength = strlen(path);
    if (!strcmp(&path[destDirPathLength - 1], "/") == 0) {
        strcat(probepath, "/");
    }
    strcat(probepath, PROBENAME);

    int fd = open(probepath, O_CREAT | O_RDWR, 0660);
    if (fd == -1) {
        if (errno == EACCES) {
            printf("%s无法读写文件。xware用户对路径没有读写权限。%s\n", RED, NOSTYLE);
        } else {
            printf("%s无法读写文件。错误码：%u。%s\n", RED, errno, NOSTYLE);
        }
        return 0;
    } else {
        close(fd);
        remove(probepath);
        printf("%s正常。%s\n", GREEN, NOSTYLE);
        return 1;
    }
}

int checkDirPermission(const char* dirpath) {
    if (strcmp(dirpath, "/") == 0) {
        return (chdir("/") == 0);
    } else {
        char tmp[PATH_MAX];
        strncpy(tmp, dirpath, PATH_MAX);
        char* parentpath = dirname(tmp);
        if (checkDirPermission(parentpath)) {
            int ret = chdir(dirpath);
//            printf("#%s\n", dirpath);
            if (ret == 0) {
                return 1;
            } else {
                if (errno == EACCES) {
                    printf("%s无法打开文件夹%s。检查文件夹x权限。%s\n", RED, dirpath, NOSTYLE);
                } else {
                    printf("%s无法打开文件夹%s。错误码：%u。%s\n", RED, dirpath, errno, NOSTYLE);
                }
                return 0;
            }
        } else {
            return 0;
        }

    }
}

void clearSupplementaryGroups() {
    // get groups user 'xware' belongs to, save to global 'grpList1'
    int grpCount = NGROUPS_MAX;

    if (getgrouplist("xware", xware_gid, grpList1, &grpCount) == -1) { // getgrouplist returns the groups a user belongs to
        perror("getgrouplist");
        exit(EXIT_FAILURE);
    }

    // Clear all non-xware groups
    int ret = setgroups(grpCount, grpList1);
    if (ret != 0) {
        perror("setgroups");
        exit(EXIT_FAILURE);
    }
}

void selfCheck() {
    // check euid
    if (geteuid() != xware_uid) {
        fprintf(stderr, "Not running as xware user.\n");
        exit(EXIT_FAILURE);
    }


    // check egid
    if (getegid() != xware_gid) {
        fprintf(stderr, "Not running as xware group.\n");
        exit(EXIT_FAILURE);
    }


    // check supplementary groups
    gid_t grpList2[NGROUPS_MAX];
    int grpCount = getgroups(NGROUPS_MAX, grpList2);
    if (grpCount == -1) {
        perror("getgroups");
        exit(EXIT_FAILURE);
    }
    if (memcmp(grpList1, grpList2, grpCount * sizeof(gid_t)) != 0) {
        fprintf(stderr, "Failed to clear supplementary groups.\n");
        exit(EXIT_FAILURE);
    }
}

void prepare() {
    // get uid, gid of 'xware'
    struct passwd* usrInfo = getpwnam("xware");
    if (strcmp(usrInfo->pw_name, "xware") == 0) {
        xware_uid = usrInfo->pw_uid;
        xware_gid = usrInfo->pw_gid;
    }
}


int main(const int argc, const char* argv[]) {
    prepare();
    clearSupplementaryGroups();
    selfCheck();

    struct libmnt_table* mt = mnt_new_table_from_file("/opt/xware_desktop/mounts");
    if (mt == NULL) {
        fprintf(stderr, "mnt_new_table_from_file failed.\n");
        exit(EXIT_FAILURE);
    }
    struct libmnt_iter* itr = mnt_new_iter(MNT_ITER_FORWARD);
    struct libmnt_fs* fs = NULL;

    while(1) {
        int tmp = mnt_table_find_next_fs(mt, itr, &matchAll, NULL, &fs);
        if (tmp < 0) { // error
            fprintf(stderr, "mnt_table_find_next_fs failed.\n");
            break;
        } else {
            if (tmp == 1) { // reach EOF
                break;
            }
            const char* target = mnt_fs_get_target(fs);
            if (target == NULL) {
                fprintf(stderr, "mnt_fs_get_target failed.\n");
            } else {
                printf("%s%s%s\n", BOLD, target, NOSTYLE);
                printf("================================\n");
                if (checkDirPermission(target)) {
                    checkWritePermission(target);
                }
                printf("\n");
            }
        }
    }
    printf("%s", NOSTYLE);
    mnt_free_fs(fs);
    mnt_free_iter(itr);
    mnt_free_table(mt);
    return 0;
}
