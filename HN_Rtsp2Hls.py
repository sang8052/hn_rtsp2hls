import os,sys,json,time,requests,psutil


from flask import Flask,request

import public,HN_Task,Thread_Pool
import frequest as fre

_port = 0
_ip = ""
_task_time = 0
_log_dir = ""
_hls_dir = ""
_ver = "1.0.beta"

api = Flask(__name__)


@api.route('/',methods=['GET','POST'])
@api.route('/system')
# 获取当前系统（程序）的版本信息
def get_System():
    sys = {"os":public.sys_GetOs(),"cpu":public.sys_GetCpu(),"mem":public.sys_getMem(),"ver":gconfig["ver"]}
    return fre.success_response(sys)

@api.route('/task',methods=['GET','POST'])
# 获取当前正在进行的转流进程的消息
def get_TaskLine():
    taskLine = htask.getTaskLine()
    return fre.success_response(taskLine)

@api.route("/play",methods=['GET','POST'])
def task_PlayVideo():
    args = fre.request_obj()["args"]
    parsg = [{"name":"videoId","len":["=",36]},{"name":"rtspUrl"},{"name":"hlsTime"},{"name":"hlsSize"}]
    c = fre.check_args(parsg,args)
    if c:return c
    videoId = args["videoId"]
    rtspUrl = args["rtspUrl"]
    hlsTime = str(args["hlsTime"])
    hlsSize = str(args["hlsSize"])
    if "ffmpeg" in args:
        ffmpeg = args.ffmpeg
    else:
        ffmpeg = None
    taskAll = htask.getTaskLine()["all"]
    # 检查是否有存活的进程
    for task in taskAll:
        if task["videoId"] == videoId:
            task["wait_secord"] = 0
            task["play_status"] = "alive"
            return fre.success_response(task)
    # 如果没有存在的进程 那么开始启动一个新的转流进程
    thread, task = htask.addTaskLine(videoId, rtspUrl,hlsTime,hlsSize, ffmpeg)
    tpool.add_thread(thread)
    # 等待m3u8 切片文件存在
    wait_count = 0
    play_status = "success"
    while not os.path.exists(task["videoDir"] + "video1.ts"):
        if wait_count > 15:
            play_status = "timeout"
            break
        public.Print_Log("等待切片文件生成中...")
        time.sleep(1)
        wait_count = wait_count + 1
    task["wait_secord"] = wait_count -1
    task["play_status"] = play_status
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
        if task["threadPid"]!="":
            os.system("bash kill-super.sh " + task["threadPid"])
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
        tasks = htask.getTaskAll()
        for task in tasks:
            if task["taskId"] == args["taskId"]:
                task["task_runAlive"] = task["task_runAlive"] + args["alive"]
        public.WriteFile(_log_dir + "taskLine.json",json.dumps(task))
        status = "success"
        expireTime = task["task_Init"]  + task["task_runAlive"] + _task_time
    else:
        status = "dead"
    stop={"taskId":args["taskId"],"status":status,"expireTime":expireTime}
    return fre.success_response(stop)


if __name__ == '__main__':

    # 加载配置文件
    try:
        config = json.loads(public.ReadFile("config.json"))
        _port = int(config["rect_port"])
        _task_time = int(config["task_time"])
        _ip = config["rect_ip"]
        _log_dir  = config["log_dir"]
        _hls_dir  = config["hls_dir"]
    except:
        public.Print_Log("[致命错误]加载核心配置文件出错，程序终止!")
        sys.exit(0)

    # 检查是否存在 日志文件夹 和 hls 输出文件夹
    if not os.path.exists(_log_dir):
        os.mkdir(_log_dir)
    if not os.path.exists(_hls_dir):
        os.mkdir(_hls_dir)



    # 启动前准备工作 杀死所有携带参数 HNId=Rtsp2Hls 的进程
    #tasks = public.GetSystemTask("HNId=Rtsp2Hls")
    #for task in tasks:
    #    os.popen("kill -9 "+task["pid"])

    if os.path.exists(_log_dir + "taskLine.json"):
        os.remove(_log_dir + "taskLine.json")

    if not os.path.exists("kill-super.sh"):
        shell = requests.get("https://mirrors.jshainei.com/smb/codesrc/shell/kill-super.sh").text
        public.WriteFile("kill-super.sh", shell)

    time.sleep(1)
    public.Print_Log("转流任务队列初始化中...", _log_dir + "run.log")
    htask = HN_Task.HN_Task(_log_dir,_hls_dir,_task_time)

    time.sleep(1)
    public.Print_Log("线程调度线程启动中...", _log_dir + "run.log")
    tpool = Thread_Pool.Thread_Pool(public.GetStrUuid(),"HN Thread Pool Control",htask,_log_dir,_task_time)
    tpool.start()


    time.sleep(1)
    public.Print_Log("API 框架（FLASK）启动中...",_log_dir + "run.log")
    # 启动 API 进程
    api.run(_ip,_port)




