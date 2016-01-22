import fileinput, json, sys, logging, datetime, multiprocessing, Queue, urllib, requests
from classes.hijack import *
from classes.event import *
from classes.origin import *
from classes.prefix import *
from netaddr import IPNetwork

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
                for prefix in announcement['neighbor']['message'][announcementType][updateType][ipVersion][neighbor].keys():
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
            elif updateType == 'withdraw':
                for prefix in announcement['neighbor']['message'][announcementType][updateType][ipVersion].keys():
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
            logging.info('Bootstrap\t Parsing Event failed, errormsg: {0}'.format(e))
        except IntegrityError as e:
            logging.info('Bootstrap\t Parsing Event, database error, errormsg: {0}'.format(e))
    f.close()

def processEvents(eventQueue):
    while True:
        prefix = False
        event = eventQueue.get()
        logging.info('ProcessEvents\t Picked {0} event from queue: {1}'.format(event.updateType, str(event.subnet + '/' + str(event.mask))))
        logging.debug('ProcessEvents\t Picked {0} event from queue: {1}'.format(event.updateType, str(event.__dict__)))
        # Check if event prefix exactly matches a monitoring prefix
        if Prefix.select().where((Prefix.subnet == event.subnet) & (Prefix.mask == event.mask)).exists():
            prefix = Prefix.select().where((Prefix.subnet == event.subnet) & (Prefix.mask == event.mask)).first()
            event.prefixType = 'prefixmatch'

        # Event prefix is not a possible prefix hijack. Check if it is more specific or of it is a supernet
        # Note: If 145.0.0.0/8 and 145.0.100.0/24 are monitored, a malicious announcement of 145.0.0.0/16 can trigger
        # either a less or more specific hijack, depending on which record is first encountered.
        # This tool should not be used that way. Please only monitor the largest network only.
        if not prefix:
            eventCidrPrefix = event.subnet + '/' + str(event.mask)
            for monitoredPrefix in Prefix.select():
                monitoredCidrPrefix = monitoredPrefix.subnet + '/' + str(monitoredPrefix.mask)
                if IPNetwork(monitoredCidrPrefix) in IPNetwork(eventCidrPrefix):
                    event.prefixType = 'supernet'
                    prefix = monitoredPrefix
                    break
                elif IPNetwork(eventCidrPrefix) in IPNetwork(monitoredCidrPrefix):
                    event.prefixType = 'subnet'
                    prefix = monitoredPrefix
        logging.info('Bootstrap\t Event {2} with prefix {0} was tested as a {1}'.format(event.subnet + '/' + str(event.mask), str(event.prefixType), event.updateType))
        if not prefix:
            discardEvent(event)
        else:
            if event.updateType == 'announce':
                checkAnnouncementEvent(event, prefix)
            if event.updateType == 'withdraw':
                checkWithdrawalEvent(event, prefix)

# Test event if it is an withdrawal
def checkWithdrawalEvent(event, prefix):
    checkIfHijacked(event, prefix)

