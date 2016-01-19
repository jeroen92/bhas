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
    except OperationalError as e:
        print 'An error occurred while creating the database tables.\nError message: {0}\n'.format(e)
        return 1
    with open(settings.INPUTFILE, 'rb') as inputprefix:
        reader = csv.reader(inputprefix)
        for row in reader:
            subnet = row[0].split('/')[0]
            mask = row[0].split('/')[1]
            try:
                target = Prefix.create(subnet=subnet, mask=mask)
                target.save()
            except IntegrityError as e:
                # string.ljust(x) appends x spaces to the right end of the string
                print 'Error for prefix {0}{1}'.format(row[0].ljust(49),e)
                pass
    return 0
