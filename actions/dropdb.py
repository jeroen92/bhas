import settings
from classes.hijack import *
from classes.target import *

def dropDb():
    print 'Destroying database'
    print 'Dropping tables\n'
    try:
        settings.DATABASE.drop_tables([Hijack,Target], safe=True)
    except Exception as e:
        print 'An error occured while dropping the database tables.\nError message: {0}\n'.format(e)
        return 1
    print 'Successfull'
    return 0
