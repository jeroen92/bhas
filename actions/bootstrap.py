import fileinput, json, sys
from classes.hijack import *
from classes.origin import *
from classes.prefix import *

def bootstrap():
    while True:
        line = sys.stdin.readline()
        event = json.loads(line)
        try:
            prefix = event['neighbor']['message']['update']['announce']['ipv4 unicast'][event['neighbor']['ip']].keys()[0]
            prefix = Prefix.create(subnet=prefix.split('/')[0], mask=prefix.split('/')[1])
        except KeyError as e:
            print e
        except IntegrityError as e:
            print e
    f.close()
