from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime

db = SqliteExtDatabase('./db/bhas.db')

class BaseModel(Model):
    class Meta:
        database = db

class Target(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    prefix = CharField()
    mask = BigIntegerField()
    originUpstreamAs = IntegerField()
    originUpstreamAsCc = CharField()
    asPath = CharField()
    updatedAt = DateTimeField()
