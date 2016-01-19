from playhouse.sqlite_ext import SqliteExtDatabase

global DATABASE, VERSION, APPNAME_SHORT
DATABASE = SqliteExtDatabase('./db/bhas.db')
VERSION = '0.1'
APPNAME_SHORT = 'bhas'
