import fileinput, json, sys, logging
from classes.hijack import *
from classes.origin import *
from classes.prefix import *

def bootstrap():
    while True:
        line = sys.stdin.readline()
        logging.debug('Bootstrap\t Got new line from stdin, trying to parse JSON')
        try:
            event = json.loads(line)
        except ValueError:
            logging.debug(e)
        logging.debug('Bootstrap\t Load json into dict: {0}'.format(event))
        try:
            prefix = event['neighbor']['message']['update']['announce']['ipv4 unicast'][event['neighbor']['ip']].keys()[0]
            logging.debug('Bootstrap\t Stripping prefix from update message: {0}'.format(str(prefix)))
            prefix = Prefix.create(subnet=prefix.split('/')[0], mask=prefix.split('/')[1])
        except KeyError as e:
            logging.debug(e)
        except IntegrityError as e:
            logging.debug(e)
    f.close()
