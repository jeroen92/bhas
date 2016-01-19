from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
import datetime, settings

class Hijack(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    prefix = CharField()
    mask = BigIntegerField()
    originUpstreamAs = IntegerField()
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField()
