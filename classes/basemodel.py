import settings
from peewee import *

class BaseModel(Model):
    class Meta:
        database = settings.DATABASE

