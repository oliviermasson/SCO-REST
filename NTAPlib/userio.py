import sys
import getopt
import os
import getpass
import random

single='1'
multi='any'


def validateoptions(sysargs,validoptions,**kwargs):
    returndict={}
    returndict['MODE']=None
    returndict['OPTS']={}
    passedargs=[]
    usage="ERROR: Unable to process arguments"
    for key in kwargs.keys():
        if key == 'usage':
            usage=kwargs[key]
        if key == 'knownmodes':
            if len(sysargs) > 0 and sys.argv[1] not in knownmodes:
                fail(usage)
            else:
                returndict['mode']=sysargs[1]

    if len(sysargs) == 1:
        message(usage)
        sys.exit(1)

    optionlist=[]
    if type(validoptions) is dict:
        for key in validoptions.keys():
            if validoptions[key] == 'bool':
                optionlist.append(key)
            else:
                optionlist.append(key + "=")
    else:
        for item in validoptions:
            optionlist.append(item + "=")
    try:
        options,args = getopt.getopt(sysargs[1:],'',optionlist)
    except getopt.GetoptError as e:
        message(usage)
        fail(str(e))
    except Exception as e:
        fail(usage)

    for item in options:
        returndict['OPTS'][str(item).strip('=')]=None

    for o, a in options:
        barearg=o
        if o.startswith('--'):
            barearg=o[2:]
        if type(validoptions) is dict:
            bareoption=set([barearg,barearg + "="]).intersection(validoptions.keys()).pop()
            if validoptions[bareoption] == 'str':
                truevalue=str(a)
            elif validoptions[bareoption] == 'int':
                truevalue=int(a)
            elif validoptions[bareoption] == 'bool':
                truevalue=True
            elif validoptions[bareoption] == 'duration':
                truevalue=duration2seconds(a)
                if not truevalue:
                    fail("Illegal value for --" + barearg)
        returndict['OPTS'][barearg]=truevalue
    
    if 'required' in kwargs.keys():
        for item in kwargs['required']:
            if type(item) is str:
                if item not in returndict['OPTS'].keys():
                    fail("--" + item + " is required")
            elif type(item) is list:
                if not set(item).intersection(set(returndict['OPTS'].keys())):
                    fail("One of the following arguments is required: --" + ' --'.join(item))

    if 'dependent' in kwargs.keys():
        for key in kwargs['dependent'].keys():
            if key in returndict['OPTS'].keys():
                for item in kwargs['dependent'][key]:
                    if type(item) is str:
                        if item not in returndict['OPTS'].keys():
                            fail("Argument --" + key + " requires the use of ---" + item)
                    elif type(item) is list:
                        if not set(item).intersection(set(returndict['OPTS'].keys())):
                            fail("Argument --" + key + " requires one of the following arguments: --" + ' --'.join(item))
    
    return(returndict)

def message(args,**kwargs):
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
    leader=''
    if 'service' in kwargs.keys():
        leader=leader + kwargs['service'] + ": "
    if type(args) is list:
        for line in args:
            sys.stdout.write(leader + line + "\n")
            sys.stdout.flush()
    else:
        sys.stdout.write(leader + str(args) + "\n")
        sys.stdout.flush()

def ERROR(args,**kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")

def fail(args,**kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")
    sys.exit(1)

def warn(args,**kwargs):
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
        else:
            linefeed()
    if type(args) is list:
        for line in args:
            sys.stdout.write("WARNING: " + line + "\n")
            sys.stdout.flush()
    else:
        sys.stdout.write("WARNING: " + args + "\n")
        sys.stdout.flush()

def justexit():
    sys.stdout.write("Exiting... \n")
    sys.exit(0)

def linefeed():
    sys.stdout.write("\n")
    sys.stdout.flush()

def duration2seconds(value):
    if not value[-1].isalpha:
        value=value + 'd'
    if value[-1] == 's':
        return(int(a[:-1]))
    elif value[-1] == 'm':
        return(int(a[:-1])*60)
    elif value[-1] == 'h':
        return(int(a[:-1])*60*60)
    elif value[-1] == 'd':
        return(int(value[:-1])*60*60*24)
    else:
        return(None)
