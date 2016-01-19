from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.prefix import *
import datetime, settings

class Hijack(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    prefix = ForeignKeyField(Prefix, on_delete="CASCADE")
    subnet = CharField()
    mask = IntegerField()
    originAs = IntegerField()
    originUpstreamAs = IntegerField()
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField()
