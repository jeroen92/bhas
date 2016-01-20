import fileinput, json
from classes.hijack import *
from classes.origin import *
from classes.prefix import *

def bootstrap():
    for line in fileinput.input():
        event = json.loads(line)
        try:
            prefix = event['neighbor']['message']['update']['announce']['ipv4 unicast'][event['neighbor']['ip']].keys()[0]
            print prefix
            prefix = Prefix.create(subnet=prefix.split('/')[0], mask=prefix.split('/')[1])
        except KeyError as e:
            pass
        except IntegrityError as e:
            print e
