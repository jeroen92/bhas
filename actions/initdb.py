import settings
import csv
import json
import os, subprocess
import ipwhois
from classes.hijack import *
from classes.prefix import *
from classes.origin import *

def writeOrigin(origin_as, prefix):
    try:
        Origin.get(Origin.originAs == origin_as, Origin.prefix == prefix)
    except:
        target = Origin.create(prefix=prefix, originAs=origin_as)
        target.save()
 
def initDb():
    print 'Initializing database'
    print 'Creating tables\n'
    try:
        settings.DATABASE.create_tables([Prefix,Origin,Hijack], safe=True)
    except OperationalError as e:
        print 'An error occurred while creating the database tables.\nError message: {0}\n'.format(e)
        return 1
    with open(settings.INPUTFILE, 'rb') as inputprefix:
        reader = csv.reader(inputprefix)
        for row in reader:
            subnet = row[0].split('/')[0]
            mask = row[0].split('/')[1]
            try:
                target = Prefix.create(subnet=subnet, mask=mask)
                target.save()
            except IntegrityError as e:
                # string.ljust(x) appends x spaces to the right end of the string
                print 'Error for prefix {0}{1}'.format(row[0].ljust(49),e)
                pass
    for prefix in Prefix.select():
        prefixm = prefix.subnet+'/'+str(prefix.mask)
        url = "https://stat.ripe.net/data/whois/data.json?resource={0}".format(prefixm)
        system_out = subprocess.Popen(["/usr/bin/curl", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = system_out.communicate()
        dict = json.loads(stdout)
        found = False
        for list in dict['data']['irr_records']:
            for value in list:
                if value['key'] == "origin":
                    found = True
                    origin_as = value['value']
                    writeOrigin(origin_as, prefix)
        if not found:
            origin_as = ipwhois.IPWhois(prefix.subnet).lookup()['asn']
            writeOrigin(origin_as, prefix)
    return 0
