import datetime
import io
import logging
import os
from pydub import AudioSegment
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatAction,
    InputFile,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)
from database.models import Conversation, Messages, User
from main_bot_logic import main_bot_logic
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1 as speech

import boto3

from utils import (
    get_message_id_from_feedback,
    store_message_media,
    update_feedback_by_message_id,
    insert_message,
    get_user,
    upload_to_s3,
)

load_dotenv()

# Initialize Google Translate client
translate_client = translate.Client()
# Initialize Text-to-Speech client
text_to_speech_client = texttospeech.TextToSpeechClient()
# Initialize Speech-to-Text client
speech_client = speech.SpeechClient()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    user = get_user(
        telegram_id=str(update.message.from_user.id),
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name,
        telegram_username=update.message.from_user.username,
    )

    welcome_message = (
        "Welcome to Agri.Chat!🌱🌶️\nHere you can ask questions about Chilli farming by typing (📝) or sending a voice message (🎙️). You can ask in both English and Hindi. "
        "\nHere are some examples: \n"
        "1. What is the ideal temperature for chilli plants?\n"
        "2. How often should I water my chilli plants?\n"
        "3. What kind of soil is best for chilli plants?\n"
        "\n"
        "Agri.Chat में आपका स्वागत है!🌱🌶️\nआप यहां मिर्च की खेती के बारे में प्रश्न पूछ सकते हैं, टाइप (📝) करके या एक वॉयस मैसेज (🎙️) भेजकर। आप अंग्रेजी और हिंदी दोनों में पूछ सकते हैं।"
        "\nयहां कुछ उदाहरण हैं: \n"
        "1. मिर्च के पौधों के लिए आदर्श तापमान क्या है?\n"
        "2. मैं अपने मिर्च के पौधों को कितनी बार पानी दूं?\n"
        "3. मिर्च के पौधों के लिए कौन सी मिट्टी सबसे अच्छी है?"
    )

    update.message.reply_text(welcome_message)


def synthesize_speech(input_text: str, input_language: str) -> str:
    synthesis_input = texttospeech.SynthesisInput(text=input_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="hi-IN" if input_language == "hi" else "en-IN",
        name="hi-IN-Neural2-A" if input_language == "hi" else "en-IN-Standard-D",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
    )

    try:
        response = text_to_speech_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open("response.ogg", "wb") as out:
            out.write(response.audio_content)
            logger.info("Successfully wrote voice response to file")

    except Exception as e:
        logger.error("Error while synthesizing speech: %s", str(e))

    return "response.ogg"


