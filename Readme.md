# REST API SnapCenter for Oracle examples

I created these scripts to demonstrate SnapCenter's capabilities with the REST API, in an Oracle environment.

### **_These scripts are provided "as is" and withtout any support from NetApp._**

These scripts require at least Python v3.6 and SnapCenter v4.9P1 or upper

| Name | Purpose |
|------|---------|
| **get-sco-resources.py** | List Oracle resource available per host |
| **get-backup.py** | List all backup available for a ressource |
| **get-clones.py** | List all clone available for a ressource |
| **create-sco-backup.py** | Create an OnDemand backup for a ressource |
| **create-sco-clone-specfile.py** | Create a clone specification file |
| **create-sco-clone.py** | Create a clone from a specification file<br>Compatible for CDB and PDB clone |
| **refresh-sco-clone.py** | Refresh an existing CDB or PDB clone with Latest backup or new OnDemand backup or existing backup | 
| **delete-clone.py** | Delete an existing clone |
| **clone.json** | Example of JSON file for CDB clone creation |
| **pdbclone.json** | Example of JSON file for PDB clone creation |
| **refresh.json** | Example of JSON file for CDB clone refresh |
| **refreshpdb.json** | Example of JSON file for PDB clone refresh |

<br>


Before using these scripts you must create a token from SC swagger ``https://<snapcenter url>:<port>/swagger``.  
  
Example to create a non-expiring token:
```
curl -X 'POST' \
  'https://snapcenterurl:8146/api/4.9/auth/login?TokenNeverExpires=false' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "UserOperationContext": {
    "User": {
      "Name": "domain\\user",
      "Passphrase": "password",
      "Rolename": "role"
    }
  }
}'
```

And export this token as an environment variable named ``SCO_TOKEN``

Before creating a clone, you must create a clone specification file (stored on the snapcenter server).  
This clone specification file must then be used by the ``create-clone.py``  
To simplify the automation of this, the path on the snapcenter server to this clone specification file is passed from ``create-sco-clone-specfile.py`` to ``create-clone.py`` through a **.env variable** as ``SCO_CLONE_SPECFILE`` variable

Examples:

**Get SCO resource available on hostname racnode4 :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./get-sco-resources.py --url snapcenter.demo.com:8146 --hostname racnode4.demo.com
Retrieving SCO resources on [snapcenter.demo.com:8146] from hostname [racnode4.demo.com]...


Name : OM4
        Key              : 1234
        dbVersion        : 19.0.0.0.0
        Id               : racnode4.demo.com\OM4
        dbId             : 1804048823
        Hosts            : None
        DbUniqueName     : OM4
        IsClone          : False
        DatabaseStatus   : 4
        LastBackupDate   : None
        LastBackupStatus : Not protected
        IsProtected      : False
                PDBName         : PDB$SEED
                PDBName         : OM4PDB
                Total PDB = [2]


Name : OM3cl1
        Key              : 1286
        dbVersion        : 19.0.0.0.0
        Id               : racnode4.demo.com\OM3cl1
        dbId             : 0
        Hosts            : None
        DbUniqueName     : OM3cl1
        IsClone          : True
        DatabaseStatus   : 0
        LastBackupDate   : None
        LastBackupStatus : Not protected
        IsProtected      : False
```
**Get Backup available for ressource OM3 on hostname racnode3.demo.com :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./get-backup.py --url snapcenter.demo.com:8146 --resourcename OM3 --hostname racnode3.demo.com
Retrieving all backups on [snapcenter.demo.com:8146] for resource [OM3]...


        BackupName          : racnode3_demo_com_OM3_racnode3_02-28-2024_16.30.02.1136_0
        BackupId            : 32046
        BackupType          : Oracle Database Data Backup
        BackupTime          : 2024-02-28T16:31:49.719
        ProtectionGroupName : racnode3_demo_com_OM3
        PolicyName          : OrabackupOM2
        IsClone             : False
        With Secondary      : False
                Source              : svm-snapcenter:/om_data01


        BackupName          : racnode3_demo_com_OM3_racnode3_02-28-2024_16.30.02.1136_1
        BackupId            : 32048
        BackupType          : Oracle Database Log Backup
        BackupTime          : 2024-02-28T16:32:17.928
        ProtectionGroupName : racnode3_demo_com_OM3
        PolicyName          : OrabackupOM2
        IsClone             : False
        With Secondary      : False
                Source              : svm-snapcenter:/om_data01


        BackupName          : racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0
        BackupId            : 32156
        BackupType          : Oracle Database Data Backup
        BackupTime          : 2024-03-08T12:39:22.966
        ProtectionGroupName : racnode3_demo_com_OM3
        PolicyName          : OrabackupOM2
        IsClone             : False
        With Secondary      : False
                Source              : svm-snapcenter:/om_data01


        BackupName          : racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_1
        BackupId            : 32158
        BackupType          : Oracle Database Log Backup
        BackupTime          : 2024-03-08T12:39:50.381
        ProtectionGroupName : racnode3_demo_com_OM3
        PolicyName          : OrabackupOM2
        IsClone             : False
        With Secondary      : False
                Source              : svm-snapcenter:/om_data01


Total Backups = [4]
```