# Test event if it is an announcement
def checkAnnouncementEvent(event, prefix):
    query = prefix.origins.select().where(Origin.asPath >> None)
    if query.exists():
        origins = query.execute()
        for origin in origins:
            if origin.originAs == event.originAs:
                origin.asPath = event.asPath
                origin.originUpstreamAs = None
                if len(origin.asPath.split(',')) > 1:
                    origin.originUpstreamAs = event.asPath.split(',')[-2]
                origin.save()
    if checkEventOrigin(event, prefix) == 0:
        logging.info("ProcessEvents\t Event dismissed for monitored event. Check application for leaking events (i.e. events that are not explicitly discarded or else triggered for a hijack.")

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
        originUpstreamAs = event.asPath.split(',')[-2:][::-1][-1],
        hijackType = hijackType,
        createdAt = event.timestamp)
        # Get all origin ASses that are allowed to announce prefix
    origins = prefix.origins.iterator()
    originAs = ','.join([str(origin.originAs) for origin in origins])
    origins = prefix.origins.iterator()
    originUpstreamAs = ','.join([str(origin.originUpstreamAs) for origin in origins])
    logging.warning('originupstreamas: {0}'.format(originUpstreamAs))
    if not originUpstreamAs: originUpstreamAs = '- (None, AS_PATH length is one)'
    if hijackType == 1:
        logging.warning("ProcessEvents\t Prefix hijack alert. Prefix: {0}/{1} is now being announced by AS {2} with upstream AS {3}. Should be announced by AS {4} with upstream AS {5}".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2:][::-1][-1], originAs, originUpstreamAs))
    elif hijackType == 2:
        logging.warning("ProcessEvents\t Subnet hijack alert. Subnet: {0}/{1} is now being announced by AS {2} with upstream AS {3}. Should be announced by AS {4} with upstream AS {5}".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2:][::-1][-1], originAs, originUpstreamAs))
    elif hijackType == 3:
        logging.warning("ProcessEvents\t AS & Prefix hijack alert. AS {2} and prefix: {0}/{1} are now being announced with upstream AS {3}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2:][::-1][-1]))
    elif hijackType == 4:
        logging.warning("ProcessEvents\t AS & Subnet hijack alert. AS {2} and subnet {0}/{1} are now being announced with upstream AS {3}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2:][::-1][-1]))
    elif hijackType == 5:
        logging.warning("ProcessEvents\t Less specific hijack alert. Prefix: {0}/{1} hides monitored prefix {6}/{7} by AS {2} with upstream AS {3}. The monitored prefix should be announced by {4}.".format(event.subnet, event.mask, event.originAs, event.asPath.split(',')[-2:][::-1][-1], originAs, originUpstreamAs, prefix.subnet, str(prefix.mask)))
    return 2

def clearHijack(event, prefix, hijack):
    hijack.withdrawnAt = datetime.datetime.now()
    hijack.save()

# Before discarding, check if the related prefix is currently hijacked
def checkIfHijacked(event, prefix, origin = None):
    if event.updateType == 'withdraw':
        # If hijack for prefix exists
        query = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.withdrawnAt == None) & (Hijack.subnet == event.subnet) & (Hijack.mask == event.mask))
        if query.exists():
            for hijack in query.execute():
                logging.info('ProcessEvents\t Event {0} with prefix {1} was identified as the withdrawal of an existing hijack. Clear Hijack.'.format(event.updateType, str(event.subnet + '/' + str(event.mask))))
                clearHijack(event, prefix, hijack)
        # If hijack for prefix does not exist
        else:
            # First check if hijack exists with same prefix, but has already been withdrawn
            # If so, we withdraw it again, and do not delete the whole prefix. Might be a delayed withdrawal.
            query = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.subnet == event.subnet) & (Hijack.mask == event.mask))
            if query.exists():
                for hijack in query.execute():
                    logging.info('ProcessEvents\t Event {0} with prefix {1} was identified as not the first withdrawal of an existing hijack. Clear Hijack once more.'.format(event.updateType, str(event.subnet + '/' + str(event.mask))))
                    clearHijack(event, prefix, hijack)
            # If no hijacks exists that only matches the event's prefix, it is a legitimate withdrawal of the original prefix
            else:
                logging.info('ProcessEvents\t Event {0} with prefix {1} was identified as the withdrawal of a monitored prefix. Set prefix withdrawnAt.'.format(event.updateType, str(event.subnet + '/' + str(event.mask))))
                prefix.withdrawnAt = datetime.datetime.now()
                prefix.save()
    # If announcement, check if hijack exists
    elif event.updateType == 'announce':
        for origin in prefix.origins.iterator():
            if event.originAs == origin.originAs:
                hijacks = Hijack.select().where((Hijack.prefix == prefix) & (Hijack.withdrawnAt == None)).execute()
                for hijack in hijacks:
                    # TODO: re check what this is about...
                    # TODO: get all origin aspaths and check if this announcement matches one of them. If so, the hijack is over and hijacks regarding this prefix should be cleared from the database
                    if not hijack.hijackType == 5:
                        logging.info('ProcessEvents\t Event {0} with prefix {1} was identified as the withdrawal of an existing hijack. Clear Hijack.'.format(event.updateType, str(event.subnet + '/' + str(event.mask))))
                        clearHijack(event, prefix, hijack)

