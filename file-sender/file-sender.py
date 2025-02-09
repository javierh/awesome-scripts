import os
import re
import tempfile
import subprocess
import logging
import shutil

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

# Insert your Telegram bot token here
TOKEN = "YOUR_BOT_TOKEN"

async def start(update: Update, context: CallbackContext):
    """Handler for the /start command."""
    await update.message.reply_text(
        "Hello! Send me a YouTube link, and I'll send you the audio in MP3 format."
    )

async def process_video(update: Update, context: CallbackContext):
    """Handler for processing YouTube links, downloading, and converting to MP3."""
    text = update.message.text
    pattern = r'https?://(?:www\.)?youtu(?:be\.com|\.be)/[^\s]+'
    match = re.search(pattern, text)
    if not match:
        await update.message.reply_text("Please send a valid YouTube link.")
        return

    url = match.group(0)
    await update.message.reply_text("Downloading and converting the video, please wait...")

    temp_dir = tempfile.mkdtemp()

    try:
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        downloaded_files = [f for f in os.listdir(temp_dir) if not f.endswith('.info.json')]
        if not downloaded_files:
            await update.message.reply_text("Failed to download the video.")
            return

        video_filename = downloaded_files[0]
        video_filepath = os.path.join(temp_dir, video_filename)
        base_name = os.path.splitext(video_filename)[0]
        mp3_filename = f"{base_name}.mp3"
        mp3_filepath = os.path.join(temp_dir, mp3_filename)

        cmd = [
            'ffmpeg', '-y', '-i', video_filepath, '-vn',
            '-ar', '44100', '-ac', '2', '-b:a', '192k', mp3_filepath
        ]
        subprocess.run(cmd, check=True)

        with open(mp3_filepath, 'rb') as audio_file:
            await update.message.reply_audio(audio_file, title=base_name)

    except Exception as e:
        logging.exception("Error processing the video:")
        await update.message.reply_text("An error occurred while processing the video.")
    finally:
        shutil.rmtree(temp_dir)

def main():
    """Bot entry point."""
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))

    app.run_polling()

if __name__ == '__main__':
    main()
