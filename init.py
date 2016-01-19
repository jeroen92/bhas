#!/usr/bin/env python

from actions.bootstrap import *
from actions.initdb import *
from classes.event import *
from classes.orm_event import *
import time, argparse

VERSION = '0.1'
APPNAME_SHORT = 'bhas'

USAGE = '{1}.py [-hi]\n\n\
BGP Hijack Alerting System, version {0} \
'.format(VERSION, APPNAME_SHORT)

parser = argparse.ArgumentParser(description=USAGE)
parser.add_argument('-i', '--initialize', action="store_true", help='Initialize the database')

args = parser.parse_args()
