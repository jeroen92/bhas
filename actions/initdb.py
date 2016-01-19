import settings
import csv
from classes.hijack import *
from classes.prefix import *
from classes.origin import *

def initDb():
    print 'Initializing database'
    print 'Creating tables\n'
    try:
        settings.DATABASE.create_tables([Prefix,Origin,Hijack], safe=True)
    except peewee.OperationalError as e:
        print 'An error occurred while creating the database tables.\nError message: {0}\n'.format(e)
        return 1
    with open(settings.INPUTFILE, 'rb') as inputprefix:
        print inputprefix
        reader = csv.reader(inputprefix)
        for row in reader:
            subnet = row.split('/')[0]
            mask = row.split('/')[1]
            target = Prefix(subnet=subnet, mask=mask)
    return 0