**Get Clone available for ressource OM3 on hostnane racnode3.demo.com :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./get-clones.py --url snapcenter.demo.com:8146 --resourceid racnode3.demo.com\\OM3
Retrieving all clones available on [snapcenter.demo.com:8146] for resource [racnode3.demo.com\OM3]...
Total number of clone present for resource [racnode3.demo.com\OM3] = [1]
        Clone attached to HostName   : racnode4.demo.com
        CloneLevel                   : 0
        CloneID                      : 80
        CloneName                    : racnode3_demo_com_OM3__clone__29108_03-08-2024_12.51.47
        Backupame                    : racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0
        Source DBsid                 : OM3
        Source SC Id                 : 1233
        Source dvVersion             : 19.0.0.0.0
        Source Type                  : Oracle Database
        is in ArchiveLog Mode        : True
        Dest DBsid                   : OM3cl1
        Dest SC Id                   : 1286
        PDBNames                     : [{'Value': 'PDB$SEED'}, {'Value': 'OM3PDB'}]
        SnapshotName                 : racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0
        ResourceName                 : svm-snapcenter:/om_data01
        VolumeName                   : om_data01
        AggregateName                : aggr1_grenada_04
        LogicalPath                  : 192.168.1.10:/Sc3c8dfa83-403b-466c-9a34-afd999630100

```

**Create a clone specification file for a PDB clone operation from a specified backupname :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./create-sco-clone-specfile.py --url snapcenter.demo.com:8146 --resourcename OM3 --hostname racnode3.demo.com --clonesid PDBcl1 --backupname racnode3_demo_com_OM3_racnode3_02-28-2024_13.06.41.5913_0 --pdbclone
```

**Create a PDB clone PDBcl1 from OM3PDB hosted by CDB OM3 from hostname racnode3.demo.com into CDB OM4 attached to hostname racnode4.demo.com:**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./create-sco-clone.py --url snapcenter.demo.com:8146 --clonetohost racnode4.demo.com --foreground --jsonfilepath ./pdbclone.json
Create SCO clone on [snapcenter.demo.com:8146] with specification file [C:\Program Files\NetApp\SnapCenter WebApp\App_Data\Oracle\clone_specs\oracle_clonespec_OM3_OM3cl1_2024-03-08_11.02.30.026.xml] ...

Clone Job Name [Clone from backup 'racnode3_demo_com_OM3_racnode3_02-28-2024_13.06.41.5913_0'] with Id [29100] created succesfully on SnapCenter server
Job still in progress, Wait...

Job Id [29100] is finished
Status [3]
Error : None
JobStatus [0]
```
ceci avec le fichier de config pdbclone.json suivant:

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# cat pdbclone.json
{
    "OracleSkipRecovery": false,
    "OracleUntilCancel": true,
    "ScriptTimeout": 60,
    "EnableEmail": false,
    "SkipNIDCreation": true,
    "SkipTempTablespaceTempFileCreation": false,
    "PDBName": "OM3PDB",
    "PDBCloneName": "PDBcl1",
    "CDBTargetSID": "OM4",
    "OpenPluggableDatabaseAfterClone": true
  }
```

<br>


``refresh-sco-clone.py`` is able to refresh a PDB or CDB existing clone.  
If the clone already exist, il will delete it.  
And based on the backupname parameter a new clone will be created:
* ``backupname`` = ```<existing backup name>``` : then a new clone will be create from this existing backupname
* ``backupname`` = ```Latest``` : then the latest available backup will be used to create a new clone
* ``backupname`` = ```ondemand``` : then a new on demand backup is executed and the resulting backupname is used to create the new clone

<br>

