from peewee import Model, SqliteDatabase, AutoField, ForeignKeyField, TextField


db = SqliteDatabase('my.db')


class BaseModel(Model):
    class Meta:
        database = db


class Repository(BaseModel):
    repo_id = AutoField()
    url = TextField(unique=True)


class Commit(BaseModel):
    repo = ForeignKeyField(Repository)
    hash_ = TextField()
    branch = TextField()
    status = TextField()
