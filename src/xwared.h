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
#include <glib.h>
#include <pwd.h>

#define CONFIG_PATH "/opt/xware_desktop/settings.ini"

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
void runETM();
void watchETM();
void endETM(const int restart);
int toRunETM = 1; // when endETM() is called, set this to 0.
pthread_mutex_t etmMutex = PTHREAD_MUTEX_INITIALIZER;
const char* etmWorkingDir = "/opt/xware_desktop/xware/lib";
char* etmArgv[] = {"/opt/xware_desktop/xware/lib/EmbedThunderManager", "--verbose", NULL};
//char* etmArgv[] = {"//usr/bin/sleep", "1", NULL};

#define ETMPATCH_PATH "/opt/xware_desktop/etmpatch.so"

void registerSignalHandlers();
void cleanPreviousRun();
void unload();
void hookEtmPatch();
int main(const int argc, const char* argv[]);


