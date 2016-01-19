from playhouse.sqlite_ext import SqliteExtDatabase

global DATABASE, VERSION, APPNAME_SHORT, INPUTFILE
DATABASE = SqliteExtDatabase('./db/bhas.db')
VERSION = '0.1'
APPNAME_SHORT = 'bhas'
INPUTFILE = './input.csv'
