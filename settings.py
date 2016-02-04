from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqlite_ext import MySQLDatabase
from playhouse.sqlite_ext import PostgresqlDatabase

global DATABASE, VERSION, APPNAME_SHORT, INPUTFILE
DATABASE = SqliteExtDatabase('./db/bhas.db')
#MYSQLDATABASE = MySQLDatabase("bhas", host="localhost", port=3306, user="root", passwd="monitoring")
#DATABASE = PostgresqlDatabase("bhas", host="localhost", port=5432, user="bhas", password='',fields={'cidr': 'cidr'})
PostgresqlDatabase.register_fields({'cidr': 'cidr'})

VERSION = '0.1'
APPNAME_SHORT = 'bhas'
INPUTFILE = './input.csv'
