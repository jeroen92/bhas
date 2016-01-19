from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from classes.basemodel import *
import datetime, settings

class Prefix(BaseModel):
    subnet = CharField(unique=True, primary_key=True, index=True)
    mask = BigIntegerField()
