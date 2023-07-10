import os
from database.models import Conversation, MessageMediaFiles, Messages, User
from peewee import DoesNotExist, Update
import glob
import datetime
import logging
import boto3

logger = logging.getLogger(__name__)


def get_user(
    telegram_id: str,
    first_name: str = "",
    last_name: str = "",
    telegram_username: str = "",
) -> User:
    try:
        person = User.get(User.telegram_id == telegram_id)
        person.last_used = datetime.datetime.now()
        person.save()
        logger.info(f"{person.first_name} is accessing the bot.")

    except DoesNotExist:
        person = User.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            telegram_username=telegram_username,
            last_used=datetime.datetime.now(),
        )
        logger.info(f"{person.first_name} created and is accessing the bot.")
    return person


def get_conversation_instance(
    user_id: str,
) -> Conversation:
    try:
        conversation = Conversation.get(Conversation.user_id == user_id)
    except DoesNotExist:
        conversation = Conversation.create(user_id=user_id)
        print("+++++ New conversation created++++++")
    return conversation


def insert_message(
    user_id: str,
    user_input: str,
    message_response: str,
    translated_message: str,
    message_translated_reponse: str,
) -> Messages:
    conversation = get_conversation_instance(user_id)

    print("Conversation already exists")
    # create new conversation if not already present
    # if not conversation:
    #     conversation = Conversation.create(user_id=user_id)
    #     print("+++++ New conversation created++++++")
    # print(message_translated_reponse)
    # print("+++++Response length++++++", len(message_response))
    message = Messages.create(
        conversation=conversation.id,
        original_message=user_input,
        translated_message=translated_message,
        message_response=message_response,
        message_translated_response=message_translated_reponse,
    )
    print("++++Message inserted+++++")
    return message


# Get list of pdfs within any given directory.
def get_pdf_list_from_directory(parent_dir: str) -> list:
    pdf_files = glob.glob(f"{parent_dir}/*.pdf")
    print("*****", pdf_files)
    return pdf_files


def get_chat_history(user_id):
    conversation = get_conversation_instance(user_id)

    messages = (
        Messages.select()
        .where(
            Messages.conversation_id == conversation.id, Messages.is_deleted == False
        )
        .order_by(Messages.created_on.desc())
        .limit(10)
    )
    history = []
    for message in reversed(messages):
        history.append((message.translated_message, message.message_response))

    print("********************** CHAT HISTORY **********************")
    print(history)
    print("********************** END **********************")
    return history


def get_message_id_from_feedback(message):
    print(message.split("_"))
    return message.split("_")


def update_feedback_by_message_id(message_id, feedback):
    try:
        message = Messages.get(id=message_id)
        message.feedback = feedback
        message.save()
    except DoesNotExist:
        print(f"Message with ID {message_id} not found")


def upload_to_s3(file, object_key):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        s3.upload_file(file, os.getenv("AWS_STORAGE_BUCKET_NAME"), object_key)

        logger.info(f"{object_key} stored successfully")
    except Exception as e:
        logger.info("*******S3 Exception*****")
        logger.info(e)
        logger.info("Failed to save file.")


def store_message_media(message_id, file_path, type):
    audio_input_ref = MessageMediaFiles.create(
        message=message_id, media_type=type, s3_key=file_path
    )
    logger.info("Stored message media reference")


class VideoMapUtil:
    video_map = {}
    video_map.update(
        {
            "./pdf_videos/Controlling_aphids_in_chilli.pdf": {
                "hindi": "https://youtu.be/CZY3tJGwKEY",
                "telugu": "https://www.youtube.com/watch?v=ss54_iQSkxU",
            },
            "./pdf_videos/Control_leaf_curl_in_chilli.pdf": {
                "hindi": "https://youtu.be/CZY3tJGwKEY",
                "telugu": "https://www.youtube.com/watch?v=ss54_iQSkxU",
            },
            "./pdf_videos/Control_weed_in_chilli_farms.pdf": {
                "hindi": "https://youtu.be/abOIywZjdMc",
                "telugu": "https://www.youtube.com/watch?v=J9-OpwXHPvA",
            },
            "./pdf_videos/Irrigation_in_chilli_field.pdf": {
                "hindi": "https://youtu.be/abOIywZjdMc",
                "telugu": "https://www.youtube.com/watch?v=J9-OpwXHPvA",
            },
            "./pdf_videos/Precautions_during_chilli_harvest.pdf": {
                "hindi": "https://youtu.be/yBs5PVUzr-M",
                "telugu": "https://www.youtube.com/watch?v=J5R8gx7gJzQ",
            },
            "./pdf_videos/Prevent_mirco_nutrient_efficiency_in_chilli.pdf": {
                "hindi": "https://youtu.be/RYveEkJJkQA",
                "telugu": "https://www.youtube.com/watch?v=h-KhLED9i5w",
            },
            "./pdf_videos/Prevention_of_soil_borne_diseases_in_chilli.pdf": {
                "hindi": None,
                "telugu": "https://www.youtube.com/watch?v=joM8Bqa4wsA",
            },
            "./pdf_videos/Raising_chilli_nursery_using_tray_methods.pdf": {
                "hindi": "https://youtu.be/XBH7hdpttbc",
                "telugu": "https://www.youtube.com/watch?v=IOUGcHvu9_4",
            },
            "./pdf_vidoes/Seed_treatment_in_chilli.pdf": {
                "hindi": "https://www.youtube.com/watch?v=PT8NG-MB9po",
                "telugu": "https://www.youtube.com/watch?v=4wwKCgzXfDg",
            },
        }
    )
