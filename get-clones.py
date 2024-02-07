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
import re

validoptions={'url':'str',
              'resourceid':'str',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','resourceid']

usage="get-clones\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --resourceid\n" + \
      "          specifies the source resource name to query\n" + \
      "          use get-sco-resources.py to get resource id\n" + \
      "          examples: \n" + \
      "          rac\\\iSCSI\n" + \
      "          racn3.netapp.com\\\OM3\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
resourceid=myoptions['OPTS']['resourceid']
try:
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False

print("Retrieving all clones available on [" + url + "] for resource [" + resourceid + "]...")


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
if resourceid is not None:
    restargs='AppObjectId={}'.format(resourceid)
    getClones=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
else:
    getClones=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug,scVersion=scVersion)
print("Total number of clone present for resource [{}] = [{}]".format(resourceid,len(getClones.response['Clones'])))
if getClones.result == 0:
    for clone in getClones.response['Clones']:
        print("\tClone attached to HostName   : {}".format(clone['SmCloneHost']['HostName']))
        if clone['SmCloneHost']['ClusterHost'] is True:
            print("\tClusterName                  : {}".format(clone['SmCloneHost']['ClusterName']))
            print("\tCluster Members              : {}".format(clone['SmCloneHost']['Members']))
        print("\tCloneLevel                   : {}".format(clone['SmCloneHost']['CloneLevel']))
        print("\tCloneID                      : {}".format(clone['CloneID']))
        print("\tCloneName                    : {}".format(clone['CloneName']))
        print("\tBackupame                    : {}".format(clone['BackupName']))
        for smcloneobject in clone['CloneObjects']:
            print("\tSource DBsid                 : {}".format(smcloneobject['SourceObject']['dbSid']))
            print("\tSource SC Id                 : {}".format(smcloneobject['SourceObject']['Id']))
            print("\tSource dvVersion             : {}".format(smcloneobject['SourceObject']['dbVersion']))
            print("\tSource Type                  : {}".format(smcloneobject['SourceObject']['Type']))
            #print("\tSource Status                : {}".format(smcloneobject['SourceObject']['DatabaseStatus']))
            print("\tis in ArchiveLog Mode        : {}".format(smcloneobject['SourceObject']['IsInArchiveLogMode']))
            print("\tDest DBsid                   : {}".format(smcloneobject['CloneObject']['dbSid']))
            print("\tDest SC Id                   : {}".format(smcloneobject['CloneObject']['Id']))
            #print("\tDest Status                  : {}".format(smcloneobject['CloneObject']['DatabaseStatus']))
            print("\tPDBNames                     : {}".format(smcloneobject['SourceObject']['PDBNames']))
        for component in clone['CloneComponents']['CloneComponentMapping']:
            if len(component['SnapshotName']) > 0:
                print("\tSnapshotName                 : {}".format(component['SnapshotName']))
                for storage in component['sourcestorageFootPrint']['StorageSystemResources']:
                    print("\tResourceName                 : {}".format(storage['ResourceName']))
                    print("\tVolumeName                   : {}".format(storage['Volume']['Name']))
                    print("\tAggregateName                : {}".format(storage['Volume']['AggregateName']))
                for system in component['clonestorageFootPrint']['StorageSystemResources']:
                    print("\tLogicalPath                  : {}".format(system['LogicalPath']))
        print("\n")
else:
    print("REST call failed")
    print(getClones.reason)
    if getClones.stdout is not None:
        for line in getClones.stdout:
            print("STDOUT>> " + line)
    if getClones.stderr is not None:
        for line in getClones.stderr:
            print("STDERR>> " + line)
    sys.exit(1)    