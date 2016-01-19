import settings
from classes.hijack import *
from classes.target import *

def initDb():
    print 'Initializing database'
    print 'Creating tables\n'
    try:
        settings.DATABASE.create_tables([Hijack,Target], safe=True)
    except Exception as e:
        print 'An error occured while creating the database tables.\nError message: {0}\n'.format(e)
        return 1
    return 0
