import fileinput, json, sys, logging, datetime, multiprocessing, Queue
from classes.hijack import *
from classes.event import *
from classes.origin import *
from classes.prefix import *

def bootstrap():
    logging.info('Bootstrap\t Create shared Queue and start subprocess')
    eventQueue = multiprocessing.Queue()
    eventProcessor = multiprocessing.Process(target=processEvents, args = (eventQueue,))
    eventProcessor.start()
    processStdin(eventQueue)
    eventProcessor.join()

def processStdin(eventQueue):
    while True:
        line = sys.stdin.readline()
        if line == '':
            continue
        logging.debug('Bootstrap\t Got new line from stdin, trying to parse JSON')
        try:
            announcement = json.loads(line)
        except ValueError:
            logging.debug(e)
        logging.debug('Bootstrap\t Load json into dict: {0}'.format(announcement))
        try:
            logging.debug('Bootstrap\t Stripping attributes from update message')
            announcementType = announcement['type']
            prefix = announcement['neighbor']['message'][announcementType]['announce']['ipv4 unicast'][announcement['neighbor']['ip']].keys()[0]
            subnet = prefix.split('/')[0]
            mask = prefix.split('/')[1]
            asPath = announcement['neighbor']['message']['update']['attribute']['as-path']
            neighbor = announcement['neighbor']['ip']
            timestamp = datetime.datetime.fromtimestamp(announcement['time']).strftime('%Y-%m-%d %H:%M:%S')
            event = Event(
                subnet=subnet,
                mask=mask,
                asPath=asPath,
                neighbor=neighbor,
                med=None,
                announcementType=announcementType,
                timestamp=timestamp
            )
            logging.debug('Bootstrap\t Parsed Event from update message: {0}'.format(str(event.__dict__)))
            eventQueue.put_nowait(event)
        except KeyError as e:
            logging.debug(e)
        except IntegrityError as e:
            logging.debug(e)
    f.close()

def processEvents(eventQueue):
    while True:
        event = eventQueue.get()
        logging.info('ProcessEvents\t Picked event from queue: {0}'.format(str(event.__dict__)))
        prefix = Prefix.select().where((Prefix.subnet == event.subnet) & (Prefix.mask == event.mask)).execute()
        if len(prefix) == 0:
            discardEvent(event)
        else:
            checkEventOrigin(event, prefix)

def checkEventOrigin(event, prefix):
    print event

def discardEvent(event):
    logging.info("ProcessEvents\t Dismissing update")
    del(event)
