#!/usr/bin/env python3

import time
import os
import telegram
from telegram.constants import ParseMode
import threading
import asyncio
import re
import yt_dlp
from telegram.ext import Application, MessageHandler, filters

# --- CONFIGURATION ---
MONITOR_FOLDER_PATH = "/mnt/data/music"
TELEGRAM_BOT_TOKEN = "518820532:AAGdCnVv8HR8dapzjDLsivCtIJ3onXteq8g"
TELEGRAM_CHAT_ID = "135572121"
INTERVAL_SECONDS = 10
WAIT_SECONDS_FOR_SIZE_CHECK = 60
ALLOWED_EXTENSIONS = {".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a"}
YOUTUBE_DOWNLOAD_PATH = "/tmp"
# --- END CONFIGURATION ---

def is_audio_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

async def send_telegram_file(bot, chat_id, file_path):
    """Sends a file to a Telegram chat asynchronously."""
    try:
        with open(file_path, 'rb') as file:
            await bot.send_document(chat_id=chat_id, document=file)
        print(f"Fichero '{os.path.basename(file_path)}' enviado a chat ID: {chat_id}")
    except Exception as e:
        print(f"Error al enviar fichero '{os.path.basename(file_path)}' a chat ID: {chat_id}. Error: {e}")

def download_youtube_as_mp3(youtube_url):
    """Downloads a YouTube video as MP3 using yt-dlp and returns the path to the downloaded file."""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(YOUTUBE_DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            video_title = info_dict.get('title', None)
            if video_title:
                mp3_filename = f"{video_title}.mp3"
                mp3_filepath = os.path.join(YOUTUBE_DOWNLOAD_PATH, mp3_filename)

                if os.path.exists(mp3_filepath):
                    print(f"MP3 creado: {mp3_filepath}")
                    return mp3_filepath
                else:
                    print(f"Error: No se encontró el archivo MP3 después de la conversión: {mp3_filepath}")
                    return None
            else:
                print(f"Error: No se pudo obtener el título del video de YouTube para URL: {youtube_url}")
                return None
    except Exception as e:
        print(f"Error al descargar y convertir video de YouTube desde URL: {youtube_url}. Error: {e}")
        return None

async def telegram_message_handler(update, context):
    """Handles Telegram messages, looks for YouTube URLs, downloads them as MP3, and sends them back to the user."""
    message_text = update.message.text
    youtube_url_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+))', message_text)

    if youtube_url_match:
        youtube_url = youtube_url_match.group(1)
        user_chat_id = update.message.chat_id
        print(f"URL de YouTube detectada del usuario {user_chat_id}: {youtube_url}")

        mp3_filepath = download_youtube_as_mp3(youtube_url)
        if mp3_filepath:
            await send_telegram_file(context.bot, user_chat_id, mp3_filepath)
        else:
            await context.bot.send_message(chat_id=user_chat_id, text="Error al descargar y convertir el video de YouTube.")
    else:
        print(f"Mensaje recibido del usuario {update.message.chat_id}, pero no es una URL de YouTube.")

def main():
    """Main function to set up the bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    youtube_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_message_handler)
    app.add_handler(youtube_url_handler)

    print("Bot de Telegram inicializado y escuchando mensajes...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
