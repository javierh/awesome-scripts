import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pytube import YouTube
from moviepy.editor import *  # Para la conversión de video a audio
import os
import re

# --- TOKEN DEL BOT DE TELEGRAM ---
# Reemplaza 'YOUR_TELEGRAM_BOT_TOKEN' con el token que te proporciona BotFather
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
# --- FIN DEL TOKEN DEL BOT ---

def start(update, context):
    """Comando /start para iniciar el bot."""
    update.message.reply_text('¡Hola! Envíame un enlace de YouTube y lo convertiré a MP3.')

def help_command(update, context):
    """Comando /help para mostrar ayuda."""
    update.message.reply_text('Envíame un enlace de YouTube y lo descargaré, convertiré a MP3 y te lo enviaré. Acepto enlaces de youtube.com y youtu.be.')

def download_youtube_audio(update, context):
    """Descarga el video de YouTube, lo convierte a MP3 y lo envía al usuario."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Expresión regular para extraer la URL de YouTube, cubriendo ambos dominios
    url_pattern = re.compile(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+))')
    match = url_pattern.search(user_message)

    if match:
        youtube_url = match.group(1)
        try:
            yt = YouTube(youtube_url)
            update.message.reply_text(f'Descargando audio de: {yt.title}...')

            # Obtener el stream de audio de mayor calidad disponible en formato MP4 (o similar progresivo)
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            if audio_stream:
                video_filename = audio_stream.default_filename
                video_path = audio_stream.download(filename=video_filename) # Descarga el archivo con el nombre original

                # Convertir a MP3 usando MoviePy
                mp3_filename = os.path.splitext(video_filename)[0] + ".mp3" # Cambia la extensión a .mp3
                mp3_path = os.path.splitext(video_path)[0] + ".mp3" # Mismo path base pero con extensión .mp3
                try:
                    videoclip = VideoFileClip(video_path)
                    videoclip.audio.write_audiofile(mp3_path, codec='libmp3lame') # Especificamos codec para MP3
                    videoclip.close() # Cierra el clip de video para liberar recursos

                    # Enviar el archivo MP3 al usuario
                    with open(mp3_path, 'rb') as audio_file:
                        context.bot.send_audio(chat_id=chat_id, audio=audio_file, title=mp3_filename)

                    update.message.reply_text('¡Audio MP3 enviado! Limpiando archivos temporales...')

                    # Borrar archivos de video y audio
                    os.remove(video_path)
                    os.remove(mp3_path)
                    update.message.reply_text('Archivos temporales borrados.')

                except Exception as conversion_error:
                    update.message.reply_text(f'Error al convertir a MP3: {conversion_error}')
                    return # Importante salir si hay un error en la conversión para evitar borrar archivos no deseados

            else:
                update.message.reply_text('No se encontró un stream de audio adecuado para este video.')

        except Exception as download_error:
            update.message.reply_text(f'Error al descargar el video de YouTube: {download_error}')
    else:
        update.message.reply_text('Por favor, envíe un enlace de YouTube válido.')


def main():
    """Inicia el bot y lo mantiene en funcionamiento."""
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    # Comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Manejador de mensajes de texto (donde se espera la URL de YouTube)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_youtube_audio))

    # Iniciar el bot
    updater.start_polling()

    # Mantener el bot funcionando hasta que se detenga manualmente
    updater.idle()

if __name__ == '__main__':
    main()
