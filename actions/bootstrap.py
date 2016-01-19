import fileinput
from classes.hijack import *
from classes.origin import *
from classes.prefix import *

def bootstrap():
    for line in fileinput.input():
        print line
