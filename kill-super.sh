#!/bin/sh  
# kill  process and child process  
ps --ppid $1 | awk '{if($1~/[0-9]+/) print $1}'| xargs kill -9  
kill -9 $1  
pid=$1
echo "Kill Pid ${pid} Process And Child Process Success"
