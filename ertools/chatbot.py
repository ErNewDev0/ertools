import logging
import os
import random
import re
import string
import traceback

import aiofiles
import psycopg2
import aiohttp
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto

from .getuser import Extract
from .misc import Handler, save_chat_history, get_chat_history
from .prompt import intruction

chat_history = {}



class Api:
    def __init__(self, name: str, dev: str, apikey: str, db_url: str):
        self.name = name
        self.dev = dev
        self.apikey = apikey
        self.db_url = db_url  # User harus isi ini dengan URL PostgreSQL

        # Koneksi ke PostgreSQL
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()

        # Buat tabel jika belum ada
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id BIGINT,
            role TEXT,
            parts TEXT
        );
        """)
        self.conn.commit()
        self.safety_rate = {key: "BLOCK_NONE" for key in ["HATE", "HARASSMENT", "SEX", "DANGER"]}

    def configure_model(self, mode):
        genai.configure(api_key=self.apikey)
        instruction = intruction[mode].format(name=self.name, dev=self.dev)
        return genai.GenerativeModel("models/gemini-1.5-flash", system_instruction=instruction)

    def _log(self, record):
        return logging.getLogger(record)

    def KhodamCheck(self, input):
        try:
            model = self.configure_model("khodam")
            response = model.generate_content(input)
            return response.text.strip()
        except Exception as e:
            self._log(__name__).error(f"KhodamCheck error: {str(e)}")
            return f"Terjadi kesalahan: {str(e)}"

    def chatbotnya(self, message):
        try:
            mention = Extract().getMention(message.from_user)
            url_pattern = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+")
            urls = url_pattern.findall(message.text)
    
            if urls:
                url = urls[0]
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    return f"URL tidak dapat diakses ({response.status_code})."
    
                soup = BeautifulSoup(response.content, "html.parser")
                title = soup.title.string if soup.title else "Tidak ada judul"
                meta_description = soup.find("meta", attrs={"name": "description"})
                description = meta_description["content"] if meta_description else "Tidak ada deskripsi"
    
                return (
                    f"URL yang dikirim oleh {mention}:\n"
                    f"**Judul**: {title}\n"
                    f"**Deskripsi**: {description}\n"
                    f"**Link**: {url}"
                )
    
            text = Handler().getMsg(message, is_chatbot=True)
            msg = f"Halo gue {mention}:\n{text}"
    
            model = self.configure_model("chatbot")
            history = self.get_chat_history(message.chat.id)  # Ambil history dari PostgreSQL
    
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message({"role": "user", "parts": msg}, safety_settings=self.safety_rate)
    
            if response and response.text:
                self.save_chat_history(message.chat.id, "user", msg)
                self.save_chat_history(message.chat.id, "model", response.text)
    
                # Hapus history lama jika lebih dari 20 pesan
                self.cursor.execute("""
                    DELETE FROM chat_history WHERE chat_id = %s
                    AND id NOT IN (SELECT id FROM chat_history WHERE chat_id = %s ORDER BY id DESC LIMIT 20);
                """, (message.chat.id, message.chat.id))
                self.conn.commit()
    
                return response.text
            else:
                return "Maaf, aku tidak bisa menjawab saat ini."
        except Exception:
            error_detail = traceback.format_exc()
            self._log(__name__).error(f"ChatBot error:\n{error_detail}")
            return f"Terjadi kesalahan:\n{error_detail}"

    def clear_chat_history(self, message):
        if chat_history.pop(message.from_user.id, None):
            mention = Extract().getMention(message.from_user)
            return f"Riwayat obrolan untuk {mention} telah dihapus."
        return "Maaf, kamu siapa"


class ImageGen:
    def __init__(self, url: str = "https://mirai-api.netlify.app/api/image-generator/bing-ai"):
        self.url = url

    def _log(self, record):
        return logging.getLogger(record)

    async def generate_image(self, prompt: str, caption: str = None):
        payload = {"prompt": prompt}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Error: Request failed with status {response.status}")

                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    raise Exception(f"Error: Failed to decode JSON response. Raw response: {await response.text()}")

                if "url" in data:
                    imageList = []
                    for num, image_url in enumerate(data["url"], 1):
                        random_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
                        filename = f"{random_name}_{num}.jpg"
                        async with session.get(image_url) as image_response:
                            if image_response.status != 200:
                                raise Exception(f"Error: Failed to download image with status {image_response.status}")

                            async with aiofiles.open(filename, "wb") as file:
                                content = await image_response.read()
                                await file.write(content)

                        if num == 1 and caption:
                            imageList.append(InputMediaPhoto(filename, caption=caption))
                        else:
                            imageList.append(InputMediaPhoto(filename))
                        self._log(filename).info("Successfully saved")

                    if imageList:
                        return imageList
                    else:
                        raise Exception("Error: No images generated")
                else:
                    raise Exception(f"Error: Invalid response format. Data: {data}")

    def _remove_file(self, images: list):
        for media in images:
            filename = media.media
            if os.path.exists(filename):
                os.remove(filename)
                self._log(filename).info("Successfully removed")
