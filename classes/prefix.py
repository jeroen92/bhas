from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
import datetime, settings

class Prefix(BaseModel):
    subnet = CharField()
    mask = BigIntegerField()

    class Meta:
        indexes = (
            (('subnet', 'mask'), True),
        )
