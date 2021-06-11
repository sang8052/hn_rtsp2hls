import os,json,time

import public,Thread_FFmpeg

class HN_Task():

    def __init__(self,config,ptask):
        self.config = config
        self.task = ptask


    def getTaskLine(self):
        tasks = self.task
        # 全部进程队列
        Task = []
        # 存活进程队列
        TaskAlive = []
        #print(tasks)
        for task in tasks["all"]:
            task["expireTime"] = task["task_Init"]  + task["task_runAlive"] + self.config["task_time"]
            # 进程心跳时间
            if int(task["threadHeart"]) >= int(time.time()) - 5:
                TaskAlive.append(task)
                Task.append(task)
            if int(task["threadHeart"]) < int(time.time()) - 5 and task["threadHeart"] >= int(time.time()) - 15:
                Task.append(task)
        taskLine = {"alive": Task, "all": tasks["all"]}
        self.task = taskLine
        return taskLine


    # 重启指定的进程
    def resetTaskLine(self,task):
        if not os.path.exists(self.config["log_dir"]):
            os.mkdir(self.config["log_dir"])
        thread =Thread_FFmpeg.Thread_FFmpeg(task["taskId"],"FFmpeg Rtsp To Hls", task["videoId"], task["ffmpeg_shell"] , self.config["log_dir"])
        thread.start()
        task["task_Init"]=int(time.time())
        task["task_run"]= 0
        task["threadHeart"] = int(time.time())
        task["threadPid"] = thread.get_threadPid()
        task["waitRun"] = True
        self.task["all"].append(task)
        return thread,task

    def addTaskLine(self,videoId,rtspUrl,hls_time,hls_size,ffmpeg=False):
        if not os.path.exists(self.config["log_dir"]):
            os.mkdir(self.config["log_dir"])
        if ffmpeg:
            shell = ffmpeg
        else:
            shell = 'ffmpeg -rtsp_transport tcp -i "__RTSPURL__" -fflags flush_packets -max_delay 1 -an -flags -global_header -hls_time __HLSTIME__ -hls_list_size __HLSSIZE__ -hls_flags omit_endlist+split_by_time -vcodec libx264 -y __VIDEOOUTDIR__/video.m3u8'
        if not os.path.exists(self.config["hls_dir"] + videoId):
            os.mkdir(self.config["hls_dir"] + videoId)
        else:
            os.system("rm -rf "+ self.config["hls_dir"] + videoId )
            os.mkdir(self.config["hls_dir"] + videoId)
        shell = shell.replace("ffmpeg", "/usr/local/ffmpeg/bin/ffmpeg")

        shell = shell.replace("__HLSTIME__", hls_time)
        shell = shell.replace("__HLSSIZE__", hls_size)
        shell = shell.replace("__RTSPURL__", rtspUrl)
        shell = shell.replace("__VIDEOOUTDIR__",self.config["hls_dir"] + videoId)
        task = {
                "taskId":public.GetStrUuid(),"task_Init":int(time.time()),"task_run":0,"task_runAlive":0,
                "videoId": videoId, "rtspUrl": rtspUrl,"ffmpeg_shell":shell,"videoUrl":videoId + "/video.m3u8","videoDir":self.config["hls_dir"] + videoId +"/",
                'hls_time':hls_time,"hls_size":hls_size,
                "threadHeart":int(time.time()),"waitRun":True,
        }
        public.Print_Log("线程参数构造完成，准备启动线程...")
        thread =Thread_FFmpeg.Thread_FFmpeg(task["taskId"],"FFmpeg Rtsp To Hls", videoId, task["ffmpeg_shell"] ,self.config["log_dir"] )
        thread.start()

        self.task["all"].append(task)
        return thread,task

    def set_task(self,task):
        self.task["all"] = task

    def remove_task(self,taskId):
        ntask = []
        for task in self.task["all"]:
            if task["taskId"] !=taskId:
                ntask.append(task)
        self.task["all"]  = ntask

    def find_task(self,taskId):
        for task in self.task["all"]:
            if task["taskId"] ==taskId:
                return task
        return False
