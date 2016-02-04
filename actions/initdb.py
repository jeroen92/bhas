import settings
import csv
import json
import os, subprocess
import ipwhois, requests
from classes.hijack import *
from classes.prefix import *
from classes.origin import *
from netaddr import IPNetwork

def writeOrigin(origin_as, prefix):
    originAsCc='XYZ'
    asGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(origin_as))
    prefixNetwork = IPNetwork(prefix.subnet + '/' + str(prefix.mask))
    for location in json.loads(asGeolocation.text)['data']['locations']:
        for locationPrefix in location['prefixes']:
            if prefixNetwork in IPNetwork(locationPrefix):
                originAsCc = location['country']
                break
    # If no location was found, try current prefix geolocation
    if originAsCc == 'XYZ':
        print "Could not get location data from origin AS, now trying prefix geolocation"
        prefixGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(prefix.subnet + '/' + str(prefix.mask)))
        for location in json.loads(prefixGeolocation.text)['data']['locations']:
            for locationPrefix in location['prefixes']:
                if prefixNetwork in IPNetwork(locationPrefix):
                    originAsCc = location['country']
                    break
    try:
        Origin.get(Origin.originAs == origin_as, Origin.prefix == prefix)
    except:
        target = Origin.create(prefix=prefix, originAs=origin_as, originAsCc=originAsCc)
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
                target = Prefix.create(subnet=subnet, mask=mask, prefix=subnet + '/' + str(mask))
                target.save()
            except IntegrityError as e:
                # string.ljust(x) appends x spaces to the right end of the string
                print 'Error for prefix {0}{1}'.format(row[0].ljust(49),e)
                pass

    for prefix in Prefix.select():
        if prefix.origins.exists(): continue
        prefixm = prefix.subnet+'/'+str(prefix.mask)
        url = "https://stat.ripe.net/data/whois/data.json?resource={0}".format(prefixm)
        system_out = subprocess.Popen(["/usr/bin/curl", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = system_out.communicate()
        dict = json.loads(stdout)
        found = False
        if 'irr_records' in dict['data'].keys():
            for list in dict['data']['irr_records']:
                for value in list:
                    if value['key'] == "origin":
                        found = True
                        origin_as = value['value']
                        writeOrigin(origin_as, prefix)
        if not found:
            try:
                origin_as = ipwhois.IPWhois(prefix.subnet).lookup()['asn']
                writeOrigin(origin_as, prefix)
            except:
                prefix.delete()
    return 0
