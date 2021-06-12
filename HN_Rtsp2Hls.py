import os,sys,json,time,requests,psutil


from flask import Flask,request

import public,HN_Task,Thread_Pool
import frequest as fre


_ver = "1.5.2.beta"

api = Flask(__name__)


@api.route('/',methods=['GET','POST'])
# 获取当前系统（程序）的版本信息
def get_System():
    sys = {"os":public.sys_GetOs(),"ver":_ver}
    return fre.success_response(sys)

@api.route('/task',methods=['GET','POST'])
# 获取当前正在进行的转流进程的消息
def get_TaskLine():
    taskLine = htask.getTaskLine()
    return fre.success_response(taskLine)

@api.route("/play",methods=['GET','POST'])
def task_PlayVideo():
    args = fre.request_obj()["args"]
    parsg = [{"name":"videoId","len":["=",32]},{"name":"rtspUrl"},{"name":"hlsTime"},{"name":"hlsSize"}]
    c = fre.check_args(parsg,args)
    if c:return c
    videoId = args["videoId"]
    rtspUrl = args["rtspUrl"]
    hlsTime = str(args["hlsTime"])
    hlsSize = str(args["hlsSize"])
    public.Print_Log("执行视频串流，videoId:" + videoId)
    if "ffmpeg" in args:
        ffmpeg = args.ffmpeg
    else:
        ffmpeg = None
        public.Print_Log("取系统运行任务队列成功!")

    taskAll = htask.getTaskLine()["all"]
    # 检查是否有存活的进程
    for task in taskAll:
        if task["videoId"] == videoId:
            task["wait_secord"] = 0
            task["play_status"] = "alive"
            return fre.success_response(task)

    # 如果没有存在的进程 那么开始启动一个新的转流进程
    public.Print_Log("开始启动一个新的转流进程!")
    thread, task = htask.addTaskLine(videoId, rtspUrl,hlsTime,hlsSize, ffmpeg)
    # 等待m3u8 切片文件存在
    wait_count = 0
    play_status = "success"
    while not os.path.exists(task["videoDir"] + "video"+task["hls_size"]+".ts"):
        if wait_count > config["hls_timeout"] :
            play_status = "timeout"
            break
        public.Print_Log("等待切片文件生成中...")
        time.sleep(1)
        wait_count = wait_count + 1
    tpool.add_thread(thread)
    task["threadHeart"] = int(time.time())
    task["wait_secord"] = wait_count -1
    task["play_status"] = play_status
    task["waitRun"] = False
    task["threadPid"] = thread.pid
    tasks = htask.getTaskLine()["all"]
    kid = 0
    for t in tasks:
        if t["taskId"] == task["taskId"]:
            tasks[kid] = task
        else:
            kid = kid + 1
    htask.set_task(tasks)
    return fre.success_response(task)


@api.route("/stop",methods=['GET','POST'])
def task_StopVideo():
    args = fre.request_obj()["args"]
    parsg = [{"name": "taskId", "len": ["=", 36]}]
    c = fre.check_args(parsg, args)
    if c: return c
    task = htask.find_task(args["taskId"])
    if task:
        htask.remove_task(args["taskId"])
        if "threadPic" in task:
            if task["threadPid"]!="":
                public.Kill_Process(task["threadPid"])
        tpool.remove_thread(args["taskId"])
        status = "success"
    else:
        status = "dead"
    stop={"taskId":args["taskId"],"status":status}
    return fre.success_response(stop)

@api.route("/alive",methods=['GET','POST'])
def task_AliveVideo():
    args = fre.request_obj()["args"]
    parsg = [{"name": "taskId", "len": ["=", 36]},{"name":"alive"}]
    c = fre.check_args(parsg, args)
    if c: return c
    task = htask.find_task(args["taskId"])
    expireTime = 0
    if task:
        tasks = htask.getTaskLine()["all"]
        kid = 0
        for task in tasks:
            if task["taskId"] == args["taskId"]:
                task["task_runAlive"] = task["task_runAlive"] + args["alive"]
                tasks[kid] = task
            else:
                kid = kid + 1
        htask.set_task(tasks)
        status = "success"
        expireTime = task["task_Init"]  + task["task_runAlive"] + config["task_time"]
    else:
        status = "dead"
    stop={"taskId":args["taskId"],"status":status,"expireTime":expireTime}
    return fre.success_response(stop)


if __name__ == '__main__':

    public.Print_Log("RTSP 转 HLS直播流控制工具,Version:" + _ver)
    public.Print_Log("copyright © jshainei.com 2019-2021 ")

    # 加载配置文件
    try:
        config = json.loads(public.ReadFile("config.json"))
    except:
        public.Print_Log("[致命错误]加载核心配置文件出错，程序终止!")
        sys.exit(0)


    # 检查是否存在 日志文件夹 和 hls 输出文件夹
    if not os.path.exists(config["log_dir"]):
        os.mkdir(config["log_dir"])
    if not os.path.exists(config["hls_dir"]):
        os.mkdir(config["hls_dir"])




    public.cache_set("sysVer",_ver)

    ptask = {"alive": [], "all": []}
    pthread = []

    # 启动前杀死所有的 ffmpeg 的进程
    os.system("pkill -9 ffmpeg")

    time.sleep(1)
    public.Print_Log("转流任务队列初始化中...", config["log_dir"] + "run.log")
    htask = HN_Task.HN_Task(config,ptask)

    time.sleep(1)
    public.Print_Log("线程调度线程启动中...",  config["log_dir"]  + "run.log")
    tpool = Thread_Pool.Thread_Pool(public.GetStrUuid(),"HN Thread Pool Control",htask,config)
    tpool.start()


    time.sleep(1)
    public.Print_Log("API 框架（FLASK）启动中...",config["log_dir"] + "run.log")
    try:
        spid = os.getpid()
        prun = public.GetSystemTask("HN_Rtsp2Hls")
        for p in prun:
            if p["pid"] != str(spid):
                os.system("kill -9 " + str(p["pid"]))
    except:
        public.Print_Log("自动进程KILL 异常...", config["log_dir"] + "run.log")
        pass

    # 启动 API 进程
    api.run(config["rect_ip"],config["rect_port"])







