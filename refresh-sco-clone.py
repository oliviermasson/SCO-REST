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
import json
import os

validoptions={'url':'str',
              'clonesid':'str',
              'clonetohost':'str',
              'jsonfilepath':'str',
              'foreground':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','clonesid','clonetohost']

usage="refresh-sco-clone\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --clonesid\n" + \
      "          Oracle SID name of the cloned DB (max 8 chars)\n" + \
      "          it will refresh this existing clone\n" + \
      "          if it does not exists it will create a new clone on the database SID provided in the clone specfile with same on demand backup data\n\n" + \
      "          --clonetohost\n" + \
      "          FQDN name of the host on which to attach this clone\n\n" + \
      "          [--jsonfilepath]\n" + \
      "          optionally specifies json file which contains all refresh parameters\n" + \
      "          clone specification file paramter is directly added through dotenv variable created with create-sco-clone-specfile.py\n" + \
      "          be default import local file : ./refresh.json \n\n" + \
      "          [--foreground]\n" + \
      "          Force the script to wait the end of the created job before returning\n" + \
      "          If not specified this script will only return the clone job id\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
clonesid=myoptions['OPTS']['clonesid']
clonetohost=myoptions['OPTS']['clonetohost']
try:
    jsonfilepath=myoptions['OPTS']['jsonfilepath']
except:
    jsonfilepath=os.path.dirname(os.path.realpath(__file__))+"\\refresh.json"
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

variable_name = 'SCO_CLONE_SPECFILE'
env_vars = dotenv_values('.env')
#print("Get local dotenv variable %s [%s]" % (variable_name,repr(env_vars[variable_name])))
try:
    clone_spec_filepath=env_vars[variable_name]
except:
    print("ERROR: dotenv variable SCO_CLONE_SPECFILE not created. Please run create-sco-clone-specfile.py before running refresh operation")
    sys.exit(1)

print("Refresh SCO clone on [" + url + "] with specification file [" + clone_spec_filepath + "] and clone SID [" + clonesid + "] with new OnDemand backup data...")
print("\n")

api="/version"
scVersionResp=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug)
if scVersionResp.result == 0:
    scVersion=scVersionResp.response['ProductVersion']
    if scVersion not in '4.9 P1|5.0':
        print("ERROR: your SnapCenter server must be running version 4.8 or upper")
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

api='/plugins/SCO/resources/refreshclone'
with open(jsonfilepath) as json_file:
    jsonargs=json.load(json_file)

""" jsonargs={'OracleCloneSpecificationFile':clone_spec_filepath}
jsonargs['OracleSkipRecovery']=True
jsonargs['EnableEmail']=False
jsonargs['SkipNIDcreation']=True
jsonargs['SkipTempTablespaceTempFileCreation']=True
jsonargs['OpenPluggableDatabaseAfterClone']=True """

jsonargs['OracleCloneSpecificationFile']=clone_spec_filepath
jsonargs['CloneToHost']=clonetohost
jsonargs['CloneDatabaseSID']=clonesid

refreshClone=doREST.doREST(url,'post',api,json=jsonargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if refreshClone.result == 0:
    if refreshClone.response['Result']['_errorCode'] != 0:
        print("ERROR [{}]".format(refreshClone.response['Result']['_message']))
        sys.exit(1)
    JobName=refreshClone.response['Job']['Name']
    JobId=refreshClone.response['Job']['Id']
    print("Clone Job Name [{}] with Id [{}] created succesfully on SnapCenter server ".format(JobName,JobId))
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
            #print("timeout is [{}]".format(istimeout))
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
    print(refreshClone.reason)
    if refreshClone.stdout is not None:
        for line in refreshClone.stdout:
            print("STDOUT>> " + line)
    if refreshClone.stderr is not None:
        for line in refreshClone.stderr:
            print("STDERR>> " + line)
    sys.exit(1)    