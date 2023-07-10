# auto-generated snapshot
from peewee import *
import datetime
import peewee
import uuid


snapshot = Snapshot()


@snapshot.append
class User(peewee.Model):
    id = CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
    phone = CharField(max_length=15, null=True)
    telegram_id = CharField(max_length=50, null=True, unique=True)
    telegram_username = CharField(max_length=50, null=True, unique=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    last_used = DateTimeField(null=True)
    platform = CharField(default='TELEGRAM', max_length=255)
    class Meta:
        table_name = "user"


@snapshot.append
class Language(peewee.Model):
    id = CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
    name = CharField(max_length=512)
    code = CharField(max_length=10, unique=True)
    class Meta:
        table_name = "language"


@snapshot.append
class Conversation(peewee.Model):
    id = CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
    user = snapshot.ForeignKeyField(backref='user', index=True, model='user')
    name = CharField(max_length=255, null=True)
    bot_type = CharField(default='TELEGRAM', max_length=10)
    bot_reference = CharField(max_length=50, null=True)
    language = snapshot.ForeignKeyField(backref='language', index=True, model='language', null=True)
    class Meta:
        table_name = "conversation"


@snapshot.append
class Messages(peewee.Model):
    id = CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
    conversation = snapshot.ForeignKeyField(backref='conversation', index=True, model='conversation')
    original_message = CharField(max_length=255)
    translated_message = CharField(max_length=255, null=True)
    message_input_time = DateTimeField(default=datetime.datetime.now)
    message_response = CharField(max_length=2048, null=True)
    message_translated_response = CharField(max_length=2048, null=True)
    message_response_time = DateTimeField(null=True)
    feedback = CharField(max_length=10, null=True)
    class Meta:
        table_name = "messages"


@snapshot.append
class MessageMediaFiles(peewee.Model):
    id = CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)
    message = snapshot.ForeignKeyField(backref='media_files', index=True, model='messages')
    media_type = CharField(max_length=20)
    s3_key = CharField(max_length=255)
    class Meta:
        table_name = "media_files"


def forward(old_orm, new_orm):
    user = new_orm['user']
    return [
        # Apply default value 'TELEGRAM' to the field user.platform,
        user.update({user.platform: 'TELEGRAM'}).where(user.platform.is_null(True)),
    ]


def backward(old_orm, new_orm):
    user = new_orm['user']
    return [
        # Apply default value 'NA' to the field user.gender,
        user.update({user.gender: 'NA'}).where(user.gender.is_null(True)),
    ]
