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
            logging.debug('Bootstrap\t Load json into dict: {0}'.format(announcement))
        except ValueError as e:
            logging.debug(e)
            continue

        # CHECK IF UPDATE OR WITHDRAWAL
        try:
            logging.debug('Bootstrap\t Stripping attributes from update message')
            announcementType = announcement['type']
            neighbor = announcement['neighbor']['ip']
            # Check for announce/withdraw
            if 'announce' in announcement['neighbor']['message'][announcementType]:
                updateType = 'announce'
                asPath = announcement['neighbor']['message']['update']['attribute']['as-path']
                neighbor = announcement['neighbor']['ip']
                timestamp = datetime.datetime.fromtimestamp(announcement['time']).strftime('%Y-%m-%d %H:%M:%S')
            elif 'withdraw' in announcement['neighbor']['message'][announcementType]:
                updateType = 'withdraw'

            # Check ipv4/ipv6
            if announcement['neighbor']['message'][announcementType][updateType].get('ipv4 unicast', None):
                ipVersion = 'ipv4 unicast'
            elif announcement['neighbor']['message'][announcementType][updateType].get('ipv6 unicast', None):
                ipVersion = 'ipv6 unicast'

            if updateType == 'announce':
                # TODO can have multiple keys -->announcements !
                prefix = announcement['neighbor']['message'][announcementType][updateType]['ipv4 unicast'][neighbor].keys()[0]
            elif updateType == 'withdraw':
                prefix = announcement['neighbor']['message'][announcementType][updateType]['ipv4 unicast'].keys()[0]
            subnet = prefix.split('/')[0]
            mask = prefix.split('/')[1]
            event = Event(
                subnet=subnet,
                mask=mask,
                asPath=asPath,
                neighbor=neighbor,
                med=None,
                announcementType = announcementType,
                updateType = updateType,
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
        logging.info('ProcessEvents\t Picked {0} event from queue: {1}'.format(event.updateType, str(event.__dict__)))
        prefix = Prefix.select().where((Prefix.subnet == event.subnet) & (Prefix.mask == event.mask)).first()
        if not prefix:
            checkLessSpecificHijack(event)
        else:
            if event.updateType == 'announce':
                checkAnnouncementEvent(event, prefix)
            if event.updateType == 'withdraw':
                checkWithdrawalEvent(event, prefix)

def checkWithdrawalEvent(event, prefix):
    checkIfHijacked(event, prefix)

def checkAnnouncementEvent(event, prefix):
    query = prefix.origins.select().where(Origin.asPath >> None)
    if query.exists():
        origins = query.execute()
        for origin in origins:
            if not origin.originAs == event.originAs:
                continue
            origin.asPath = event.asPath
            origin.originUpstreamAs = None
            if len(origin.asPath.split(',')) > 1:
                origin.originUpstreamAs = event.asPath.split(',')[-2]
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

def clearHijack(event, prefix):
    hijack.withdrawnAt = datatime.datetime.now
    hijack.save()

# Before discarding, check if the related prefix is currently hijacked
def checkIfHijacked(event, prefix, origin = None):
    if event.updateType == 'withdraw':
        # If hijack for prefix exists
        query = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.withdrawnAt == None))
        if query.exists():
            for hijack in query.execute():
                clearHijack(event, prefix)
        # If hijack for prefix does not exist
        else:
            # First check if hijack exists with same prefix, but has already been withdrawn
            # If so, we withdraw it again, and do not delete the whole prefix. Might be a delayed withdrawal.
            query = Hijack.select().where(Hijack.prefix == prefix)
            if query.exists():
                for hijack in query.execute():
                    clearHijack(event, prefix)
            # If no hijacks exists that only matches the event's prefix, it is a legitimate withdrawal of the original prefix
            else:
                prefix.withdrawnAt = datetime.datetime.now
                prefix.save()
    # If announcement, check if hijack exists
    elif event.updateType == 'announce':
        hijacks = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.withdrawnAt == None) & (Hijack.asPath == event.asPath)).execute()
        for hijack in hijacks:
            clearHijack(event, prefix)

def checkUpstreamAs(event, prefix, origin):
    if origin.originUpstreamAs == event.asPath[-2]:
        checkIfHijacked(event, prefix, origin)
    else:
        upstreamGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(event.asPath.split(',')[-2]))
        for location in json.loads(upstreamGeolocation.text)['data']['locations']:
            if location['country'] == origin.originAsCc:
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
