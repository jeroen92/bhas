import fileinput, json, sys, logging, datetime, multiprocessing, Queue, urllib, requests
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

        # CHECK IF UPDATE OR WITHDRAWAL
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
        prefix = Prefix.select().where((Prefix.subnet == event.subnet) & (Prefix.mask == event.mask)).first()
        if not prefix:
            checkLessSpecificHijack(event)
        else:
            query = prefix.origins.select().where(Origin.asPath >> None)
            if query.exists():
                origins = query.execute()
                for origin in origins:
                    origin.asPath = event.asPath
                    origin.originUpstreamAs = None
                    if len(origin.asPath.split(',')) > 1:
                        origin.originUpstreamAs = event.asPath.split(',')[-2]
                        upstreamGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(event.asPath.split(',')[-2]))
                        for location in json.loads(upstreamGeolocation.text)['data']['locations']:
                            if event.subnet + '/' + event.mask in location['prefixes']:
                                origin.originUpstreamAsCc = location['country']
                                break
                    origin.save()
            if checkEventOrigin(event, prefix) == 0:
                logging.info("ProcessEvents\t Event dismissed for monitored event. Check application for leaking events (i.e. events that are not explicitly discarded or else triggered for a hijack.")

def checkLessSpecificHijack(event):
    print 'do something'

# Hijack types:
# 1: prefix hijack
# 2: subnet hijack
# 3: AS hijack + prefix
# 4: AS hijack + subnet
# 5: Less specific prefix hijack
def reportHijack(event, prefix, hijackType, origin = None):
    Hijack.create(
        prefix = prefix,
        subnet = event.subnet,
        mask = event.mask,
        originAs = event.originAs,
        asPath = event.asPath,
        originUpstreamAs = event.asPath.split(',')[-2],
        hijackType = hijackType,
        createdAt = event.timestamp)
        # Get all origin ASses that are allowed to announce prefix
    origins = prefix.origins.iterator()
    originAs = ','.join([str(origin.originAs) for origin in origins])
    originUpstreamAs = ','.join([str(origin.originUpstreamAs) for origin in origins])
    if not originUpstreamAs: originUpstreamAs = '- (None, AS_PATH length is one)'
    if hijackType == 1:
        logging.warning("ProcessEvents\t Prefix hijack alert. Prefix: {0}/{1} is now being announced by AS {2} with upstream AS {3}. Should be announced by AS {4} with upstream AS {5}".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2], originAs, originUpstreamAs))
    elif hijackType == 2:
        logging.warning("ProcessEvents\t Subnet hijack alert. Subnet: {0}/{1} is now being announced by AS {2} with upstream AS {3}. Should be announced by AS {4} with upstream AS {5}".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2], originAs, originUpstreamAs))
    elif hijackType == 3:
        logging.warning("ProcessEvents\t AS & Prefix hijack alert. AS {2} and prefix: {0}/{1} are now being announced with upstream AS {3}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2]))
    elif hijackType == 4:
        logging.warning("ProcessEvents\t AS & Subnet hijack alert. AS {2} and subnet {0}/{1} are now being announced with upstream AS {3}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2]))
    elif hijackType == 5:
        logging.warning("ProcessEvents\t Less specific hijack alert. Prefix: {0}/{1} hides monitored prefix {6}/{7} by AS {2} with upstream AS {3}. The monitored prefix should be announced by {4}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2], originAs, originUpstreamAs, origin.subnet, origin.mask))
    return 2

# Before discarding, check if the related prefix is currently hijacked
def checkIfHijacked(event, prefix, origin):
    hijacks = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.withdrawnAt == None) & (Hijack.asPath == event.asPath))
    for hijack in hijacks:
        hijack.withdrawnAt = datetime.datetime.now

def checkUpstreamAs(event, prefix, origin):
    if origin.originUpstreamAs == event.asPath[-2]:
        checkIfHijacked(event, prefix, origin)
    else:
        upstreamGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(event.asPath.split(',')[-2]))
        for location in json.loads(upstreamGeolocation.text)['data']['locations']:
            if event.subnet + '/' + event.mask in location['prefixes']:
                event.originUpstreamAsCc = location['country']
        if event.originUpstreamAsCc == origin.originUpstreamAsCc:
            discardEvent(event)
        else:
            # TODO check less/more specific prefix and alert prefix/subnet hijack --> type 3/4
            reportHijack(event, prefix, origin)

# Compare the AS path in the event with the AS path saved in the database
def checkAsPath(event, prefix, origin):
    if origin.asPath == event.asPath:
        checkIfHijacked(event, prefix, origin)
    else:
        checkUpstreamAs(event, prefix, origin)

# Not necessary for the test, so not implemented
def checkRipestatOriginAs(event, prefix):
    logging.info("ProcessEvents\t CheckRipestatOriginAs is not implemented. Hijack will be reported.")
    # TODO check less/more specific prefix and alert prefix/subnet hijack --> type 1/2
    reportHijack(event, prefix, 1)

# If the origin AS in the event matches at least one (MOAS) AS in the database
# for that prefix, set originMatches to True and continue to check the AS path
# If not, check RIPEstat IRR for a registered AS change
def checkEventOrigin(event, prefix):
    originMatches = False
    for origin in prefix.origins.iterator():
        if origin.originAs == event.originAs:
            originMatches = True
            prefixOrigin = origin
    if originMatches:
        checkAsPath(event, prefix, origin)
    else:
        checkRipestatOriginAs(event, prefix)

def discardEvent(event):
    logging.info("ProcessEvents\t Dismissing update")
    del(event)
    return 1
