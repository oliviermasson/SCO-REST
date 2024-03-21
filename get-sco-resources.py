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

validoptions={'url':'str',
              'hostname':'str',
              'debug':'bool',
              'resourcetype':'str',
              'resourcename':'str',
              'restdebug':'bool'}

requiredoptions=['url','hostname']

usage="get-sco-resources\n" + \
      "           --url\n" + \
      "          <fqdn:port> of Snapcenter server\n\n" + \
      "          --hostname\n" + \
      "          name of the host or RAC cluster node\n\n" + \
      "          [--resourcetype]\n" + \
      "          optionally specifies the resource type Database or ApplicationVolume\n" + \
      "          default is database\n\n" + \
      "          [--resourcename]\n" + \
      "          optionally specifies the resource name\n\n" + \
      "          [--debug]\n" + \
      "          optionally show debug output\n\n" + \
      "          [--restdebug]\n" + \
      "          optionally show REST API calls and responses\n\n" 

myoptions=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

url=myoptions['OPTS']['url']
hostname=myoptions['OPTS']['hostname']
try:
    resourcetype=myoptions['OPTS']['resourcetype']
except:
    resourcetype='Database'
try:
    resourcename=myoptions['OPTS']['resourcename']
except:
    resourcename=None
try:
    debug=myoptions['OPTS']['debug']
except:
    debug=False
try:
    restdebug=myoptions['OPTS']['restdebug']
except:
    restdebug=False



print("Retrieving SCO resources on [" + url + "] from hostname [" + hostname + "]...")
print("\n")

api="/version"
scVersionResp=doREST.doREST(url,'get',api,debug=debug,restdebug=restdebug)
if scVersionResp.result == 0:
    scVersion=scVersionResp.response['ProductVersion']
    if (scVersion not in '4.9 P1|5.0'):
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

api='/hosts/{}/plugins/SCO/resources'.format(hostname)
restargs='ResourceType=Database&UseKnwonResources=False'
rest=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
if rest.result == 0:
    for resource in rest.response['Resources']: 
        for OperationResult in resource['OperationResults']:
            if resourcename is not None:
                if resourcename != OperationResult['Target']['Name']:
                    continue
            print("Name : {}".format(OperationResult['Target']['Name']))
            print("\tKey              : {}".format(OperationResult['Target']['Key']))
            print("\tdbVersion        : {}".format(OperationResult['Target']['dbVersion']))
            print("\tId               : {}".format(OperationResult['Target']['Id']))
            print("\tdbId             : {}".format(OperationResult['Target']['dbId']))
            print("\tHosts            : {}".format(OperationResult['Target']['Hosts']))
            print("\tDbUniqueName     : {}".format(OperationResult['Target']['DbUniqueName']))
            print("\tIsClone          : {}".format(OperationResult['Target']['IsClone']))
            print("\tDatabaseStatus   : {}".format(OperationResult['Target']['DatabaseStatus']))
            print("\tLastBackupDate   : {}".format(OperationResult['Target']['LastBackupDate']))
            print("\tLastBackupStatus : {}".format(OperationResult['Target']['LastBackupStatus']))
            print("\tIsProtected      : {}".format(OperationResult['Target']['IsProtected']))
            #print("\tPDBNames         : {}".format(OperationResult['Target']['PDBNames']))
            api='/hosts/{}/resources/detail'.format(hostname)
            restargs='guid={}'.format(OperationResult['Target']['Id'].replace("\\","%5C"))
            restdetails=doREST.doREST(url,'get',api,restargs=restargs,debug=debug,restdebug=restdebug,scVersion=scVersion)
            if rest.result == 0:
                if restdetails.response['AppObject']['PDBNames'] is not None:
                    for pdbs in restdetails.response['AppObject']['PDBNames']:
                        print("\t\tPDBName         : {}".format(pdbs['Value']))
                    print("\t\tTotal PDB = [{}]".format(len(restdetails.response['AppObject']['PDBNames'])))
            print("\n")
else:
    print("REST call failed")
    print(rest.reason)
    if rest.stdout is not None:
        for line in rest.stdout:
            print("STDOUT>> " + line)
    if rest.stderr is not None:
        for line in rest.stderr:
            print("STDERR>> " + line)
    sys.exit(1)    