import os,json,time

import public,Thread_FFmpeg

class HN_Task():

    def __init__(self,log_dir,hls_dir,task_time):
        self.task_time = task_time
        self.log_dir = log_dir
        self.hls_dir = hls_dir
        self.log_taskLine = log_dir + "taskLine.json"
        self.log_taskdir = log_dir + "tasks/"

    def getTaskLine(self):
        if not os.path.exists(self.log_taskLine):
            taskLine = {"alive": [], "sleep": [], "all": []}
        else:
            tasks = self.getTaskAll()
            # 全部进程队列
            Task = []
            # 存活进程队列
            TaskAlive = []
            # 疑似存活进程队列
            TaskSleep = []

            for task in tasks:
                task["expireTime"] = task["task_Init"] + task["task_runAlive"] + self.task_time
                # 进程心跳时间
                if int(task["threadHeart"]) >= int(time.time()) - 5:
                    TaskAlive.append(task)
                    Task.append(task)
                if int(task["threadHeart"]) < int(time.time()) - 5 and task["threadHeart"] >= int(time.time()) - 15:
                    TaskSleep.append(task)
                    Task.append(task)
            public.WriteFile(self.log_taskLine,json.dumps(Task))
            taskLine = { "alive": Task,"all":tasks}
        return taskLine

    def getTaskAll(self):
        if not os.path.exists(self.log_taskLine):
            return []
        data = public.ReadFile(self.log_taskLine)
        if data == "":return []
        return json.loads(data)

    # 重启指定的进程
    def resetTaskLine(self,task):
        if not os.path.exists(self.log_taskdir):
            os.mkdir(self.log_taskdir)

        thread =Thread_FFmpeg.Thread_FFmpeg(task["taskId"],"FFmpeg Rtsp To Hls", task["videoId"], task["ffmpeg_shell"] , self.log_dir)
        thread.start()
        task["task_Init"]=int(time.time())
        task["task_run"]= 0
        task["threadHeart"] = int(time.time())
        task["threadPid"] = thread.get_threadPid()
        task["waitRun"] = True
        taskLine = self.getTaskLine()
        taskLine["all"].append(task)
        public.WriteFile(self.log_taskLine, json.dumps(taskLine["all"]))

        return thread,task




    def addTaskLine(self,videoId,rtspUrl,hls_time,hls_size,ffmpeg=False):
        if not os.path.exists(self.log_taskdir):
            os.mkdir(self.log_taskdir)
        if ffmpeg:
            shell = ffmpeg
        else:
            shell = 'ffmpeg -rtsp_transport tcp -i "__RTSPURL__" -fflags flush_packets -max_delay 1 -an -flags -global_header -hls_time __HLSTIME__ -hls_list_size __HLSSIZE__ -hls_flags omit_endlist+split_by_time -vcodec libx264 -y __VIDEOOUTDIR__/video.m3u8'
        if not os.path.exists(self.hls_dir + videoId):
            os.mkdir(self.hls_dir + videoId)
        else:
            os.system("rm -rf "+ self.hls_dir + videoId + "/*")
        shell = shell.replace("ffmpeg", "/usr/local/ffmpeg/bin/ffmpeg")
        shell = shell.replace("__HLSTIME__", hls_time)
        shell = shell.replace("__HLSSIZE__", hls_size)
        shell = shell.replace("__RTSPURL__", rtspUrl)
        shell = shell.replace("__VIDEOOUTDIR__",self.hls_dir + videoId)
        task = {
                "taskId":public.GetStrUuid(),"task_Init":int(time.time()),"task_run":0,"task_runAlive":0,
                "videoId": videoId, "rtspUrl": rtspUrl,"ffmpeg_shell":shell,"videoUrl":videoId + "/video.m3u8","videoDir":self.hls_dir + videoId +"/",
                "threadHeart":int(time.time()),"waitRun":True,
        }
        public.Print_Log("线程参数构造完成，准备启动线程...")
        thread =Thread_FFmpeg.Thread_FFmpeg(task["taskId"],"FFmpeg Rtsp To Hls", videoId, task["ffmpeg_shell"] , self.log_dir)
        thread.start()

        taskLine = self.getTaskLine()
        taskLine["all"].append(task)
        public.WriteFile(self.log_taskLine, json.dumps(taskLine["all"]))

        return thread,task

    def remove_task(self,taskId):
        tasks = self.getTaskAll()
        ntask = []
        for task in tasks:
            if task["taskId"] !=taskId:
                ntask.append(task)
        public.WriteFile(self.log_taskLine, json.dumps(ntask))

    def find_task(self,taskId):
        tasks = self.getTaskAll()
        for task in tasks:
            if task["taskId"] ==taskId:
                return task
        return False






