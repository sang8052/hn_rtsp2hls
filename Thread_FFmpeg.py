import threading,time,os,json

import public


class Thread_FFmpeg (threading.Thread):

    def __init__(self, threadId, threadName, videoId, shell,log_dir):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.threadName = threadName
        self.videoId = videoId
        self.shell = shell
        self.log_dir = log_dir
        self.pid = ""
        self.status = True




    def run(self):
        public.Print_Log("启动转流进程[" + self.threadId + "]--[videoId:" + self.videoId + "]成功",self.log_dir + "run.log")
        self.start_shell()
        public.Print_Log("进程命令执行成功")
        while self.status:
            time.sleep(1)

        os.system("bash kill-super.sh"+self.pid)




    def start_shell(self):
        if not os.path.exists("./shell"):
            os.mkdir("./shell")
        fshell = """pid=$$
echo $pid > "./shell/TASK_%s.pid"
%s
""" % (self.threadId,self.shell)
        public.WriteFile("./shell/SHELL_" + self.threadId + ".sh" , fshell)
        os.system("nohup bash ./shell/SHELL_" + self.threadId + ".sh > " + self.log_dir + "tasks/" + self.threadId + ".log &")
        time.sleep(1)
        pid = public.ReadFile("./shell/TASK_"+ self.threadId + ".pid").replace("\n","")
        self.pid = pid
        return self.pid

    def stop_thread(self):
        self.status = False

    def get_threadPid(self):
        return self.pid