def process_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    user = get_user(
        telegram_id=str(update.message.from_user.id),
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name,
        telegram_username=update.message.from_user.username,
    )

    response, message_id = main_bot_logic(
        user.id, user_input, context.bot_data["qa"], context.bot_data["video_vectordb"]
    )
    print("Message_id", message_id)
    # context.user_data['message_id'] = message_id

    if response:
        feedback_keyboard = [
            [
                InlineKeyboardButton("👍", callback_data=f"good_{message_id}"),
                InlineKeyboardButton("👎", callback_data=f"bad_{message_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(feedback_keyboard)
        update.message.reply_text(response, reply_markup=reply_markup)
        response_audio_file = synthesize_speech(response, "en")

        # Write audio response to s3 bucket
        file_name_audio_repsonse = (
            f"{update.message.from_user.id}_audio_response_{message_id}"
        )
        target_response_folder_name = "AGRI_CHAT/audio_output"
        audio_response_s3_target = os.path.join(
            target_response_folder_name, file_name_audio_repsonse + ".ogg"
        )
        upload_to_s3(response_audio_file, audio_response_s3_target)
        if message_id:
            store_message_media(
                message_id=message_id,
                file_path=audio_response_s3_target,
                type="audio_response",
            )

        with open(response_audio_file, "rb") as audio_file:
            context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=InputFile(audio_file, filename="response.ogg"),
            )


def process_voice(update: Update, context: CallbackContext) -> None:
    # Download the audio file from Telegram

    user = get_user(
        telegram_id=str(update.message.from_user.id),
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name,
        telegram_username=update.message.from_user.username,
    )
    voice = context.bot.get_file(update.message.voice.file_id)
    voice_file = voice.download()

    target_folder_name = "AGRI_CHAT/audio_input"
    file_name = (
        f"{update.message.from_user.id}_audio_input_{update.message.voice.file_id}"
    )
    audio_s3_target = os.path.join(target_folder_name, file_name + ".ogg")
    upload_to_s3(voice_file, audio_s3_target)

    # # Load the OGA audio file
    # audio = AudioSegment.from_file(voice_file, format="ogg")

    # # Export the audio as WAV format
    # voice_file = audio.export(voice_file, format="wav")

    print("*** Audio file***", voice_file)
    audio = None
    with open(voice_file, "rb") as audio_data:
        audio_content = audio_data.read()
        audio = speech.RecognitionAudio(content=audio_content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000,
        language_code="en-IN",
    )

    response = speech_client.recognize(config=config, audio=audio)

    # Retrieve the transcriptions
    transcriptions = [result.alternatives[0].transcript for result in response.results]

    # Send the transcriptions as a reply
    transcriptions = "\n".join(transcriptions)

    result = translate_client.detect_language(transcriptions)
    # print(result, type(result))
    print(result)

    if result["confidence"] < 0.7:
        os.remove(voice_file)
        if result["language"] == "hi-Latn":
            update.message.reply_text(
                "क्षमा करे | में समझी नहीं | कृपया फिर से प्रयास करे ।"
            )
            return
        else:
            update.message.reply_text("Sorry! I couldn't understand. Please try again.")
            return

    original_message = transcriptions
    heard_message = f"""This is what I heard: {original_message}.\nLet me try to find an answer for you."""
    input_lang = "en"
    if result["language"] == "hi-Latn":
        translated = translate_client.translate(
            transcriptions, source_language="en", target_language="hi"
        )
        original_message = translated["translatedText"]
        heard_message = f"""मैंने ये समझा: {original_message} | \nकृपया मेरे उत्तर का प्रतीक्षा करें"
            """
        input_lang = "hi"

    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    translated_heard_message = heard_message

    update.message.reply_text(heard_message)
    heard_audio_file = synthesize_speech(translated_heard_message, input_lang)
    with open(heard_audio_file, "rb") as audio_file:
        context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=InputFile(audio_file, filename="response.ogg"),
        )

    response, message_id = main_bot_logic(
        user.id,
        original_message,
        context.bot_data["qa"],
        context.bot_data["video_vectordb"],
    )
    print("Message_id", message_id)
    if message_id:
        store_message_media(
            message_id=message_id, file_path=audio_s3_target, type="audio_input"
        )
    os.remove(voice_file)

    if response:
        feedback_keyboard = [
            [
                InlineKeyboardButton("👍", callback_data=f"good_{message_id}"),
                InlineKeyboardButton("👎", callback_data=f"bad_{message_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(feedback_keyboard)
        update.message.reply_text(response, reply_markup=reply_markup)
        response_audio_file = synthesize_speech(response, "en")

        # Write audio response to s3 bucket
        file_name_audio_repsonse = (
            f"{update.message.from_user.id}_audio_response_{message_id}"
        )
        target_response_folder_name = "AGRI_CHAT/audio_output"
        audio_response_s3_target = os.path.join(
            target_response_folder_name, file_name_audio_repsonse + ".ogg"
        )
        upload_to_s3(response_audio_file, audio_response_s3_target)
        if message_id:
            store_message_media(
                message_id=message_id,
                file_path=audio_response_s3_target,
                type="audio_response",
            )

        with open(response_audio_file, "rb") as audio_file:
            context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=InputFile(audio_file, filename="response.ogg"),
            )


def handle_feedback(update: Update, context: CallbackContext) -> None:
    # message_id = context.user_data['message_id']
    # message_id, feedback = get_message_id_from_feedback(update)
    query = update.callback_query
    query.answer()
    print("Feedback", query.data)
    feedback, message_id = get_message_id_from_feedback(str(query.data))
    print("Feedback received for :", message_id)

    update_feedback_by_message_id(message_id, feedback)
    if feedback == "good":
        logger.info("Received positive feedback")
    elif feedback == "bad":
        logger.info("Received negative feedback")
    thank_you_message = (
        "🙏 Thank you for your feedback! 😊"
        if feedback == "good"
        else "🙏 Sorry to hear that! We'll strive to improve. 😔"
    )
    result = translate_client.detect_language(query.message.text)
    feedback_language = result["language"]
    if feedback_language == "hi":
        translation = translate_client.translate(
            thank_you_message, target_language="hi"
        )
        thank_you_message = translation["translatedText"]
    context.bot.send_message(chat_id=update.effective_chat.id, text=thank_you_message)
    query.edit_message_text(
        text=f"{query.message.text}\n(You rated: {'👍' if feedback == 'good' else '👎'})"
    )


def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main(updater: Updater):
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, process_message))
    dp.add_handler(MessageHandler(Filters.voice, process_voice))
    dp.add_handler(CallbackQueryHandler(handle_feedback))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
