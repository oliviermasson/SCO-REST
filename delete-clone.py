#! /bin/python3

import sys
pythonversion=sys.version_info
if pythonversion[0] != 3 or (pythonversion[1] < 6 or pythonversion[1] > 11):
    print("This script requires Python 3.6 through 3.11")
    sys.exit(1)

MAXTIMEOUT=1200 # wait max 20 minutes before timeout for job creation

sys.path.append(sys.path[0] + "/NTAPlib")
import doREST
import userio
import getopt
import os
from dotenv import dotenv_values
import datetime
import time

validoptions={'url':'str',
              'cloneid':'str',
              'clonetype':'str',
              'foreground':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','cloneid']

usage="delete-clone\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --cloneid\n" + \
      "          Id of the clone to delete\n" + \
      "          This can be found with get-clone.py\n\n" + \
      "          [--clonetype]\n" + \
      "          optionally specifies the clone plugin type (VSC 'for VMWare), SMSQL, SCO 'for Oracle' or CustomPlugin\n" + \
      "          default is SCO for Oracle\n\n" + \
      "          [--foreground]\n" + \
      "          Force the script to wait the end of the created job before returning\n" + \
      "          If not specified this script will only return the clone job id\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
cloneid=myoptions['OPTS']['cloneid']
try:
    clonetype=myoptions['OPTS']['clonetype']
except:
    clonetype="SCO"
try:
    foreground=myoptions['OPTS']['foreground']
except:
    foreground=False
try:
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False

print("Delete SCO clone with id [" + cloneid + "] on [" + url + "] ...")
print("\n")

api="/version"
scVersionResp=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug)
if scVersionResp.result == 0:
    scVersion=scVersionResp.response['ProductVersion']
    if scVersion not in '4.9 P1|5.0':
        print("ERROR: your SnapCenter server must be running version 4.9P1 or upper")
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

api='/clones/{}'.format(cloneid)
restargs='PluginCode={}'.format(clonetype)

deleteClone=doREST.doREST(url,'delete',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if deleteClone.result == 0:
    if deleteClone.response['Result']['_errorCode'] != 0:
        print("ERROR [{}]".format(deleteClone.response['Result']['_message']))
        sys.exit(1)
    JobName=deleteClone.response['Job']['Name']
    JobId=deleteClone.response['Job']['Id']
    print("Delete Clone Job Name [{}] with Id [{}] created succesfully on SnapCenter server ".format(JobName,JobId))
    if foreground:
        # wait end of Job before returning
        api='/jobs/{}'.format(JobId)
        getJob=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if getJob.result == 0:
            jobPercentComplete=getJob.response['Results'][0]['PercentageComplete']
            begin = datetime.datetime.now()
            #print("begin time [{}]".format(begin))
            istimeout=False
            while int(jobPercentComplete) != 100:
                print("Job still in progress, Wait...")
                time.sleep(5)
                loopGetJob=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
                if loopGetJob.result == 0:
                    jobPercentComplete=loopGetJob.response['Results'][0]['PercentageComplete']
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
            print("timeout is [{}]".format(istimeout))
            if istimeout is True:
                print("TIMEOUT (20 minutes): Check Job creation on Snapcenter GUI to see more detail on your job")
                sys.exit(1)
            print("Job Id [{}] is finished".format(JobId))
            JobStatus=loopGetJob.response['Results'][0]['Status']
            JobError=loopGetJob.response['Results'][0]['Error']
            JobJobStatus=loopGetJob.response['Results'][0]['JobStatus']
            print("Status [{}]".format(JobStatus))
            print("Error : {}".format(JobError))
            print("JobStatus [{}]".format(JobJobStatus))
            if JobError is not None:
                sys.exit(1)
else:
    print("REST call failed")
    print(deleteClone.reason)
    if deleteClone.stdout is not None:
        for line in deleteClone.stdout:
            print("STDOUT>> " + line)
    if deleteClone.stderr is not None:
        for line in deleteClone.stderr:
            print("STDERR>> " + line)
    sys.exit(1)    