# Match origin upstream AS to event upstream AS. If no match, compare country code of event AS to country code of prefix origin AS
def checkUpstreamAs(event, prefix, origin):
    if origin.originUpstreamAs == event.asPath[-2]:
        logging.info('ProcessEvents\t Event {0} with prefix {1}, event upstream AS {2} was tested equal to origin upstream AS {3}.'.format(event.updateType, str(event.subnet + '/' + str(event.mask)), event.asPath[-2], origin.originUpstreamAs))
        checkIfHijacked(event, prefix, origin)
    else:
        logging.info('ProcessEvents\t Event {0} with prefix {1}, event upstream AS {2} was tested not equal to origin upstream AS {3}.'
            .format(event.updateType, str(event.subnet + '/' + str(event.mask)), event.asPath[-2], origin.originUpstreamAs))
        upstreamGeolocation = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource={0}".format(event.asPath.split(',')[-2:][::-1][-1]))
        for location in json.loads(upstreamGeolocation.text)['data']['locations']:
            if location['country'] == origin.originAsCc:
                logging.info('ProcessEvents\t Event {0} with prefix {1}, event upstream AS {2} CC {4} was tested equal to origin AS {3} CC {5}.'
                    .format(event.updateType, str(event.subnet + '/' + str(event.mask)), event.asPath[-2], origin.originUpstreamAs, location['country'], origin.originAsCc))
                discardEvent(event)
                return 1
        logging.info('ProcessEvents\t Event {0} with prefix {1}, announcing upstream AS {2} does not have an IRR matching CC for monitored AS {3} CC {4}.'
            .format(event.updateType,
                str(event.subnet + '/' + str(event.mask)),
                str(event.originAs),
                origin.originAs,
                origin.originAsCc))

        # If announced prefix is an exact match to the monitored prefix
        if event.prefixType == 'prefixmatch':
            reportHijack(event, prefix, 3, origin)
        # If not, check if a more specific is announced
        elif event.prefixType == 'subnet':
            reportHijack(event, prefix, 4, origin)
        elif event.prefixType == 'supernet':
            reportHijack(event, prefix, 5, origin)

# Compare the AS path in the event with the AS path saved in the database
def checkAsPath(event, prefix, origin):
    logging.info('origin is: {0}'.format(origin.__dict__))
    if origin.asPath == event.asPath:
        logging.info('ProcessEvents\t Event {0} with prefix {1}, event AS path of {2} was tested equal to origin AS path {3}.'.format(event.updateType, str(event.subnet + '/' + str(event.mask)), event.asPath, origin.asPath))
        checkIfHijacked(event, prefix, origin)
    else:
        logging.info('ProcessEvents\t Event {0} with prefix {1}, event AS path of {2} was tested not equal to origin AS path {3}.'
            .format(event.updateType,
                str(event.subnet + '/' + str(event.mask)),
                event.asPath,
                origin.asPath))
        checkUpstreamAs(event, prefix, origin)

# Not necessary for the test, so not implemented
def checkRipestatOriginAs(event, prefix):
    logging.info("ProcessEvents\t CheckRipestatOriginAs is not implemented. Hijack will be reported.")
    # If announced prefix is an exact match to the monitored prefix
    if event.prefixType == 'prefixmatch':
        reportHijack(event, prefix, 1)
    # If not, check if a more specific is announced
    elif event.prefixType == 'subnet':
        reportHijack(event, prefix, 2)
    elif event.prefixType == 'supernet':
        reportHijack(event, prefix, 5)

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
    	logging.warning("ERR: {0},\n{1}".format(prefixOrigin.__dict__, event.__dict__))
        checkAsPath(event, prefix, prefixOrigin)
    else:
        checkRipestatOriginAs(event, prefix)

def discardEvent(event):
    logging.info("ProcessEvents\t Dismissing update for prefix {0}".format(event.subnet + '/' + str(event.mask)))
    del(event)
    return 1
