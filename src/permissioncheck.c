#define _GNU_SOURCE
#include <dirent.h>
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
#define RED           "\033[0;31m"
#define GREEN         "\033[0;32m"

// global variables
int verbose_mode = 0;
gid_t xware_gid = -1;
uid_t xware_uid = -1;
gid_t grpList1[NGROUPS_MAX];
int nGrpList1 = NGROUPS_MAX;
gid_t grpList2[NGROUPS_MAX];
int nGrpList2 = NGROUPS_MAX;

int matchAll(struct libmnt_fs* a, void* b) {
    // match all fs
    return 1;
}

int xdaccess(const char* path, const int mode) {
    // wrapper for access/eaccess
    // as of glibc 2.19, eaccess doesn't test ACLs.
    // access seems to support ACLs, but it performs tests based on real uid/gid, ignoring euid/egid.
    // so for now, permissioncheck REQUIRES CAP_SETUID and CAP_SETGID capabilities.
    // solely setting SUID/SGID won't work!
    char modestr[3] = {0};
    modestr[0] = (mode & R_OK) ? 'r' : ' ';
    modestr[1] = (mode & W_OK) ? 'w' : ' ';
    modestr[2] = (mode & X_OK) ? 'x' : ' ';

    if (verbose_mode) {
        printf("# [DEBUG] access %s on %s\n", modestr, path);
    }

    int result = access(path, mode);
    if (result == -1) {
        if (errno == EACCES) {
            printf("%s对%s需要%s权限，未满足。%s\n", RED, path, modestr, NOSTYLE);
        } else if (errno == ENOENT) {
            printf("%s%s不存在。%s\n", RED, path, NOSTYLE);
        } else {
            printf("%s对%s检测失败。错误码：%u。%s\n", RED, path, errno, NOSTYLE);
        }
    }
    return result;
}

int checkTargetDirPermissions(const char* path) {
    int ret;
    ret = xdaccess(path, W_OK | X_OK);
    if (ret == -1) {
        return 0;
    }

    // TDDOWNLOAD
    char pTDDOWNLOAD[PATH_MAX];
    sprintf(pTDDOWNLOAD, "%s/TDDOWNLOAD", path);
    ret = xdaccess(pTDDOWNLOAD, W_OK | X_OK) | ret;

    // ThunderDB
    char pThunderDB[PATH_MAX];
    sprintf(pThunderDB, "%s/ThunderDB", path);
    ret = xdaccess(pThunderDB, W_OK | X_OK) | ret;

    char pThunderDBsqlite[PATH_MAX];
    sprintf(pThunderDBsqlite, "%s/ThunderDB/etm_task_store.db", path);
    ret = xdaccess(pThunderDBsqlite, R_OK | W_OK) | ret;

    char pThunderUuid[PATH_MAX];
    sprintf(pThunderUuid, "%s/ThunderDB/uuid", path);
    ret = xdaccess(pThunderUuid, R_OK | W_OK) | ret;

    if (ret == 0) {
        printf("%s正常。%s\n", GREEN, NOSTYLE);
        return 1;
    } else {
        return 0;
    }
}

int checkDirXPermissions(const char* dirpath) {
    if (strcmp(dirpath, "/") == 0) {
        return (xdaccess("/", X_OK) == 0);
    } else {
        char tmp[PATH_MAX] = {0};
        strncpy(tmp, dirpath, PATH_MAX);
        char* parentpath = dirname(tmp);
        if (checkDirXPermissions(parentpath)) {
            return (xdaccess(dirpath, X_OK) == 0);
        } else {
            return 0;
        }
    }
}

void clearSupplementaryGroups() {
    // get groups user 'xware' belongs to, save to global 'grpList1'

    if (getgrouplist("xware", xware_gid, grpList1, &nGrpList1) == -1) { // getgrouplist returns the groups a user belongs to
        perror("getgrouplist");
        exit(EXIT_FAILURE);
    }

    // Clear all non-xware groups
    int ret = setgroups(nGrpList1, grpList1);
    if (ret != 0) {
        perror("setgroups");
        exit(EXIT_FAILURE);
    }
}

void selfCheck() {
    // 'access' function tests based on uid, 'eaccess' ignores ACLs, have to set uid/gid.
    setgid(xware_gid);
    setuid(xware_uid); // uid after gid, otherwise fail on setting gid.

    if (verbose_mode) {
        printf("# [DEBUG] uid=%d, euid=%d, xware_uid=%d\n", getuid(), geteuid(), xware_uid);
    }
    // check uid
    if (getuid() != xware_uid) {
        fprintf(stderr, "Not running as xware user.\n");
        exit(EXIT_FAILURE);
    }

    // check euid
    if (geteuid() != xware_uid) {
        fprintf(stderr, "Not running as xware user.\n");
        exit(EXIT_FAILURE);
    }


    if (verbose_mode) {
        printf("# [DEBUG] gid=%d, egid=%d, xware_gid=%d\n", getgid(), getegid(), xware_gid);
    }
    // check gid
    if (getgid() != xware_gid) {
        fprintf(stderr, "Not running as xware group.\n");
        exit(EXIT_FAILURE);
    }
    // check egid
    if (getegid() != xware_gid) {
        fprintf(stderr, "Not running as xware group.\n");
        exit(EXIT_FAILURE);
    }

    // check supplementary groups
    nGrpList2 = getgroups(NGROUPS_MAX, grpList2);
    if (nGrpList2 == -1) {
        perror("getgroups");
        exit(EXIT_FAILURE);
    }
    if (verbose_mode) {
        printf("# [DEBUG] xware is a member of: ");
        int i = 0;
        for (i = 0; i < nGrpList1; i++) {
            printf("%d\t", grpList1[i]);
        }
        printf("\n");

        printf("# [DEBUG] post-setgroups, calling process groups: ");
        for (i = 0; i < nGrpList2; i++) {
            printf("%d\t", grpList2[i]);
        }
        printf("\n");
    }
    if ( (nGrpList1 != nGrpList2) ||
         (memcmp(grpList1, grpList2, nGrpList2 * sizeof(gid_t)) != 0)) {
        fprintf(stderr, "Failed to clear supplementary groups.\n");
        exit(EXIT_FAILURE);
    }
}

void prepare() {
    if (getuid() == 0) {
        printf("# 提示：本程序不需root使用。\n");
    }

    // get uid, gid of 'xware'
    struct passwd* usrInfo = getpwnam("xware");
    if (usrInfo == NULL) {
        perror("getpwnam");
        exit(EXIT_FAILURE);
    }
    xware_uid = usrInfo->pw_uid;
    xware_gid = usrInfo->pw_gid;
}


int main(const int argc, const char* argv[]) {
    if (argc == 2) {
        if (strcmp(argv[1], "--verbose") == 0) {
            verbose_mode = 1;
        }
    }

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
                if (checkDirXPermissions(target)) {
                    checkTargetDirPermissions(target);
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
