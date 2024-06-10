import os
import speech_recognition as sr
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from pydub import AudioSegment
from gtts import gTTS
import whisper
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

import g4f
from g4f.client import Client

API_KEY = os.getenv("API_KEY")
client = Client()


def ask_gpt(prompt: str) -> str:
    response = g4f.ChatCompletion.create(
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        provider=g4f.Provider.DeepInfra(),
        api_key=API_KEY,
        messages=[{"role": "user", "content": f"Ответь на этот вопрос на русском языке: {prompt}"}],
    )
    out = ""
    for el in response:
        out += el
    index_to_cut = out.find("<g4f")

    trimmed_string = out[:index_to_cut]
    return trimmed_string


r = sr.Recognizer()

# Load Whisper model
#model = whisper.load_model("base")


async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = await update.message.voice.get_file()
    file_path = 'voice_message.ogg'

    await voice.download_to_drive(file_path)

    try:
        audio = AudioSegment.from_file(file_path, format="ogg")
        audio.export("voice_message.wav", format="wav")

        # Use Whisper model for speech-to-text
        # result = model.transcribe("voice_message.wav", language="russian")
        # text = result["text"]

        # variant with google
        with sr.AudioFile('voice_message.wav') as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ru")

        await update.message.reply_text("Вы сказали: " + text)
        answer = ask_gpt(text)
        print(answer)

        # Convert GPT response to audio
        audio_response = gTTS(text=answer, lang="ru", slow=False)
        audio_response.save("response.mp3")
        with open("response.mp3", "rb") as audio_file:
            await context.bot.send_audio(chat_id=update.message.chat_id, audio=audio_file)

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists('voice_message.wav'):
            os.remove('voice_message.wav')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправьте мне голосовое сообщение, и я его распознаю и дам ответ.")


def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    application.add_handler(CommandHandler("start", start))
    application.run_polling()


if __name__ == '__main__':
    main()
