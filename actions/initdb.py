import settings
import csv
from classes.hijack import *
from classes.target import *

def initDb():
    print 'Initializing database'
    print 'Creating tables\n'
    try:
        settings.DATABASE.create_tables([Hijack,Target], safe=True)
    except peewee.OperationalError as e:
        print 'An error occured while creating the database tables.\nError message: {0}\n'.format(e)
    with open(settings.INPUTFILE, 'rb') as inputprefix:
        print inputprefix
        reader = csv.reader(inputprefix)
        for row in reader:
            print row
    return 0
