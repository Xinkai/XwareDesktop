#include <stdlib.h>
#include <sys/file.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

// save the environment variables.
char** environ = NULL;

#include "daemon.h"
char* xwareArgv[] = {"./foo.py", "para1", "para2", NULL};

int passArguments(const int argc, const char* argv[]) {
	return 0;
}

int watchChild(pid_t pid) {
	int status;
	waitpid(pid, &status, 0);
	printf("waitpid: %d\n", status);
	runXware();

	return 0;
}

int runXware() {
	pid_t childPid = fork();

	if (childPid < 0) {
		perror("Fork failed");
		exit(EXIT_FAILURE);
	} else if (childPid == 0) {
		// child
		printf("child: pid(%u) ppid(%u)\n", getpid(), getppid());

		execve(xwareArgv[0], xwareArgv, environ);
		perror("execve");
		exit(EXIT_FAILURE);
	} else {
		// parent
		printf("parent: pid(%u) cpid(%u)\n", getpid(), childPid);
		watchChild(childPid);
	}
	return 0;
}

int main(const int argc, const char* argv[], char* envp[]) {
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);
	environ = envp;

    int pidFile = open("/tmp/xware_daemon.pid", O_CREAT | O_RDWR, 0666);
    if (pidFile == -1) {
        perror("Open pid file");
        exit(EXIT_SUCCESS);
    }

    int rc = flock(pidFile, LOCK_EX | LOCK_NB);
    if (rc == 0) {
        // success
        puts("Xware daemon: unlocked.");
		runXware();
    } else {
        if (errno == EWOULDBLOCK) {
            puts("Xware daemon: locked.");
        }
        puts("Xware daemon: unknown.");
    }
    close(pidFile);
    exit(EXIT_SUCCESS);
}
