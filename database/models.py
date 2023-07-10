import datetime
import uuid
from peewee import *
from database.database_config import db


class BaseModel(Model):
    created_on = DateTimeField(default=datetime.datetime.now)
    updated_on = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)

    class Meta:
        database = db


class User(BaseModel):
    BOT_CHOICES = (
        ("TELEGRAM", "TELEGRAM"),
        ("WHATSAPP", "WHATSAPP"),
    )

    id = CharField(primary_key=True, default=uuid.uuid4, max_length=50)
    phone = CharField(max_length=15, null=True)
    telegram_id = CharField(max_length=50, unique=True, null=True)
    telegram_username = CharField(max_length=50, unique=True, null=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    # gender = CharField(max_length=10, choices=GENDER_CHOICES, default="NA")
    last_used = DateTimeField(null=True)
    platform = CharField(choices = BOT_CHOICES, default="TELEGRAM")

    class Meta:
        table_name = "user"


class Language(BaseModel):
    LANGUAGE_CODES = (
        ("eng", "english"),
        ("hin", "hindi"),
        ("kan", "kannada"),
        ("mar", "Marathi"),
        ("guj", "Gujarati"),
        ("tel", "Telugu"),
        ("ori", "Oriya/Odia"),
    )
    id = CharField(max_length=50, primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=512, null=False)
    code = CharField(max_length=10, unique=True, null=False, choices=LANGUAGE_CODES)

    class Meta:
        table_name = "language"


class Conversation(BaseModel):
    BOT_CHOICES = (
        ("WHATSAPP", "WHATSAPP"),
        ("TELEGRAM", "TELEGRAM"),
    )
    id = CharField(primary_key=True, default=uuid.uuid4, max_length=50)
    user = ForeignKeyField(User, backref="user")
    name = CharField(max_length=255, null=True)
    bot_type = CharField(max_length=10, choices=BOT_CHOICES, default="TELEGRAM")
    bot_reference = CharField(max_length=50, null=True)
    language = ForeignKeyField(Language, backref="language", null=True)

    class Meta:
        table_name = "conversation"


class Messages(BaseModel):
    id = CharField(primary_key=True, default=uuid.uuid4, max_length=50)
    conversation = ForeignKeyField(Conversation, backref="conversation")
    original_message = CharField()
    translated_message = CharField(null=True)
    message_input_time = DateTimeField(default=datetime.datetime.now)
    message_response = CharField(max_length=2048, null=True)
    message_translated_response = CharField(max_length=2048, null=True)
    message_response_time = DateTimeField(null=True)
    feedback = CharField(max_length=10, null=True)

    class Meta:
        table_name = "messages"


class MessageMediaFiles(BaseModel):
    MEDIA_TYPES = (
        ("audio_input", "audio_input"),
        ("audio_response", "audio_response"),
    )

    id = CharField(primary_key=True, default=uuid.uuid4, max_length=50)
    message = ForeignKeyField(Messages, backref="media_files")
    media_type = CharField(max_length=20, choices=MEDIA_TYPES)
    s3_key = CharField(max_length=255, null=False)

    class Meta:
        table_name = "media_files"
