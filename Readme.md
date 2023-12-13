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
| **refresh-sco-clone.py** | Refresh an existing clone with new OnDemand backup or existing backup | 
| **delete-clone.py** | Delete an existing clone |
| **clone.json** | Example of JSON file for CDB clone creation |
| **pdbclone.json** | Example of JSON file for PDB clone creation |
| **refresh.json** | Example of JSON file for CDB clone refresh |
| **refreshpdb.json** | Example of JSON file for PDB clone refresh |

<br>
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
      "Passphrase": "p4ssw0rd",
      "Rolename": "string"
    }
  }
}'
```

And export this token as an environment variable named ``SCO_TOKEN``

Before creating a clone, you must create a clone specification file (stored on the snapcenter server).  
This clone specification file must then be used by the ``create-clone.py``  
To simplify the automation of this, the path on the snapcenter server to this clone specification file is passed from ``create-sco-clone-specfile.py`` to ``create-clone.py`` through a **.env variable** as ``SCO_CLONE_SPECFILE`` variable
