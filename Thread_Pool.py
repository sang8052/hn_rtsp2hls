# 线程池调度线程

import threading,time,os,json

import public


class Thread_Pool (threading.Thread):

    def __init__(self, threadId, threadName,htask,config):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.threadName = threadName
        self.config = config
        self.task = htask
        self.threadPool = []

    # 启动任务调度
    def run(self):
        public.Print_Log("进程调度线程已经启动", self.config["log_dir"] + "run.log")
        while True:
            nthreadPool = []
            ntasks = []
            tasks = self.task.getTaskLine()["all"]
            try:
                for task in tasks:
                    heart = int(time.time()) - task["threadHeart"]
                    runTime = int(time.time()) - task["task_Init"]
                    aliveTime = self.config["task_time"] + task["task_runAlive"]
                    # 超过进程存活时间 , 杀死进程并 从队列中移除
                    if runTime > aliveTime:
                        public.Kill_Process(task["threadPid"])
                        public.Print_Log("线程[" + task["taskId"] + "]因 超过最大运行时间 已经被从线程池移除",
                                         self.config["log_dir"] + "run.log")
                    else:
                        if not task["waitRun"]:
                            if "play_status" in task:
                                if task["play_status"] == "timeout":
                                    public.Print_Log("线程[" + task["taskId"] + "]因 视频启动超时 已经被从线程池移除",
                                                     self.config["log_dir"] + "run.log")
                                    public.Kill_Process(task["threadPid"])
                                else:
                                    nthreadPool.append(thread)
                                    task["threadHeart"] = int(time.time())
                                    task["task_run"] = runTime
                                    ntasks.append(task)
                            else:
                                nthreadPool.append(thread)
                                task["threadHeart"] = int(time.time())
                                task["task_run"] = runTime
                                ntasks.append(task)
                        else:
                            thread = self.find_thread(task["taskId"])
                            if thread:
                                task["threadPid"] = thread.get_threadPid()
                                process = public.get_process_status(int(task["threadPid"]))
                                if process == "killed":
                                    public.Print_Log(
                                        "线程[" + task["taskId"] + "]因 无法找到进程对象（" + task["threadPid"] + "） 已经被从线程池移除",
                                        self.config["log_dir"] + "run.log")
                                    public.Kill_Process(task["threadPid"])
                                    public.Print_Log("线程[" + task["taskId"] + "]自动重启动中...",
                                                     self.config["log_dir"] + "run.log")
                                    thread = self.task.resetTaskLine(task)
                                    nthreadPool.append(thread)
                                else:
                                    nthreadPool.append(thread)
                                    task["threadHeart"] = int(time.time())
                                    task["task_run"] = runTime
                                    ntasks.append(task)
                            else:
                                if not task["waitRun"]:
                                    public.Print_Log("线程[" + task["taskId"] + "]因 无法找到线程池对象 已经被从线程池移除",
                                                     self.config["log_dir"] + "run.log")
                                    public.Kill_Process(task["threadPid"])
                                    public.Print_Log("线程[" + task["taskId"] + "]自动重启动中...",
                                                     self.config["log_dir"] + "run.log")
                                    thread = self.task.resetTaskLine(task)
                                    nthreadPool.append(thread)
                                else:
                                    task["threadHeart"] = int(time.time())
                                    task["task_run"] = runTime
                                    ntasks.append(task)
                self.threadPool = nthreadPool
                self.task.set_task(ntasks)
                time.sleep(0.5)
            except:
                public.Print_Log("线程调度出现异常...",  self.config["log_dir"] + "run.log")



    #向线程池中新增线程
    def add_thread(self,thread):
        self.threadPool.append(thread)



    # 从线程池中移除指定的线程
    def remove_thread(self,threadId):
        threadPool = []
        for thread in self.threadPool:
            try:
                if thread.threadId != threadId:
                    threadPool.append(thread)
            except:
                pass
        self.threadPool = threadPool


    def find_thread(self,threadId):
        for thread in self.threadPool:
            try:
                if thread.threadId == threadId:
                    return thread
            except:
                pass
        return False


