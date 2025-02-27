import logging
import os
import random
import re
import string
import traceback

import aiofiles
import aiohttp
import google.generativeai as genai
import pg8000
import requests
from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto

from .getuser import Extract
from .misc import Handler
from .prompt import intruction

chat_history = {}

class Api:
    def __init__(self, name: str, dev: str, apikey: str, db_url: str):
        self.name = name
        self.dev = dev
        self.apikey = apikey
        self.db_url = db_url  # User harus isi dengan URL PostgreSQL
        self.safety_rate = {key: "BLOCK_NONE" for key in ["HATE", "HARASSMENT", "SEX", "DANGER"]}

        # Parsing db_url menjadi host, user, password, dbname, port
        self.db_params = self.parse_db_url(db_url)

        # Koneksi ke PostgreSQL
        try:
            self.conn = pg8000.connect(**self.db_params)
            self.cursor = self.conn.cursor()

            # Buat tabel jika belum ada
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    role TEXT NOT NULL,
                    parts TEXT NOT NULL
                );
                """
            )
            self.conn.commit()
        except Exception as e:
            print(f"❌ Database connection error: {e}")

    def parse_db_url(self, db_url):
        """Mengubah DATABASE_URL menjadi format yang bisa diterima pg8000"""
        parsed = urlparse(db_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/")
        }

    def close_connection(self):
        """Tutup koneksi database saat bot mati"""
        if hasattr(self, "conn"):
            self.cursor.close()
            self.conn.close()

    def configure_model(self, mode):
        genai.configure(api_key=self.apikey)
        instruction = intruction[mode].format(name=self.name, dev=self.dev)
        return genai.GenerativeModel("models/gemini-1.5-flash", system_instruction=instruction)

    def _log(self, record):
        return logging.getLogger(record)

    def get_chat_history(self, chat_id):
        """Ambil history chat dari database"""
        try:
            self.cursor.execute(
                "SELECT role, parts FROM chat_history WHERE chat_id = ? ORDER BY id ASC;", (chat_id,)
            )
            return [{"role": row[0], "parts": row[1]} for row in self.cursor.fetchall()]
        except Exception as e:
            self._log(__name__).error(f"Error get_chat_history: {e}")
            return []

    def save_chat_history(self, chat_id, role, parts):
        """Simpan chat ke database"""
        try:
            self.cursor.execute(
                "INSERT INTO chat_history (chat_id, role, parts) VALUES (?, ?, ?);",
                (chat_id, role, parts),
            )
            self.conn.commit()
        except Exception as e:
            self._log(__name__).error(f"Error save_chat_history: {e}")

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
                self.cursor.execute(
                    """
                    DELETE FROM chat_history WHERE chat_id = ?
                    AND id NOT IN (SELECT id FROM chat_history WHERE chat_id = ? ORDER BY id DESC LIMIT 20);
                    """,
                    (message.chat.id, message.chat.id),
                )
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
