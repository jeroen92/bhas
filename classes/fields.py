from peewee import *
class CIDRField(Field):
    db_field = 'cidr'
    def db_value(self, value):
        return str(value) # convert UUID to str

    def python_value(self, value):
        return str(value) # convert str to UUID
