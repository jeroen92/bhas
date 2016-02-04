from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.fields import *
import datetime, settings

class Prefix(BaseModel):
    subnet = CharField()
    mask = BigIntegerField()
    withdrawnAt = DateTimeField(null=True)
    prefix = CIDRField(default='255.255.255.255/32', index=True)

    class Meta:
        indexes = (
            (('subnet', 'mask'), True),
        )
