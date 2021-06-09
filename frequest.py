import time,json,os

from flask import Flask,request

import public,HN_Task





def success_response(data):
    return {"status": "success",
            "request_id": public.GetStrUuid(), "request_time": int(time.time()), "request_ip": request.remote_addr, "request_ua": request.remote_user,
            "response": data,"ver":public.cache_get("sysVer")}

def error_response(code,msg,e):
    return {"status": "error",
            "request_id": public.GetStrUuid(), "request_time": int(time.time()), "request_ip": request.remote_addr, "request_ua": request.remote_user,
            "response": {"code": code, "msg": msg, "error": e},"ver":public.cache_get("sysVer")
            },code

def check_args(args,input):
    for k in args:
        if "name" in k:
            name = k["name"]
        else:
            name = k
        if name not in input:
            return error_response(500,"请求参数异常...","参数[" + k["name"] + "]不存在")
        if "type" in k:
            if type(input[name]) != k["type"]:
                return error_response(500, "请求参数异常...", "参数[" + k["name"] + "]格式不正确")
        if "len" in k:
            klen_p = k["len"][0]
            klen_v = k["len"][1]
            if klen_p == "=":
                if len(input[name]) != klen_v:
                    return error_response(500, "请求参数异常...", "参数[" + k["name"] + "]长度不正确,ask:" + str(klen_v) + ",input:" + str(len(input[name])))
            if klen_p == ">":
                if len(input[name]) < klen_v:
                    return error_response(500, "请求参数异常...",
                                          "参数[" + k["name"] + "]长度不正确,ask:" + str(klen_v) + ",input:" + str(
                                              len(input[name])))
            if klen_p == "<":
                if len(input[name]) > klen_v:
                    return error_response(500, "请求参数异常...",
                                          "参数[" + k["name"] + "]长度不正确,ask:" + str(klen_v) + ",input:" + str(
                                              len(input[name])))
        if "value" in k:
            if input["name"] not in k["value"]:
                return error_response(500, "请求参数异常...", "参数[" + k["name"] + "]的值不在允许的范围内")
    return False


def request_obj():

    args ={}
    pargs = request.args
    form = request.form
    try:
        data = json.loads(request.data)
    except:
        data = {}
    for key in pargs.keys():
        args[key] = pargs[key]
    for key in form.keys():
        args[key] = form[key]
    for key in data.keys():
        args[key] = data[key]
    cookies = request.cookies
    method = request.method
    obj = {"args":args, "method":method, "cookies":cookies,"request":{"args":pargs,"form":form,"data":data}}
    return obj














