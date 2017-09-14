#!/usr/bin/python3


""" This is monitor.py daemon
Example:
   $python monitory.py  <hostIpAddress> <interval>
   $python monitor.py 1.1.1.1 10


Program returns Customised report on process running,RAM usage,DISK usage for /var,syslog error count and
Change in these metrics  since last Moniorting.

Todo:
    * Code is not yet deployment ready .
    * Add platform check ,as each platform will have different command to monitor system resources
    * Syslog path can be derived config file or platform specific
    * Syslog archival aspect not tested
    * Add more try and exceptions to catch error and logging
    * Rewrite in Pythonic style
    * Test with different platform
    * Functions with default value
    * Make API more generic
    * os.popen is obsolete
"""
import sys
import subprocess
import time
import os
import datetime
CMD1='cat /proc/stat | grep procs_running'
CMD2='ps -eo pid,%mem,cmd --sort=-%mem | head -6'
CMD3="df -hl /var | awk 'BEGIN{print \"Use%\"} {percent+=$5;} END{print percent}' | tail -1"
CMD4="grep -i -e fail -e error -e corrupt /var/log/syslog"
CMD5='sudo tail -1 /var/log/syslog | cut -c 1-15'
"""Need to use these variable or define above commands in config file and parse """
SYSLOG_PATH='/var/log/syslog'
"""Best apprach is define in config file or derive based on platform """
startTimestamp=''
""" This variable tracks the last scanned syslog """

def getSyslogReport():
   """ Reports ERROR count from new syslogs
        Note:
        Args:
        Returns:
           Error count (Positive integer)
   """
   global startTimestamp
   try:
      cmd='sudo tail -n 1 /var/log/syslog| cut -c 1-15'
      proc=subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True)
      endTimestamp = proc.communicate()[0].rstrip()
   except:
      print("ERROR:::Could not collect details from:%s " %cmd)
      return -1
   if startTimestamp=='':
      cmd="awk '1,/%s/' /var/log/syslog | grep -i ERROR | wc -l" %endTimestamp
      """ Scan the entore syslog for ERROR"""
   else:
      try:
         cmd="sudo grep '%s' /var/log/syslog | wc -l " %startTimestamp
         proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
         timestampFound=proc.communicate()[0] 
      except:
         print("ERROR:::Could not get details of-> grep '^$(startTimestamp) /var/log/syslog' | wc -l ")
         return -1
      if int(timestampFound)>1:
         cmd="awk '/%s/,/%s/' /var/log/syslog | grep -i ERROR | wc -l" %(startTimestamp,endTimestamp)
      else:
         cmd="awk '1,/%s/' /var/log/syslog | grep -i ERROR | wc -l" %endTimestamp
   try:
      proc=subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True)
      errorCount = proc.communicate()[0]
   except:
      print("ERROR:::Could not collect details from:%s" %cmd)
      return -1
   startTimestamp=endTimestamp
   return int(errorCount)

def getMemoryUsage():
  """Gets top 5 process with highest memory usage
       Args:
       Returns:
           String containing Mem Reports """
  try:
     reportMem=os.popen('ps -eo pid,%mem,cmd --sort=-%mem | head -6').read()
  except:
     reportMem=-1
  return reportMem

def getDiskUsage():
   """Gets Disk usage for /var"""
   try:
      proc=subprocess.Popen(["df -hl /var | awk 'BEGIN{print \"Use%\"} {percent+=$5;} END{print percent}' | tail -1"],stdout=subprocess.PIPE, shell=True)
      reportDisk = proc.communicate()[0]
   except:
      print("ERROR:::Could not get df -hl /var detail")
      reportDisk=-1
   return int(reportDisk)

def getProcessCount(cmd='cat /proc/stat | grep procs_running'):
    """
       Gets total count of running  process
    """
    try:
       proc=subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True)
       pcount=proc.communicate()[0].split()[1]
    except:
       print("ERROR:::Could not get details from " +cmd)
       pcount=-1
    return int(pcount)



def getReport(interval):
    """
    Returns the Process Count ,disk usage, RAM usage,Syslog Error count
    """
    count1 = getProcessCount()
    duse1=getDiskUsage()
    ecount1=getSyslogReport()
    time.sleep(float(interval))
    count2=getProcessCount()
    duse2=getDiskUsage()
    ecount2=getSyslogReport()
    memUsage=getMemoryUsage()
   
    if (count1 == -1 or count2 == -1):
        preport=-1
    else:
       if count2 >= count1:
          diff='-'
       else:
           diff='+'
       preport=str(count2) +' '+diff+str(abs(count2-count1))
    if (duse1==-1 or duse2 == -1):
       dreport=-1
    else:
       if duse1 >= duse2:
          diff='-'
       else:
          diff='+'
       dreport=str(duse2) +' '+diff+str(abs(duse2-duse1))
    if (ecount1 ==-1 or ecount2==-1):
       ereport=-1
    else:
       if ecount1 >= ecount2:
          diff='-'
       else:
          diff='+'
       ereport=str(ecount2)+' '+diff+str(abs(ecount2-ecount1))
    return preport,dreport,ereport,memUsage



def processReport(interval):
    """
    Returns the cpu load as a value from the interval [0.0, 1.0]
    """
    print('*'*100)
    preport,dreport,ereport,memUsage = getReport(interval)
    print("\n\n"+str(datetime.datetime.now().isoformat())+" Summary of monitor daemon status")
    if preport != -1:
       print("INFO:Number of process running and change since last  monitoring:" +preport)
    else:
       print("ERROR:::Could not get report.Please look into the log(log is to be implemented:%s" %preport)
    if dreport !=1:
       print("INFO:%Disk usage and change in disk usage  since last  monitoring:" +dreport)
    else:
       pass
       print("ERROR:::Could not get report.Please look into the log(log is to be implemented:%s" %dreport)
    if ereport !=1:
       print("INFO:Syslog error count and change since last  monitoring:%s" %ereport)
    else:
       print("ERROR:::Could not get report.Please look into the log(log is to be implemented:" +ereport)
    print("INFO:Top 5 process using highest RAM\n" +memUsage)

NUM_ARGUMENT=2
if (len(sys.argv)-1 ==NUM_ARGUMENT):
  list1=sys.argv[1].split('.')
  if len(list1) !=4:
     print("Invalid IP address.IP address format x1.x2.x3.x4")
     sys.exit(1)
  for i in list1:
     if i > 255 and i<0:
        print("Invalid IP address format")
        sys.exit(1)
  while True:
    processReport(sys.argv[2])
    time.sleep(float(sys.argv[2]))
else:
  print("Usage is monitory.py  <hostIpAddress> <interval>")
  print("Usage is python monitor.py  127.0.0.1 60")
  print("Python daemon script which takes - two parameters as argument : IP address and monitoring interval in seconds")



