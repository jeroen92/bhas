#!/usr/bin/env python

import time, argparse, settings
from actions.bootstrap import *
from actions.dropdb import *
from actions.initdb import *

USAGE = '{1}.py [-dhi]\n\n\
BGP Hijack Alerting System, version {0} \
'.format(settings.VERSION, settings.APPNAME_SHORT)

parser = argparse.ArgumentParser(description=USAGE)
parser.add_argument('-d', '--dropdb', action="store_true", help='Drop the database tables and their contents')
parser.add_argument('-i', '--initialize', action="store_true", help='Initialize the database')
args = parser.parse_args()

if args.initialize:
    initDb()
elif args.dropdb:
    dropDb()
else:
    bootstrap()
