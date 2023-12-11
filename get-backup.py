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
import math

validoptions={'url':'str',
              'resourcename':'str',
              'hostname':'str',
              'aggr':'bool',
              'secondary':'bool',
              'debug':'bool',
              'restdebug':'bool'}

requiredoptions=['url','resourcename','hostname']

usage="get-backup\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --resourcename\n" + \
      "          specifies the resource name to query\n\n" + \
      "          --hostname\n" + \
      "          specifies the hostname to query\n" + \
      "          see get-sco-resource.py to get list resource per hostname\n\n" + \
      "          [--aggr]\n" + \
      "          optionally display hosting aggr name\n\n" + \
      "          [--secondary]\n" + \
      "          optionally display backup only from secondary locations\n" + \
      "          by default only display primary backup\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
resourcename=myoptions['OPTS']['resourcename']
hostname=myoptions['OPTS']['hostname']
try:
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False
try:
    secondary=myoptions['OPTS']['secondary']
except:
    secondary=False
try:
    aggr=myoptions['OPTS']['aggr']
except:
    aggr=False


if secondary:
    print("Retrieving secondary backup only on [" + url + "] for resource [" + resourcename + "]...")
else:
    print("Retrieving all backups on [" + url + "] for resource [" + resourcename + "]...")
print("\n")

api="/version"
scVersionResp=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug)
if scVersionResp.result == 0:
    scVersion=scVersionResp.response['ProductVersion']
    if scVersion not in '4.9 P1|5.0':
        print("ERROR : your SnapCenter server must be running version 4.8 or upper")
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
    print("ERROR: resource [{}] does not exist on host [{}]".format(resourcename,hostname))
    sys.exit(1)

api='/backups'
restargs='Resource={}'.format(resourcename)
if secondary:
    restargs=restargs + '&Secondary=True'
restBackups=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
totalLocation=0
if restBackups.result == 0:
    for backups in restBackups.response['Backups']:
        print("\tBackupName          : {}".format(backups['BackupName']))
        print("\tBackupId            : {}".format(backups['BackupId']))
        print("\tBackupType          : {}".format(backups['BackupType']))
        print("\tBackupTime          : {}".format(backups['BackupTime']))
        print("\tProtectionGroupName : {}".format(backups['ProtectionGroupName']))
        print("\tPolicyName          : {}".format(backups['PolicyName']))
        print("\tIsClone             : {}".format(backups['IsClone']))
        for components in backups['BackupComponents']:
            print("\tWith Secondary      : {}".format(components['IsSecondary']))
            for snapshots in components['SmSnapshots']:
                for storageresource in snapshots['SnapshotLocator']['StorageFootprint']['StorageSystemResources']:
                    print("\t\tSource              : {}".format(storageresource['ResourceName']))
                    if aggr:
                        print("\t\tAggregate           : {}".format(storageresource['Volume']['AggregateName']))
        api='/plugins/SCO/{}/secondarydetails'.format(resourcekey)
        restargs='BackupId={}'.format(backups['BackupId'])
        restSecondary=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
        if restSecondary.result == 0:
            if restSecondary.response['Result']['_errorCode'] == 0:
                if len(restSecondary.response['ArchivedDetails']) >= 1:
                    for secondarydetails in restSecondary.response['ArchivedDetails']:
                        for destdetails in secondarydetails['Secondaries']:
                            relationtype=destdetails['RelationshipType']
                            if relationtype == 2:
                                secondarytype='VAULT'
                            else:
                                secondarytype='MIRROR'
                            print("\t\t\tDestination[{}]         : {}:{}".format(secondarytype,destdetails['StorageSystemName'],destdetails['StorageVolumeName']))
                        print("\t\t\tTotal Secondary = [{}]".format(len(secondarydetails['Secondaries'])))
                        totalLocation+=len(secondarydetails['Secondaries'])
        print("\n")
    if secondary:
        print("Total Backups = [{}] over a total of locations = [{}]".format(len(restBackups.response['Backups']),totalLocation))
    else:
        print("Total Backups = [{}]".format(len(restBackups.response['Backups'])))
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