**Refresh a CDB clone of ressource OM3 from hostname racnode3.demo.com and attached to hostname racnode4.demo.com with a new ondemand backup :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./refresh-sco-clone.py --url snapcenter.demo.com:8146 --resourcename OM3 --hostname racnode3.demo.com --clonesid OM3cl1 --clonetohost racnode4.demo.com --SmPolicy OrabackupOM2 --backupname ondemand --jsonfilepath ./clone.json --foreground
Search existing clone [OM3cl1] for resource [OM3] on hostname [racnode4.demo.com] ...
Find clone [OM3cl1] with ID [79]
Delete clone id [79]
Delete Clone Job Name [Deleting clone 'racnode3_demo_com_OM3__clone__29104_03-08-2024_12.17.25'] with Id [29106] created succesfully on SnapCenter server
timeout is [False]
Job Id [29106] is finished
Status [3]
Error : None
JobStatus [0]
Create a new ondemand backup
Job Id [29107] is finished
Status [3]
Error [None]
JobStatus [0]
[Oracle Database Data Backup]
        BackupName [racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0]
        BackupId   [32156]
        BackupTime [2024-03-08T12:39:22.966]
Clone will be created with backupname [racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0]
[Oracle Database Log Backup]
        BackupName [racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_1]
        BackupId   [32158]
        BackupTime [2024-03-08T12:39:50.381]
Create SCO clone specification file on [snapcenter.demo.com:8146] for resource [OM3]...


Clone Specification File created succesfully on SnapCenter server at [C:\Program Files\NetApp\SnapCenter WebApp\App_Data\Oracle\clone_specs\oracle_clonespec_OM3_OM3cl1_2024-03-08_12.40.56.181.xml]
Set local dotenv variable SCO_CLONE_SPECFILE ['C:\\Program Files\\NetApp\\SnapCenter WebApp\\App_Data\\Oracle\\clone_specs\\oracle_clonespec_OM3_OM3cl1_2024-03-08_12.40.56.181.xml']
Clone Job Name [Clone from backup 'racnode3_demo_com_OM3_racnode3_03-08-2024_12.37.26.3624_0'] with Id [29108] created succesfully on SnapCenter server
Job Id [29108] is finished
Status [3]
Error : None
JobStatus [0]
```
ceci avec le fichier de config clone.json suivant:
```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# cat clone.json
{
    "OracleSkipRecovery": false,
    "OracleUntilCancel": true,
    "ScriptTimeout": 60,
    "EnableEmail": false,
    "SkipNIDCreation": false
  }
```

**Refresh PDB clone PDBcl1 from ressource (CDB) OM3 from hostname racnode3.demo.com attached to hostname racnode4.demo.com with existing backup :**

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# ./refresh-sco-clone.py --url snapcenter.demo.com:8146 --resourcename OM3 --hostname racnode3.demo.com --clonesid PDBcl1 --clonetohost racnode4.demo.com --SmPolicy OrabackupOM2 --backupname racnode3_demo_com_OM3_racnode3_02-27-2024_16.30.02.0333_0 --jsonfilepath ./pdbclone.json --foreground

Search existing clone [PDBcl1] for resource [OM3] on hostname [racnode4.demo.com] ...
Find clone [OM4:PDBcl1] with ID [68]
Delete clone id [68]
Delete Clone Job Name [Deleting clone 'racnode3_demo_com_OM3__clone__28946_02-27-2024_15.13.53'] with Id [28959] created succesfully on SnapCenter server 
Job still in progress, Wait...
timeout is [False]
Job Id [28959] is finished
Status [3]
Error : None
JobStatus [0]
Clone will be created with backupname [racnode3_demo_com_OM3_racnode3_02-27-2024_16.30.02.0333_0]
Create SCO clone specification file on [snapcenter.demo.com:8146] for resource [OM3]...

Clone Specification File created succesfully on SnapCenter server at [C:\Program Files\NetApp\SnapCenter WebApp\App_Data\Oracle\clone_specs\oracle_clonespec_OM3_PDBcl1_2024-02-28_12.10.41.147.xml]
Set local dotenv variable SCO_CLONE_SPECFILE ['C:\\Program Files\\NetApp\\SnapCenter WebApp\\App_Data\\Oracle\\clone_specs\\oracle_clonespec_OM3_PDBcl1_2024-02-28_12.10.41.147.xml']

Clone Job Name [Clone from backup 'racnode3_demo_com_OM3_racnode3_02-27-2024_16.30.02.0333_0'] with Id [28960] created succesfully on SnapCenter server 
Job Id [28960] is finished
Status [3]
Error : None
JobStatus [0]
```
ceci avec le fichier de config pdbclone.json suivant:

```
root@masson02-PC:/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/SCO-REST# cat pdbclone.json
{
    "OracleSkipRecovery": false,
    "OracleUntilCancel": true,
    "ScriptTimeout": 60,
    "EnableEmail": false,
    "SkipNIDCreation": true,
    "SkipTempTablespaceTempFileCreation": false,
    "PDBName": "OM3PDB",
    "PDBCloneName": "PDBcl1",
    "CDBTargetSID": "OM4",
    "OpenPluggableDatabaseAfterClone": true
  }
```
