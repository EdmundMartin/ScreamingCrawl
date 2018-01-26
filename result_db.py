from peewee import *
import time

db = SqliteDatabase('crawl-{}.db'.format(time.time()))


class ResultDB(Model):
    url = CharField(max_length=2000, unique=True)
    title = TextField(null=True)
    status_code = IntegerField(null=False)
    h1_1 = TextField(null=True)
    h1_2 = TextField(null=True)
    h2 = TextField(null=True)
    meta_description = TextField(null=True)
    word_count = IntegerField(null=True)

    class Meta:
        database = db