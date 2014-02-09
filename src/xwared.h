#include <stdlib.h>
#include <sys/file.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <string.h>
#include <pthread.h>
#include <sys/stat.h>

// lock of this program
#define LOCK_PATH "/tmp/xware_xwared.lock"
int fdLock = -1;

// allow the frontend to communicate with xwared
#define SOCKET_PATH "/tmp/xware_xwared.socket"
#define SOCKET_BUFFER_LENGTH 16
void setupSocketServer();
void* threadListener();
int sd = -1;
#define ETM_STOP "ETM_STOP"
#define ETM_START "ETM_START"
#define ETM_RESTART "ETM_RESTART"

#define ETM_LOCK_PATH "/tmp/xware_ETM.lock"
int fdETMLock = -1;
int etmPid = -1; // pid of EmbedThunderManager
int runETM();
int watchETM();
void endETM(const int restart);
int autoReviveETM = 1; // when endETM() is called, set this to 0.
pthread_mutex_t etmMutex = PTHREAD_MUTEX_INITIALIZER;
const char* etmWorkingDir = "/opt/xware_desktop/xware/lib";
char* etmArgv[] = {"/opt/xware_desktop/xware/lib/EmbedThunderManager", "--verbose", NULL};
//char* etmArgv[] = {"//usr/bin/sleep", "1", NULL};

#define LIBMOUNTHELPER_PATH "/opt/xware_desktop/libmounthelper.so"

void registerSignalHandlers();
void cleanPreviousRun();
void unload();
void hookLibmounthelper();
int main(const int argc, const char* argv[]);


