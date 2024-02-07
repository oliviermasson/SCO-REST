#! /bin/python3

import sys
pythonversion=sys.version_info
if pythonversion[0] != 3 or (pythonversion[1] < 6 or pythonversion[1] > 11):
    print("This script requires Python 3.6 through 3.11")
    sys.exit(1)
sys.path.append(sys.path[0] + "/NTAPlib")
import doREST
import userio
import datetime
import time
import getopt
import math

MAXTIMEOUT=2400 # wait max 40 minutes before timeout for backup job

validoptions={'url':'str',
              'resourcekey':'int',
              'resourcename':'str',
              'hostname':'str',
              'SmPolicy':'str',
              'VerifyAfterBackup':'bool',
              'VerifyOnSecondary':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','SmPolicy']
#dependentoptions=['VerifyAfterBackup','VerifyOnSecondary']

usage="create-backup\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          You need to Provide a resourcekey or resourcename and hostname\n\n" + \
      "          --resourcekey\n" + \
      "          specifies the resource key to backup\n" + \
      "          see get-sco-resource.py to get list of resource per hostname\n\n" + \
      "          \n" + \
      "          or\n" + \
      "          \n" + \
      "          --resourcename\n" + \
      "          specifies the resource name to backup\n" + \
      "          see get-sco-resource.py to get list of resource per hostname\n\n" + \
      "          --hostname\n" + \
      "          specifies the hostname to query\n" + \
      "          see get-sco-resource.py to get list resource per hostname\n\n" + \
      "          \n" + \
      "          --SmPolicy\n" + \
      "          specifies the policy name to user for this backup\n\n" + \
      "          [--VerifyAfterBackup]\n" + \
      "          optionally Verify after backup\n\n" + \
      "          [--VerifyOnSecondary]\n" + \
      "          optionally Verify from secondary\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
SmPolicy=myoptions['OPTS']['SmPolicy']
try:
    resourcekey=int(myoptions['OPTS']['resourcekey'])
except:
    resourcekey=None
try:
    resourcename=myoptions['OPTS']['resourcename']
except:
    resourcename=None
try:
    hostname=myoptions['OPTS']['hostname']
except:
    hostname=None
if(resourcekey is None and resourcename is None):
    print("ERROR : you must provide a resourcekey or resourcename plus hostname")
    sys.exit(1)    
try:
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False
try:
    VerifyAfterBackup=myoptions['OPTS']['VerifyAfterBackup']
except:
    VerifyAfterBackup=False
try:
    VerifyOnSecondary=myoptions['OPTS']['VerifyOnSecondary']
    if not VerifyAfterBackup:
        VerifyAfterBackup=True    
except:
    VerifyOnSecondary=False


api="/version"
scVersionResp=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug)
if scVersionResp.result == 0:
    scVersion=scVersionResp.response['ProductVersion']
    if scVersion not in '4.9 P1|5.0':
        print("ERROR : your SnapCenter server must be running version 4.9P1 or upper")
        sys.exit(1)
else:
    print("REST call failed")
    print(scVersionResp.reason)
    if scVersionResp.stdout is not None:
        for line in scVersionResp.stdout:
            print("STDOUT>> " + line)
    if scVersionResp.stderr is not None:
        for line in scVersionResp.stderr:
            print("STDERR>> " + line)
    sys.exit(1)


# retreive resource key with resource and hostname
if(resourcekey is None):
    api='/hosts/{}/plugins/SCO/resources'.format(hostname)
    restargs='ResourceType=Database&ResourceName={}'.format(resourcename)
    getResourceKey=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
    if getResourceKey.result == 0:
        resourcekey=getResourceKey.response['Resources'][0]['OperationResults'][0]['Target']['Key']
    else:
        print("ERROR: resource [{}] does not exist on host [{}]".format(resourcename,hostname))
        sys.exit(1)

api='/plugins/SCO/resources/{}/backup'.format(resourcekey)
restargs=None
if VerifyAfterBackup:
    restargs='verifyAfterBackup=True'
if VerifyOnSecondary:
    restargs=restargs + '&verifyInSecondary=True'
jsonargs={'name':SmPolicy}
# Perform POST backup operation
restBackups=doREST.doREST(url,'post',api,json=jsonargs,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if restBackups.result == 0:
    JobId=restBackups.response.split("/")[-1]    
    api='/jobs/{}'.format(JobId)
    # Wait end of returned jobid
    getJob=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
    if getJob.result == 0:
        jobPercentComplete=getJob.response['Results'][0]['PercentageComplete']
        begin = datetime.datetime.now()
        #print("begin time [{}]".format(begin))
        istimeout=False
        while int(jobPercentComplete) != 100:
            print("Job still in progress, Wait...")
            time.sleep(5)
            getJob=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
            if getJob.result == 0:
                jobPercentComplete=getJob.response['Results'][0]['PercentageComplete']
                now = datetime.datetime.now()
                delta = now - begin
                #print("now time [{}] delta is [{}]".format(now,delta.total_seconds()))
                if delta.total_seconds() > MAXTIMEOUT:
                    istimeout=True
                    break
            else:
                print("ERROR: getting job information")
                print("Please check SnapCenter GUI")
                sys.exit(1)
        #print("timeout is [{}]".format(istimeout))
        if istimeout is True:
            print("TIMEOUT (20 minutes): Check Job creation on Snapcenter GUI to see more detail on your job")
            sys.exit(1)
        print("Job Id [{}] is finished".format(JobId))
        JobStatus=getJob.response['Results'][0]['Status']
        JobError=getJob.response['Results'][0]['Error']
        JobJobStatus=getJob.response['Results'][0]['JobStatus']
        print("Status [{}]".format(JobStatus))
        print("Error [{}]".format(JobError))
        print("JobStatus [{}]".format(JobJobStatus))
        if JobError is not None:
            sys.exit(1)
        
        # Get backupname from jobid
        api='/backups'
        restargs='JobID={}'.format(JobId)
        getBackup=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if getBackup.result == 0:
            for BackupDetails in getBackup.response['Backups']:
                if BackupDetails['BackupType'].startswith('Oracle Database'):
                    print("[{}]".format(BackupDetails['BackupType']))
                    print("\tBackupName [{}]".format(BackupDetails['BackupName']))
                    print("\tBackupId   [{}]".format(BackupDetails['BackupId']))
                    print("\tBackupTime [{}]".format(BackupDetails['BackupTime']))
                    
else:
    print("REST call failed")
    print(restBackups.reason)
    if restBackups.stdout is not None:
        for line in restBackups.stdout:
            print("STDOUT>> " + line)
    if restBackups.stderr is not None:
        for line in restBackups.stderr:
            print("STDERR>> " + line)
    sys.exit(1)