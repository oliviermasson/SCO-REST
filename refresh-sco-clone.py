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
              'resourcename':'str',
              'hostname':'str',
              'clonesid':'str',
              'backupname':'str',
              'clonetohost':'str',
              'SmPolicy':'str',
              'secondarytype':'str',
              'includesecondary':'bool',
              'secondarylocation':'str',
              'pdbclone':'bool',
              'jsonfilepath':'str',
              'foreground':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','resourcename','hostname','clonesid','clonetohost','SmPolicy']

usage="refresh-sco-clone\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --resourcename\n" + \
      "          specifies the resource name to clone\n\n" + \
      "          --hostname\n" + \
      "          specifies the hostname that host the resource to clone\n" + \
      "          see get-sco-resource.py to get list resource per hostname\n\n" + \
      "          --clonesid\n" + \
      "          Oracle SID name of the cloned DB (max 8 chars)\n" + \
      "          it will refresh this existing clone\n" + \
      "          if it does not exists it will create a new clone on the database SID provided in the clone specfile with same on demand backup data\n\n" + \
      "          --clonetohost\n" + \
      "          FQDN name of the host on which to attach this clone\n\n" + \
      "          [--jsonfilepath]\n" + \
      "          optionally specifies json file which contains all refresh parameters\n" + \
      "          this it not the clone specification file, which is directly added through dotenv variable created with previous create-sco-clone-specfile.py\n" + \
      "          by default import local file : ./refresh.json \n\n" + \
      "          [--backupname]\n" + \
      "          optionally specifies the backupname to use for the clone creation\n" + \
      "          default is to chose the lastest backup available for this resource\n" + \
      "          you can specify ondemand as backupname to forcibly create a new backup\n" + \
      "          that will be used for the clone operation\n\n" + \
      "          --SmPolicy\n" + \
      "          specifies the policy name to user for this backup\n\n" + \
      "          [--secondarytype]\n" + \
      "          optionally specifies the secondary type VAULT or MIRROR to clone\n" + \
      "          default is VAULT\n\n" + \
      "          [--includesecondary]\n" + \
      "          optionaly specifies if secondary information must be includesd inside the specfication file\n" + \
      "          default is False\n\n" + \
      "          [--secondarylocation]\n" + \
      "          optionally specifies secondary location with format <destination svm name>:<destination volume name>\n" + \
      "          by default the created specification file will choose the first secondary location available\n" + \
      "          see backup information to get this list of secondary location\n\n" + \
      "          [--pdbclone]\n" + \
      "          optionaly specifies if this clone will be used for PDB clone operation\n" + \
      "          default is False (CDB clone)\n\n" + \
      "          [--foreground]\n" + \
      "          Force the script to wait the end of the created job before returning\n" + \
      "          If not specified this script will only return the clone job id\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
resourcename=myoptions['OPTS']['resourcename']
hostname=myoptions['OPTS']['hostname']
clonesid=myoptions['OPTS']['clonesid']
clonetohost=myoptions['OPTS']['clonetohost']
SmPolicy=myoptions['OPTS']['SmPolicy']
try:
    jsonfilepath=myoptions['OPTS']['jsonfilepath']
except:
    jsonfilepath=os.path.dirname(os.path.realpath(__file__))+"/refreshpdb.json"
try:
    backupname=myoptions['OPTS']['backupname']
except:
    backupname = "Latest"
try:
    secondarytype=myoptions['OPTS']['secondarytype']
except:
    secondarytype = "VAULT"
try:
    includesecondary=myoptions['OPTS']['includesecondary']
except:
    includesecondary = False
try:
    secondarylocation=myoptions['OPTS']['secondarylocation']
    secondarySVM=secondarylocation.split(":")[0]
    secondaryVOL=secondarylocation.split(":")[-1]
except:
    secondarylocation = False
try:
    pdbclone=myoptions['OPTS']['pdbclone']
except:
    pdbclone = False
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


################################################### 0) Search previous clone

print("Search existing clone [{}] for resource [{}] on hostname [{}] ...".format(clonesid,resourcename,clonetohost))
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

api='/clones'
cloneid=None
resourceid='{}\\{}'.format(hostname,resourcename)
cloneDeletionNeeded=True
if resourceid is not None:
    restargs='AppObjectId={}'.format(resourceid)
    getClones=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
else:
    print("ERROR resourceid missing")
    sys.exit(1)
if len(getClones.response['Clones'])>1:
    print("ERROR resourceid [{}] must have one and uniq clone\nCurrently there is [{}] clone(s)".format(resourceid,len(getClones.response['Clones'])))
    sys.exit(1)
