from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.prefix import *
import datetime, settings

class Hijack(BaseModel):
    prefix = ForeignKeyField(Prefix, on_delete="CASCADE", related_name='hijacks')
    subnet = CharField()
    mask = IntegerField()
    originAs = IntegerField()
    originUpstreamAs = IntegerField()
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField()
