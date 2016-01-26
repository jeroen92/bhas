from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqlite_ext import MySQLDatabase

global DATABASE, VERSION, APPNAME_SHORT, INPUTFILE
DATABASE = SqliteExtDatabase('./db/bhas.db')
#DATABASE = MySQLDatabase("bhas", host="localhost", port=3306, user="root", passwd="monitoring")

VERSION = '0.1'
APPNAME_SHORT = 'bhas'
INPUTFILE = './input.csv'