if len(getClones.response['Clones'])==1:
    if getClones.result == 0:
        clonematch=False
        for clone in getClones.response['Clones']:
            cloneid=clone['CloneID']
            for cloneObject in clone['CloneObjects']:
                DBsid=cloneObject['CloneObject']['Name']
                if DBsid.endswith(clonesid):
                    clonematch=True
                    print("Find clone [{}] with ID [{}]".format(DBsid,cloneid))
                    break
    if clonematch is False:
        print("ERROR failed to find clone with SID [{}]".format(clonesid))
        sys.exit(1)
else:
    cloneDeletionNeeded=False

################################################### 1) Delete previous clone
if cloneDeletionNeeded is True:      
    print("Delete clone id [{}]".format(cloneid))
    if cloneid is not None:
        api='/clones/{}'.format(cloneid)
        restargs='PluginCode=SCO'  
        deleteClone=doREST.doREST(url,'delete',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
    if deleteClone.result == 0:
        if deleteClone.response['Result']['_errorCode'] != 0:
            print("ERROR [{}]".format(deleteClone.response['Result']['_message']))
            sys.exit(1)
        JobName=deleteClone.response['Job']['Name']
        JobId=deleteClone.response['Job']['Id']
        print("Delete Clone Job Name [{}] with Id [{}] created succesfully on SnapCenter server ".format(JobName,JobId))
        # wait end of Job before returning
        api='/jobs/{}'.format(JobId)
        getJob=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if getJob.result == 0:
            jobPercentComplete=getJob.response['Results'][0]['PercentageComplete']
            begin = datetime.datetime.now()
            #print("begin time [{}]".format(begin))
            istimeout=False
            while int(jobPercentComplete) != 100:
                if debug:
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
    else:
        print("ERROR cloneid is missing")
        sys.exit(1)
else:
    print("Skip clone deletion")

################################################### 2) Create a new backup if not specified, instead use the one provided as argument

# if backupname is not provided as parameter, it will clone through the latest backup available
# if backupname is "ondemand", it will create a new backup that will then be used for the clone operation
# if backupname is passed as parameter and it exists for the ressource, it will be used for the clone operation
    
if backupname == 'Latest':
    print("Lastest backup will be used")
elif backupname == 'ondemand':
    print("Create a new ondemand backup")
    # retreive resource key with resource and hostname
    api='/hosts/{}/plugins/SCO/resources'.format(hostname)
    restargs='ResourceType=Database&ResourceName={}'.format(resourcename)
    getResourceKey=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
    if getResourceKey.result == 0:
        resourcekey=getResourceKey.response['Resources'][0]['OperationResults'][0]['Target']['Key']
    else:
        print("ERROR: resource [{}] does not exist on host [{}]".format(resourcename,hostname))
        sys.exit(1)
    api='/plugins/SCO/resources/{}/backup'.format(resourcekey)
    jsonargs={'name':SmPolicy}
    # Perform POST backup operation
    restBackups=doREST.doREST(url,'post',api,json=jsonargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
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
                if debug:
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
                        if(BackupDetails['BackupType']=='Oracle Database Data Backup'):
                            backupname=BackupDetails['BackupName']
                            print("Clone will be created with backupname [{}]".format(backupname))
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
else:
    print("Clone will be created with backupname [{}]".format(backupname))

################################################### 3) Create a clone specification file for this refresh clone operation

if secondarytype != "VAULT" and secondarytype != "MIRROR":
    print("ERROR [secondarytype must be 'VAULT' or 'MIRROR']")
    sys.exit(1)
print("Create SCO clone specification file on [" + url + "] for resource [" + resourcename + "]...")
print("\n")

# retreive resource key with resource and hostname
api='/hosts/{}/plugins/SCO/resources'.format(hostname)
restargs='ResourceType=Database&ResourceName={}'.format(resourcename)
getResourceKey=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if getResourceKey.result == 0:
    resourcekey=getResourceKey.response['Resources'][0]['OperationResults'][0]['Target']['Key']
else:
    print("REST call failed")
    print(getResourceKey.reason)
    if getResourceKey.stdout is not None:
        for line in getResourceKey.stdout:
            print("STDOUT>> " + line)
    if getResourceKey.stderr is not None:
        for line in getResourceKey.stderr:
            print("STDERR>> " + line)
    print("ERROR: resource [{}] does not exist on host [{}]".format(resourcename,hostname))
    sys.exit(1)

api='/plugins/SCO/resources/{}/clonespecification'.format(resourcekey)
jsonargs={'CloneDatabaseSID':clonesid}

if backupname == "Latest":
    jsonargs['CloneLastBackup']=0
# elif backupname.isnumeric():
#     jsonargs['CloneLastBackup']=backupname
else:
    jsonargs['BackupName']=backupname
if includesecondary is not False:
    jsonargs['IncludeSecondaryDetails']=True
    jsonargs['SecondaryStorageType']=secondarytype
jsonargs['PDBClone']=pdbclone

restSpecfile=doREST.doREST(url,'post',api,json=jsonargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if restSpecfile.result == 0:
    if restSpecfile.response['Result']['_errorCode'] != 0:
        print("ERROR [{}]".format(restSpecfile.response['Result']['_message']))
        sys.exit(1)
    print("Clone Specification File created succesfully on SnapCenter server at [{}{}]".format(restSpecfile.response['CloneSpecFilePath'],restSpecfile.response['CloneSpecFileName']))
    clone_spec_filepath="{}{}".format(restSpecfile.response['CloneSpecFilePath'],restSpecfile.response['CloneSpecFileName'])

    variable_name = 'SCO_CLONE_SPECFILE'

    with open('.env', 'w') as envfile:
        envfile.write('%s=%s\n' % (variable_name,repr(clone_spec_filepath)))
    
    env_vars = dotenv_values('.env')
    print("Set local dotenv variable %s [%s]" % (variable_name,repr(env_vars[variable_name])))

    if secondarylocation:
        
        # get clonespecificationfile before modify secondary location

        api='/clones/SCO/clonespecification/{}'.format(restSpecfile.response['CloneSpecFileName'])
        getSpecfile=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if getSpecfile.result == 0:
            if getSpecfile.response['Result']['_errorCode'] != 0:
                print("ERROR [{}]".format(getSpecfile.response['Result']['_message']))
                sys.exit(1)
        CloneSpecFileData=getSpecfile.response['oracleCloneSpecification']
        CloneSpecFileData['storage-specification']['storage-mapping']['secondary-configuration-datafiles']['secondary-locators']['secondary-locator'][0]['secondary']['svm']=secondarySVM
        CloneSpecFileData['storage-specification']['storage-mapping']['secondary-configuration-datafiles']['secondary-locators']['secondary-locator'][0]['secondary']['volume']=secondaryVOL

        # push modified clonespecificationfile into snapcenter server

        api='/clones/SCO/clonespecification/{}'.format(restSpecfile.response['CloneSpecFileName'])
        putSpecfile=doREST.doREST(url,'put',api,json=CloneSpecFileData,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if putSpecfile.result == 0:
            if putSpecfile.response['Result']['_errorCode'] != 0:
                print("ERROR [{}]".format(putSpecfile.response['Result']['_message']))
                sys.exit(1)
        else:
            print("ERROR [{}]".format(putSpecfile.reason,))
            sys.exit(1)
        print("Clone Specification File succesfully updated on SnapCenter server with new secondary location [{}]".format(secondarylocation))
else:
    print("REST call failed")
    print(restSpecfile.reason)
    if restSpecfile.stdout is not None:
        for line in restSpecfile.stdout:
            print("STDOUT>> " + line)
    if restSpecfile.stderr is not None:
        for line in restSpecfile.stderr:
            print("STDERR>> " + line)
    sys.exit(1)

################################################### 4) Create a new clone

variable_name = 'SCO_CLONE_SPECFILE'
env_vars = dotenv_values('.env')
#print("Get local dotenv variable %s [%s]" % (variable_name,repr(env_vars[variable_name])))
try:
    clone_spec_filepath=env_vars[variable_name]
except:
    print("ERROR: dotenv variable SCO_CLONE_SPECFILE not created. Please run create-sco-clone-specfile.py before running refresh operation")
    sys.exit(1)

api='/plugins/SCO/resources/clone'
with open(jsonfilepath) as json_file:
    jsonargs=json.load(json_file)

jsonargs['OracleCloneSpecificationFile']=clone_spec_filepath
jsonargs['CloneToHost']=clonetohost
#jsonargs['CloneDatabaseSID']=clonesid
restCreateClone=doREST.doREST(url,'post',api,json=jsonargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if restCreateClone.result == 0:
    if restCreateClone.response['Result']['_errorCode'] != 0:
        print("ERROR [{}]".format(restCreateClone.response['Result']['_message']))
        sys.exit(1)
    JobName=restCreateClone.response['Job']['Name']
    JobId=restCreateClone.response['Job']['Id']
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
                if debug:
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
    print(restCreateClone.reason)
    if restCreateClone.stdout is not None:
        for line in restCreateClone.stdout:
            print("STDOUT>> " + line)
    if restCreateClone.stderr is not None:
        for line in restCreateClone.stderr:
            print("STDERR>> " + line)
    sys.exit(1)    