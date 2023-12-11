import requests
import urllib3
import os
import json
urllib3.disable_warnings()

headers = {'content-type': "application/json",
           'accept': "application/json"}

def execute(self,Token,**kwargs):
    headers['Token']='{}'.format(Token)
    if self.api != "/version":
        self.url="https://" + self.url + "/api/" + self.scVersion + self.api
    else:
        self.url="https://" + self.url + "/api" + self.api
    if self.restargs is not None:
        self.url=self.url + "?" + "&".join(self.restargs)
    if self.debug:
        print("REST CALL: " + self.reqtype.upper() + " " + self.url)
        print("REST JSON: " + str(self.json))
    if self.reqtype=="get":
        response=requests.get(self.url,headers=headers,verify=False)
    elif self.reqtype=="post":
        response=requests.post(self.url,json=self.json,verify=False,headers=headers)
    elif self.reqtype=="put":
        response=requests.put(self.url,json=self.json,verify=False,headers=headers)
    elif self.reqtype=="patch":
        response=requests.patch(self.url,headers=headers,verify=False)
    elif self.reqtype=="delete":
        response=requests.delete(self.url,headers=headers,verify=False)
    else:
        self.result=1
        self.reason="Unsupported request type \"{}\"".format(self.reqtype)
        return

    if response.status_code == 202:
        try:
            self.response=response.headers["JobURI"]
            self.result=0
        except:
            if self.restdebug:
                print("REST RESPONSE: OK")
                formatted=json.dumps(response.json(),indent=1).splitlines()
                for line in formatted:
                    print("REST RESPONSE: " + line)
            try:
                convert2dict=response.json()
                self.result=0
                self.response=convert2dict
            except Exception as e:
                self.result=1
                reason=e
        return    
    if response.ok:
        if self.restdebug:
            print("REST RESPONSE: OK")
            formatted=json.dumps(response.json(),indent=1).splitlines()
            for line in formatted:
                print("REST RESPONSE: " + line)
        try:
            convert2dict=response.json()
            self.result=0
            self.response=convert2dict
        except Exception as e:
            self.result=1
            reason=e
            return
    else:
        if self.restdebug:
            print("REST RESPONSE: ERROR")
            print("REST REASON: " + response.text)
            formatted=json.dumps(response.json(),indent=1).splitlines()
            for line in formatted:
                print("REST RESPONSE: " + line)
        self.result=response.status_code
        self.reason=response.reason
        self.response=response.text
        try:
            convert2dict=response.json()
            self.response=convert2dict
        except:
            pass
        return

class doREST():

    def __init__(self,url,reqtype,api,**kwargs):

        self.url=url
        self.reqtype=reqtype
        self.api=api
        self.restargs=None
        self.json=None
        self.result=None
        self.reason=None
        self.response=None
        self.stdout=[]
        self.stderr=[]
        self.debug=False
        self.restdebug=False
        Token=None

        if os.getenv("SCO_TOKEN") is not None:
            Token=os.getenv("SCO_TOKEN")
        else:
            self.result=1
            self.reason="SnapCenter Token not found. Please generate it and set it into SCO_TOKEN env variable before execuing this script"
            self.stdout=None
            self.stderr=None
            return

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
            
        if 'restdebug' in kwargs.keys():
            self.restdebug=kwargs['restdebug']

        if 'restargs' in kwargs.keys():
            if type(kwargs['restargs']) is list:
                self.restargs=kwargs['restargs']
            elif type(kwargs['restargs']) is str:
                self.restargs=[kwargs['restargs']]
            elif type(kwargs['restargs']) is tuple:
                self.restargs=[str(''.join(kwargs['restargs']))]

        if 'scVersion' in kwargs.keys():
            self.scVersion=kwargs['scVersion']

        if 'json' in kwargs.keys():
            self.json=kwargs['json']

        if Token is not None:
            execute(self,Token)
