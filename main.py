from pydub import utils
from telegram.ext import Updater
from telegram_bot import main as telegram_main
from load_vectordb import create_vectordb
from dotenv import load_dotenv
import os
from database.database_config import db
from utils import get_pdf_list_from_directory


def setup_bot():
    load_dotenv()  # take environment variables from .env.
    pdf_directory = "./pdf"
    persist_directory = "./storage"
    list_of_pdfs = get_pdf_list_from_directory(pdf_directory)

    video_pdf_directory = "./pdf_videos"
    video_persist_directory = "./video_storage"
    list_of_video_pdfs = get_pdf_list_from_directory(video_pdf_directory)

    qa, video_vectordb = create_vectordb(
        list_of_pdfs, persist_directory, list_of_video_pdfs, video_persist_directory
    )
    updater = Updater(os.environ["TELEGRAM_BOT_TOKEN"], use_context=True)
    updater.dispatcher.bot_data["qa"] = qa
    updater.dispatcher.bot_data["video_vectordb"] = video_vectordb
    return updater


def main():
    db.connect()
    updater = setup_bot()
    telegram_main(updater)
    db.close()


if __name__ == "__main__":
    main()
