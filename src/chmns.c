#define _GNU_SOURCE
#include <sched.h> // unshare
#include <sys/mount.h> // mount
#include <unistd.h> // execvp, getuid
#include <stdio.h> // stderr
#include <stdlib.h> // getenv, EXIT_FAILURE
#include <limits.h> // PATH_MAX
#include <pwd.h> // getpwuid
#include <string.h> // strcpy
#include <errno.h> // errno

char profileDir[PATH_MAX] = {0};
char** cmd = NULL;

void useDefaultProfileDir() {
    struct passwd* pw = getpwuid(getuid()); // getuid never fail
    if (pw == NULL) {
        // error
        perror("getpwuid");
        exit(EXIT_FAILURE);
    }
    strcpy(profileDir, pw->pw_dir);
    strcat(profileDir, "/.xware-desktop/profile");
}

void prepare() {
    int ret;
    ret = unshare(CLONE_NEWNS);
    if (ret) {
        perror("unshare");
        exit(EXIT_FAILURE);
    }

    // TODO: making / recursively private causes newly mounted volumes invisible by the mount namespace.
    // In the future, we should try to only make the related volume private.
    ret = mount("", "/", "Doesntmatter", MS_PRIVATE|MS_REC|MS_NODEV, NULL);
    if (ret) {
        perror("mount (making sure subtree '/' is private)");
        exit(EXIT_FAILURE);
    }
}

void mountDirs() {
    int ret;
    char tmpDir[PATH_MAX];

    strcpy(tmpDir, profileDir);
    strcat(tmpDir, "/tmp");

    ret = mount(tmpDir, "/tmp", "Doesntmatter", MS_BIND|MS_NOEXEC, NULL);
    if (ret) {
        perror("mount (bind:/tmp)");
        exit(EXIT_FAILURE);
    }
}

void run() {
    int ret;
    ret = setenv("XWARE-DESKTOP-CHMNS", "TRUE", 1);
    if (ret) {
        perror("setenv");
    }

    ret = execvp(cmd[0], cmd);
    if (ret) {
        perror("execvp");
        exit(EXIT_FAILURE);
    }
}

void usage() {
    printf("chmns - 切换挂载命名空间。(Xware Desktop组件)\n");
    printf("-------------------------\n");
    printf("\n");
    printf("用法：chmns [选项] 命令 [命令参数1] [命令参数2]...\n");
    printf("可选项：\n");
    printf("   --profile path\t\t指明Profile路径。如果省略，则使用~/.xware-desktop/profile\n");
    printf("   --help\t\t\t显示本帮助信息并退出\n");
}

int main(int argc, char** argv) {
    // prevent execute in a nested chmns
    char* nestedMark = getenv("XWARE-DESKTOP-CHMNS");
    if (nestedMark == NULL) {
        if (errno != 0) {
            perror("getenv");
            exit(EXIT_FAILURE);
        }
    } else {
        fprintf(stderr, "错误：已经载入chmns。\n");
        exit(EXIT_FAILURE);
    };

    // parsing arguments
    int cmdIndex;
    unsigned int isProfileDirSpecified = 0;

    if (argc <= 1) {
        fprintf(stderr, "错误：未提供命令。\n");
        usage();
        exit(EXIT_FAILURE);
    }
    if (strcmp(argv[1], "--profile") == 0) {
        isProfileDirSpecified = 1;
        strcpy(profileDir, argv[2]);
    } else if (strcmp(argv[1], "--help") == 0) {
        usage();
        exit(EXIT_SUCCESS);
    }

    if (isProfileDirSpecified) {
        cmdIndex = 3;
    } else {
        cmdIndex = 1;
        useDefaultProfileDir();
    }

    if (cmdIndex == argc) {
        // no cmd, quit.
        fprintf(stderr, "错误：没有提供命令。\n");
        usage();
        exit(EXIT_FAILURE);
    } else {
        cmd = argv + cmdIndex;
    }

    prepare();
    mountDirs();
    run();
    return 0;
}