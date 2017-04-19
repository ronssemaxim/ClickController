"""
DelayedInvoke.py. Invoke any python definition after a certain time

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import threading
import time

import Logger

# set to 1/True to stop all the threads
exitFlag = 0


class DelayedInvoke(threading.Thread):
    def __init__(self, func, *args, exec_after):
        """
        Create the DelayedInvoke object.
        :param func: function name to execute eg print
        :param args: arguments to pass to the function eg "Hello %s", "world"
        :param exec_after: the time, in seconds, after which the function will be invoked
        """
        threading.Thread.__init__(self)
        self.func = func
        self.func_args = args

        self.exec_after = exec_after
        Logger.log(self.name, "Thread initialized, args = " + str(args), 7)

    def run(self):
        """
        Start the thread, start the countdown
        """
        Logger.log(self.name, "Starting thread", 7)
        if exitFlag:
            self.name.exit()
        time.sleep(self.exec_after)
        if exitFlag:
            self.name.exit()
        result = self.invoke()
        Logger.log(self.name, "Result after invoke: " + str(result), 9)
        Logger.log(self.name, "Thread finished", 7)

    def invoke(self):
        """
        Invoke the passed function and passes the specified arguments to it
        :return:
        """
        return self.func(*self.func_args)
