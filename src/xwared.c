#include "xwared.h"

void watchETM() {
    int status;
    waitpid(etmPid, &status, 0);
    printf("waitpid: %d\n", status);
}

void runETM() {
    while (toRunETM == 0) {
        sleep(1);
    } // if toRunETM is 0, then hold

    pthread_mutex_lock(&etmMutex);
    toRunETM = 1; // if ETM crashes, auto restart
    etmPid = fork();
    pthread_mutex_unlock(&etmMutex);

    if (etmPid < 0) {
        perror("Fork failed");
        exit(EXIT_FAILURE);
    } else if (etmPid == 0) {
        // child
        hookLibmounthelper();
        printf("child: pid(%d) ppid(%d)\n", getpid(), getppid());
        flock(fdETMLock, LOCK_EX | LOCK_NB);
        execv(etmArgv[0], etmArgv);
        flock(fdETMLock, LOCK_UN);
        perror("execve");
        exit(EXIT_FAILURE);
    } else {
        // parent
        printf("parent: pid(%d) cpid(%d)\n", getpid(), etmPid);
        watchETM();
    }
}

void endETM(const int restart) {
    pthread_mutex_lock(&etmMutex);
    if (etmPid == -1) {
        if (restart == 0) {
            printf("ETM not running, ignore ETM_STOP.\n");
        } else {
            printf("ETM not running, ignore ETM_RESTART.\n");
        }
    } else {
        toRunETM = restart;
        if (kill(etmPid, SIGTERM) == 0) {
            // successful
            etmPid = -1;
            flock(fdETMLock, LOCK_UN);
        } else {
            perror("kill ETM");
            exit(EXIT_FAILURE);
        }
    }
    pthread_mutex_unlock(&etmMutex);
}

void* threadListener() {
    printf("pthread listening\n");
    while(1) {
        int sdAccept = accept(sd, NULL, NULL);
        if (sdAccept < 0) {
            perror("accept failed");
            exit(EXIT_FAILURE);
        }

        char buffer[SOCKET_BUFFER_LENGTH];
        if (read(sdAccept, &buffer, SOCKET_BUFFER_LENGTH) == -1) {
            perror("read failed");
        }

        // dispatch
        if (strncmp(ETM_STOP, &buffer, SOCKET_BUFFER_LENGTH) == 0) {
            endETM(0);
        } else if (strncmp(&buffer, ETM_START, SOCKET_BUFFER_LENGTH) == 0){
            pthread_mutex_lock(&etmMutex);
            if (etmPid != -1) {
                printf("ETM running, ignore ETM_START");
            } else {
                toRunETM = 1;
            }
            pthread_mutex_unlock(&etmMutex);
        } else if (strncmp(&buffer, ETM_RESTART, SOCKET_BUFFER_LENGTH) == 0) {
            endETM(1);
        } else {
            printf("socket received the unknown: %s\n", &buffer);
        }
    }
}

void setupSocketServer() {
    sd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sd < 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_un serveraddr;
    memset(&serveraddr, 0, sizeof(serveraddr));
    serveraddr.sun_family = AF_UNIX;
    strcpy(serveraddr.sun_path, SOCKET_PATH);

    if (bind(sd, (struct sockaddr *)&serveraddr, SUN_LEN(&serveraddr)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(sd, 10) < 0) {
        perror("listen failed");
        exit(EXIT_FAILURE);
    }

    pthread_t threadSocket;
    if (pthread_create(&threadSocket, NULL, &threadListener, NULL) == 0) {
        // success
        printf("pthread listening ok\n");
    } else {
        perror("pthread_create");
    }
}

void registerSignalHandlers() {
    if (signal(SIGTERM, unload) == SIG_ERR) {
        perror("signal");
        exit(EXIT_FAILURE);
    }
    if (signal(SIGINT, unload) == SIG_ERR) {
        perror("signal");
        exit(EXIT_FAILURE);
    }
}

void cleanPreviousRun() {
    if (remove(SOCKET_PATH)) {
        if (errno != ENOENT) {
            perror("cleanPreviousRun SOCKET_PATH");
        }
    }
    if (remove(LOCK_PATH)) {
        if (errno != ENOENT) {
            perror("cleanPreviousRun LOCK_PATH");
        }
    }
    if (remove(ETM_LOCK_PATH)) {
        perror("cleanPreviousRun ETM_LOCK_PATH");
    }
}

void unload() {
    puts("unloading...");
    close(fdLock);
    if (remove(SOCKET_PATH)) {
        perror("unload SOCKET_PATH");
    }
    if (remove(LOCK_PATH)) {
        perror("unload LOCK_PATH");
    }
    if (remove(ETM_LOCK_PATH)) {
        perror("unload ETM_LOCK_PATH");
    }
    pthread_mutex_destroy(&etmMutex);
    exit(EXIT_SUCCESS);
}

void hookLibmounthelper() {
    char* LD_PRELOAD = getenv("LD_PRELOAD");
    if (LD_PRELOAD == NULL) {
        if (setenv("LD_PRELOAD", LIBMOUNTHELPER_PATH, 1) == -1) {
            perror("setenv");
        }
    } else {
        strcat(LD_PRELOAD, " ");
        strcat(LD_PRELOAD, LIBMOUNTHELPER_PATH);
        if (setenv("LD_PRELOAD", LD_PRELOAD, 1) == -1) {
            perror("setenv");
        }
    }
}

int main(const int argc, const char* argv[]) {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    if (chdir(etmWorkingDir) == -1) {
        perror("chdir");
        exit(EXIT_FAILURE);
    }
    umask(006);
    cleanPreviousRun();
    registerSignalHandlers();

    setupSocketServer();

    fdLock = open(LOCK_PATH, O_CREAT | O_RDWR, 0666);

    if (fdLock == -1) {
        perror("Open lock file");
        exit(EXIT_SUCCESS);
    }

    int rc = flock(fdLock, LOCK_EX | LOCK_NB);
    if (rc == 0) {
        // success
        puts("xwared: unlocked.");
        fdETMLock = open(ETM_LOCK_PATH, O_CREAT | O_RDWR, 0666);
        if (fdETMLock == -1) {
            perror("Open ETM lock file");
            exit(EXIT_SUCCESS);
        }

        // Check if ETM should run at start
        GKeyFile* configFile = g_key_file_new();
        if (g_key_file_load_from_file(configFile, CONFIG_PATH, G_KEY_FILE_NONE, NULL) == 0) {
            fprintf(stderr, "xwared: cannot load settings.ini, use default value\n");
        }
        GError* gErr = NULL;
        gboolean etmStart = g_key_file_get_boolean(configFile, "xwared", "startetm", &gErr);
        if (gErr == NULL) {
            if (etmStart == FALSE) {
                toRunETM = 0;
            }
        } else {
            fprintf(stderr, "xwared: %s, use default value\n", gErr->message);
            g_error_free(gErr);
        }
        g_key_file_free(configFile);

        while(1) {
            runETM();
        }

    } else {
        if (errno == EWOULDBLOCK) {
            puts("xwared: locked.");
            exit(EXIT_FAILURE);
        }
        perror("flock");
    }
    unload();
    exit(EXIT_SUCCESS);
}
