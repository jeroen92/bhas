from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
from classes.prefix import *
import datetime, settings

class Origin(BaseModel):
    prefix = ForeignKeyField(Prefix, on_delete="CASCADE", related_name='origins')
    originAs = IntegerField()
    originAsCc = CharField(null=True)
    originUpstreamAs = IntegerField(null=True)
    asPath = CharField(null=True)
    createdAt = DateTimeField(default=datetime.datetime.now)
    withdrawedAt = DateTimeField(null=True)
