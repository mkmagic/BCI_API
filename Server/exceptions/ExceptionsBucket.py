import sys
import queue
import threading
import time

class ExceptionsBucket():

    def __init__(self, serveCondition, handleFunc, serverId, logDict):
        self._errorsBucket = queue.Queue()
        self._checkerThread = threading.Thread(target=self.checkAndHandleErrors, args=(serveCondition, handleFunc))
        self._serverId = serverId
        self._bucketMutex = threading.Semaphore(1)
        self._log = logDict

    def start_error_checker(self):
        self._checkerThread.start()

    def checkAndHandleErrors(self, serveCondition, handleFunc):
        while serveCondition():
            time.sleep( 5 )
            try:
                self._bucketMutex.acquire()
                exc_info = self._errorsBucket.get(block=False)
            except queue.Empty:
                self._bucketMutex.release()
                pass
            else:
                handleFunc()
                self._log.logMethod(self._serverId, repr(exc_info), error = True)
                self._bucketMutex.release()
                raise exc_info
    
    def append(self, exception):
        self._bucketMutex.acquire()
        self._errorsBucket.put(exception)
        self._bucketMutex.release()





