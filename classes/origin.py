from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.prefix import *
import datetime, settings

class Origin(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    prefix = ForeignKeyField(Prefix, on_delete="CASCADE")
    originAs = IntegerField()
    originUpstreamAsCc = CharField()
    originUpstreamAs = IntegerField()
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField()
