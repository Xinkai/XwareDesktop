#include "daemon.h"

int watchETM() {
	int status;
	waitpid(etmPid, &status, 0);
	printf("waitpid: %d\n", status);
	while (autoReviveETM == 0) {}; // loop until the frontend restarts ETM

	return 0;
}

int runETM() {
	pthread_mutex_lock(&etmMutex);
	autoReviveETM = 1;
	etmPid = fork();
	pthread_mutex_unlock(&etmMutex);

	if (etmPid < 0) {
		perror("Fork failed");
		exit(EXIT_FAILURE);
	} else if (etmPid == 0) {
		// child
		hookLibmounthelper();
		printf("child: pid(%u) ppid(%u)\n", getpid(), getppid());
		execv(etmArgv[0], etmArgv);
		perror("execve");
		exit(EXIT_FAILURE);
	} else {
		// parent
		printf("parent: pid(%u) cpid(%u)\n", getpid(), etmPid);
		watchETM();
	}
	return 0;
}

void* threadListener() {
	printf("pthread listening\n");
	while(1) {
		int sdAccept = accept(sd, NULL, NULL);
		if (sdAccept < 0) {
			perror("accept failed");
			exit(EXIT_FAILURE);
		}

		char buffer;
		read(sdAccept, &buffer, SOCKET_BUFFER_LENGTH);

		// dispatch
		if (strncmp(ETM_STOP, &buffer, SOCKET_BUFFER_LENGTH) == 0) {
			pthread_mutex_lock(&etmMutex);
			if (etmPid == -1) {
				printf("ETM not running, ignore ETM_STOP.\n");
			} else {
				autoReviveETM = 0;
				if (kill(etmPid, SIGTERM) == 0) {
					// successful
					etmPid = -1;
				} else {
					perror("kill ETM");
					exit(EXIT_FAILURE);
				}
			}
			pthread_mutex_unlock(&etmMutex);
		} else if (strncmp(&buffer, ETM_START, SOCKET_BUFFER_LENGTH) == 0){
			pthread_mutex_lock(&etmMutex);
			if (etmPid != -1) {
				printf("ETM running, ignore ETM_START");
			} else {
				autoReviveETM = 1;
			}
			pthread_mutex_unlock(&etmMutex);
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
	if (remove(PID_PATH)) {
		if (errno != ENOENT) {
			perror("cleanPreviousRun PID_PATH");
		}
	}
}

void unload() {
	puts("unloading...");
	close(fdPid);
	if (remove(SOCKET_PATH)) {
		perror("unload SOCKET_PATH");
	}

    if (remove(PID_PATH)) {
    	perror("unload PID_PATH");
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
	chdir(etmWorkingDir);
	umask(002);
	cleanPreviousRun();
	registerSignalHandlers();

	setupSocketServer();

    int fdPid = open(PID_PATH, O_CREAT | O_RDWR, 0666);
    if (fdPid == -1) {
        perror("Open pid file");
        exit(EXIT_SUCCESS);
    }

    int rc = flock(fdPid, LOCK_EX | LOCK_NB);
    if (rc == 0) {
        // success
        puts("Xware daemon: unlocked.");
        while(autoReviveETM == 1) {
        	runETM();
        }

    } else {
        if (errno == EWOULDBLOCK) {
            puts("Xware daemon: locked.");
            exit(EXIT_FAILURE);
        }
        perror("flock");
    }
    unload();
    exit(EXIT_SUCCESS);
}
