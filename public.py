
import sys,os,json,time,re
import uuid,psutil

def Format_Date(format="%Y-%m-%d %H:%M:%S",times = None):
    if not times: times = int(time.time())
    time_local = time.localtime(times)
    return time.strftime(format, time_local)


def Print_Log(log,logpath=False):
    msg = "[" + Format_Date() + "]:" + log
    print(msg)
    if logpath:
        logfile = ReadFile(logpath)
        if not logfile:logfile = ""
        logfile = logfile + "\n" + msg
        WriteFile(logpath,logfile)


def ReadFile(filename,mode = 'r'):
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except:
                fp = open(filename, mode,encoding="GBK")
                f_body = fp.read()
                fp.close()
        else:
            return False
    return f_body


def WriteFile(filename,s_body,mode='w+'):
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False


def GetStrUuid():
    Suuid = str(uuid.uuid4())
    return Suuid


def RunShellWait(shell):
    proc = os.popen(shell)
    result = proc.read()
    proc.close()
    return  result

def GetSystemTask(grep):
    tasks = []
    taskList = RunShellWait("ps -ef | grep "+grep).split("\n")
    for task in taskList:
        if task != "":
            s = task.split(" ")
            slen = len(s)
            st = 17
            shell = ""
            while st <= slen - 1:
                if shell == "":
                    shell = s[st]
                else:
                    shell = shell + " " + s[st]
                st = st + 1
            #print(s)
            t = {"user": s[0], "pid": s[6], "pid_p": s[8], "cpu": s[10], "time_s": s[11], "tty": s[12], "time_c": s[16],
                 "shell": shell}
            tasks.append(t)
    return tasks

def Kill_Process(pid):
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'ppid','name'])
            if str(pinfo["ppid"]) == str(pid):
                os.system("kill -9 " + str(pinfo["pid"]))
        except psutil.NoSuchProcess:
            pass
    os.system("kill -9 " + str(pid))

def cache_set(key,value):
    if not os.path.exists("./cache"):
        cache = {}
    else:
        cache = json.loads(ReadFile("./cache"))
    cache[key] = value
    WriteFile("./cache",json.dumps(cache))


def cache_get(key):
    if not os.path.exists("./cache"):
        cache = {}
    else:
        cache = json.loads(ReadFile("./cache"))
    if key in cache:
        return cache[key]
    else:
        return None


# 取当前系统版本信息
def sys_GetOs():
    version = ReadFile('/etc/redhat-release')
    if not version:
        version = ReadFile('/etc/issue').strip().split("\n")[0].replace('\\n', '').replace('\l', '').strip()
    else:
        version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
    v_info = sys.version_info
    version = version + '(Py' + str(v_info.major) + '.' + str(v_info.minor) + '.' + str(v_info.micro) + ')'
    return version

# 取CPU 的型号信息
def sys_GetCpu():
    cpuCount = psutil.cpu_count()
    cpuNum = psutil.cpu_count(logical=False)
    c_tmp = ReadFile('/proc/cpuinfo')
    d_tmp = re.findall("physical id.+", c_tmp)
    cpuW = len(set(d_tmp))

    use = get_cpu_percent()

    used_all = psutil.cpu_percent(percpu=True)
    cpuinfo = open('/proc/cpuinfo', 'r').read()
    rep = "model\s+name\s+:\s+(.+)"
    tmp = re.search(rep, cpuinfo, re.I)
    cpuType = ''
    if tmp:
        cpuType = tmp.groups()[0]
    else:
        cpuinfo = RunShellWait('LANG="en_US.UTF-8" && lscpu')
        rep = "Model\s+name:\s+(.+)"
        tmp = re.search(rep, cpuinfo, re.I)
        if tmp: cpuType = tmp.groups()[0]
    cpu = {"name": cpuType + " * {}".format(cpuW),"count":cpuCount,"use":use,"all":used_all,"num":cpuNum,"w":cpuW}
    return cpu

# 取内存大小信息
def sys_getMem():
    mem = psutil.virtual_memory()
    memInfo = {'memTotal': int(mem.total / 1024 / 1024), 'memFree': int(mem.free / 1024 / 1024),
               'memBuffers': int(mem.buffers / 1024 / 1024), 'memCached': int(mem.cached / 1024 / 1024)}
    memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
    return memInfo

def get_cpu_percent(sleep=1):
    percent = 0.00
    old_cpu_time = get_cpu_time()
    old_process_time = get_process_cpu_time()
    time.sleep(sleep)
    new_cpu_time = get_cpu_time()
    new_process_time = get_process_cpu_time()
    try:
        percent = round(100.00 * ((new_process_time - old_process_time) / (new_cpu_time - old_cpu_time)), 2)
    except:
        percent = 0.00

    if percent > 100: percent = 100
    if percent > 0: return percent
    return 0.00

def get_process_cpu_time():
    pids = psutil.pids()
    cpu_time = 0.00
    for pid in pids:
        try:
            cpu_times = psutil.Process(pid).cpu_times()
            for s in cpu_times: cpu_time += s
        except:
            continue
    return cpu_time

def get_cpu_time():
    cpu_time = 0.00
    cpu_times = psutil.cpu_times()
    for s in cpu_times: cpu_time += s
    return cpu_time

def get_process_status(pid):
    try:
        p = psutil.Process(pid)
        return p.status()
    except:
        return "killed"






