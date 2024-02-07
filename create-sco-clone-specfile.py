#! /bin/python3

import sys
pythonversion=sys.version_info
if pythonversion[0] != 3 or (pythonversion[1] < 6 or pythonversion[1] > 11):
    print("This script requires Python 3.6 through 3.11")
    sys.exit(1)

sys.path.append(sys.path[0] + "/NTAPlib")
import doREST
import userio
import getopt
import os
from dotenv import dotenv_values


validoptions={'url':'str',
              'resourcename':'str',
              'hostname':'str',
              'specfilename':'str',
              'backupname':'str',
              'clonesid':'str',
              'secondarytype':'str',
              'includesecondary':'bool',
              'secondarylocation':'str',
              'pdbclone':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','resourcename','hostname','clonesid']

usage="create-sco-clone-specfile\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --resourcename\n" + \
      "          specifies the resource name to clone\n\n" + \
      "          --hostname\n" + \
      "          specifies the hostname that host the resource to clone\n" + \
      "          see get-sco-resource.py to get list resource per hostname\n\n" + \
      "          --clonesid\n" + \
      "          specifies the clone SID name (max 8 chars)\n\n" + \
      "          [--specfilename]\n" + \
      "          optionally specifies clone specification filename\n" + \
      "          default is \"oracle_clonespec_dbName_cloneSID_timeStamp.xml\"\n\n" + \
      "          [--backupname]\n" + \
      "          optionally specifies the backupname to use for the clone creation\n" + \
      "          default is to chose the lastest backup available for this resource\n\n" + \
      "          [--secondarytype]\n" + \
      "          optionally specifies the secondary type VAULT or MIRROR to clone\n" + \
      "          default is VAULT\n\n" + \
      "          [--includesecondary]\n" + \
      "          optionaly specifies is secondary information must be includesd inside the specfication file\n" + \
      "          default is False\n\n" + \
      "          [--secondarylocation]\n" + \
      "          optionally specifies secondary location with format <destination svm name>:<destination volume name>\n" + \
      "          by default the created specification file will choose the first secondary location available\n" + \
      "          see backup information to get this list of secondary location\n\n" + \
      "          [--pdbclone]\n" + \
      "          optionaly specifies if this clone will be used for PDB clone operation\n" + \
      "          default is False (CDB clone)\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
resourcename=myoptions['OPTS']['resourcename']
hostname=myoptions['OPTS']['hostname']
clonesid=myoptions['OPTS']['clonesid']
try:
    specfilename=myoptions['OPTS']['specfilename']
except:
    specfilename = None
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
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False

if secondarytype != "VAULT" and secondarytype != "MIRROR":
    print("ERROR [secondarytype must be 'VAULT' or 'MIRROR']")
    sys.exit(1)
print("Create SCO clone specification file on [" + url + "] for resource [" + resourcename + "]...")
print("\n")

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
if specfilename is not None:
    jsonargs['OracleCloneSpecificationFileName']=specfilename
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
        
        #get clonespecificationfile before modify secondary location

        api='/clones/SCO/clonespecification/{}'.format(restSpecfile.response['CloneSpecFileName'])
        getSpecfile=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if getSpecfile.result == 0:
            if getSpecfile.response['Result']['_errorCode'] != 0:
                print("ERROR [{}]".format(getSpecfile.response['Result']['_message']))
                sys.exit(1)
        CloneSpecFileData=getSpecfile.response['oracleCloneSpecification']
        CloneSpecFileData['storage-specification']['storage-mapping']['secondary-configuration-datafiles']['secondary-locators']['secondary-locator'][0]['secondary']['svm']=secondarySVM
        CloneSpecFileData['storage-specification']['storage-mapping']['secondary-configuration-datafiles']['secondary-locators']['secondary-locator'][0]['secondary']['volume']=secondaryVOL

        #push modified clonespecificationfile into snapcenter server

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