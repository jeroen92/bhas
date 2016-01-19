from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.target import *
import datetime, settings

class Hijack(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    target = ForeignKeyField(Target, on_delete="CASCADE")
    prefix = CharField()
    mask = BigIntegerField()
    originUpstreamAs = IntegerField()
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField()
