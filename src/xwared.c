#include "xwared.h"

int watchETM() {
	int status;
	waitpid(etmPid, &status, 0);
	printf("waitpid: %d\n", status);
	while (autoReviveETM == 0) {
		sleep(1);
	} // loop until the frontend restarts ETM

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
		flock(fdETMLock, LOCK_EX | LOCK_NB);
		execv(etmArgv[0], etmArgv);
		flock(fdETMLock, LOCK_UN);
		perror("execve");
		exit(EXIT_FAILURE);
	} else {
		// parent
		printf("parent: pid(%u) cpid(%u)\n", getpid(), etmPid);
		watchETM();
	}
	return 0;
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
		autoReviveETM = restart;
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

		char buffer;
		read(sdAccept, &buffer, SOCKET_BUFFER_LENGTH);

		// dispatch
		if (strncmp(ETM_STOP, &buffer, SOCKET_BUFFER_LENGTH) == 0) {
			endETM(0);
		} else if (strncmp(&buffer, ETM_START, SOCKET_BUFFER_LENGTH) == 0){
			pthread_mutex_lock(&etmMutex);
			if (etmPid != -1) {
				printf("ETM running, ignore ETM_START");
			} else {
				autoReviveETM = 1;
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
	chdir(etmWorkingDir);
	umask(002);
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

        while(autoReviveETM == 1) {
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
