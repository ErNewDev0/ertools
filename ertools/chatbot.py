import base64
import logging
import os
import random
import string

import aiofiles
import aiohttp
import google.generativeai as genai
from pyrogram.types import InputMediaPhoto

from ertools.encrypt import BinaryEncryptor

code = BinaryEncryptor()

instruction = {
    "chatbot": code.decrypt(
        "0100000101101110011001000110000100100000011000010110010001100001011011000110000101101000001000000111001101100101011011110111001001100001011011100110011100100000011000010111001101101001011100110111010001100101011011100010000001000001010010010010000001100010011001010111001001101110011000010110110101100001001000000111101101101110011000010110110101100101011111010010110000100000011110010110000101101110011001110010000001100100011010010110101101100101011011010110001001100001011011100110011101101011011000010110111000100000011011110110110001100101011010000010000001111011011001000110010101110110011111010010111000100000010000010110111001100100011000010010000001101101011001010110110101101001011011000110100101101011011010010010000001100111011000010111100101100001001000000110101101101111011011010111010101101110011010010110101101100001011100110110100100100000011110010110000101101110011001110010000001110011011010010110111001100111011010110110000101110100001000000110010001100001011011100010000001101010011001010110110001100001011100110010110000100000011100110110010101110010011101000110000100100000011100110111010101101011011000010010000001101101011001010110111001100111011001110110111101100100011000010010000001110000011001010110111001100111011001110111010101101110011000010010000001101100011000010110100101101110001000000110010001100101011011100110011101100001011011100010000001101000011101010110110101101111011100100010000001100100011000010110111000100000011010110110010101100011011001010111001001100100011000010111001101100001011011100010111000100000010000010110111001100100011000010010000001100010011001010111001001101010011001010110111001101001011100110010000001101011011001010110110001100001011011010110100101101110001000000111000001100101011100100110010101101101011100000111010101100001011011100010111000100000010101000111010101100111011000010111001100100000010000010110111001100100011000010010000001100001011001000110000101101100011000010110100000100000011011010110010101101101011000100110010101110010011010010110101101100001011011100010000001101001011011100110011001101111011100100110110101100001011100110110100100100000011110010110000101101110011001110010000001100001011010110111010101110010011000010111010000100000011001000110000101101110001000000111001001100101011011000110010101110110011000010110111000100000011100110110000101101101011000100110100101101100001000000111010001100101011101000110000101110000001000000110110101100101011011010111000001100101011100100111010001100001011010000110000101101110011010110110000101101110001000000110111001110101011000010110111001110011011000010010000001101101011001010110111001100111011001110110111101100100011000010010000001100100011000010110110001100001011011010010000001101001011011100111010001100101011100100110000101101011011100110110100100100000010000010110111001100100011000010010111000100000010100000110000101110011011101000110100101101011011000010110111000100000011101010110111001110100011101010110101100100000011100110110010101101100011000010110110001110101001000000110110101100101011011010110001001100101011100100110100101101011011000010110111000100000011010100110000101110111011000010110001001100001011011100010000001111001011000010110111001100111001000000111010001101111001000000111010001101000011001010010000001110000011011110110100101101110011101000010110000100000011101000110010101110100011000010111000001101001001000000110010001100101011011100110011101100001011011100010000001110011011001010110111001110100011101010110100001100001011011100010000001101000011101010110110101101111011100100010000001111001011000010110111001100111001000000110110101100101011011010110001001110101011000010111010000100000011100000110010101110010011000110110000101101011011000010111000001100001011011100010000001101100011001010110001001101001011010000010000001101101011001010110111001111001011001010110111001100001011011100110011101101011011000010110111000101110001000000100001101101111011011100111010001101111011010000010000001101001011011100111010001100101011100100110000101101011011100110110100100111010001000000000101000001010010100000110010101101110011001110110011101110101011011100110000100111010001000000100000101110000011000010010000001100011011101010110000101100011011000010010000001101000011000010111001001101001001000000110100101101110011010010011111100001010010000010110111001100100011000010011101000100000010000110111010101100001011000110110000100100000011010000110000101110010011010010010000001101001011011100110100100111111001000000100001101110101011010110111010101110000001000000110001101100101011100100110000101101000001011000010000001110100011000010111000001101001001000000110101001100001011011100110011101100001011011100010000001110100011001010111001001101100011000010110110001110101001000000110001001100101011100100111001101100101011011010110000101101110011001110110000101110100001011000010000001101000011101010110101001100001011011100010000001100010011010010111001101100001001000000111001101100001011010100110000100100000011001000110000101110100011000010110111001100111001000000111001101100101011100000110010101110010011101000110100100100000011011010110000101101110011101000110000101101110001000000111100101100001011011100110011100100000011101000110100101100100011000010110101100100000011001000110100101110101011011100110010001100001011011100110011100100001001000000000101000001010010100000110010101101110011001110110011101110101011011100110000100111010001000000101001101101001011000010111000001100001001000000111100101100001011011100110011100100000011010110110000101101101011101010010000001110011011101010110101101100001001111110000101001000001011011100110010001100001001110100010000001001000011011010110110100101100001000000111001101100001011110010110000100100000011011000110010101100010011010010110100000100000011100110111010101101011011000010010000001100100011000010111010001100001001000000110010001100001011011100010000001100001011011000110011101101111011100100110100101110100011011010110000100101100001000000110110101100101011100100110010101101011011000010010000001110100011010010110010001100001011010110010000001110000011001010111001001101110011000010110100000100000011011010110010101101110011001110110010101100011011001010111011101100001011010110110000101101110001000010010000000001010000010100100100101101110011001110110000101110100001011000010000001110011011001010110110001100001011011000111010100100000011000100110010101110010011010010110101101100001011011100010000001101010011000010111011101100001011000100110000101101110001000000111100101100001011011100110011100100000011010010110111001100110011011110111001001101101011000010111010001101001011001100010000001110100011001010111010001100001011100000110100100100000011101000110010101110100011000010111000000100000011011010110010101101110011001110111010101101110011001000110000101101110011001110010000001110100011000010111011101100001001000000110010001100001011011100010000001101011011001010110001101100101011100100110100101100001011000010110111000101110"
    ),
    "khodam": base64.b64decode(
        b"QW5kYSBhZGFsYWggc2VvcmFuZyBwYXJhbm9ybWFsIGJlcm5hbWEge25hbWV9IHlhbmcgbWVtaWxpa2kga2VtYW1wdWFuIHVudHVrIG1lbmRlc2tyaXBzaWthbiBraG9kYW0gc2VzZW9yYW5nIGRhbGFtIGJlbnR1ayBiaW5hdGFuZy4gVHVnYXMgQW5kYSBhZGFsYWggbWVtYmVyaWthbiBkZXNrcmlwc2kgc2luZ2thdCB0ZW50YW5nIGtob2RhbSB0ZXJzZWJ1dC4gU2V0aWFwIGlucHV0IHlhbmcgZGliZXJpa2FuIGFrYW4gZGlhbmdnYXAgc2ViYWdhaSBuYW1hIHNlc2VvcmFuZywgZGFuIEFuZGEgYWthbiBtZW5kZXNrcmlwc2lrYW4ga2hvZGFtbnlhIHNlY2FyYSBzaW5na2F0LiBEZXNrcmlwc2kgYmlzYSBiZXJzaWZhdCBwb3NpdGlmIG1hdXB1biBuZWdhdGlmLCB0ZXJnYW50dW5nIHBhZGEgYXBhIHlhbmcgQW5kYSByYXNha2FuLiBJbmkgdGlkYWsgbWVuamFkaSBtYXNhbGFoIGthcmVuYSB0dWp1YW5ueWEgYWRhbGFoIHVudHVrIGhpYnVyYW4uIEJlYmFza2FuIGRpcmltdSB1bnR1ayBtZW5qYWRpIHNlb3JhbmcgcGFyYW5vcm1hbCBzZXBlcnRpIGJpYXNhbnlhLiBQYXN0aWthbiBkZXNrcmlwc2kga2hvZGFtIHRpZGFrIG1lbGViaWhpIDIwMDAga2FyYWt0ZXIsIG1lbmdndW5ha2FuIGJhaGFzYSBJbmRvbmVzaWEsIGRhbiBkaXNhamlrYW4gZGFsYW0gYmVudHVrIHRla3Mgc2VkZXJoYW5hLiBBbmRhIGp1Z2EgYmlzYSBtZW55ZWJ1dGthbiBndXJ1IHNwaXJpdHVhbCBBbmRhLCB7ZGV2fSBqaWthIGRpcGVybHVrYW4u"
    ).decode(),
}


class Api:
    def __init__(self, name="Who?er", dev="@Chakszzz", apikey="AIzaSyA99Kj3x3lhYCg9y_hAB8LLisoa9Im4PnY", is_khodam=False):
        genai.configure(api_key=apikey)
        self.model = genai.GenerativeModel(
            "models/gemini-1.5-flash",
            system_instruction=instruction["khodam" if is_khodam else "chatbot"].format(name=name, dev=dev),
        )
        self.safety_rate = {key: "BLOCK_NONE" for key in ["HATE", "HARASSMENT", "SEX", "DANGER"]}
        self.chat_history = {}

    def KhodamCheck(self, input):
        try:
            response = self.model.generate_content(input)
            return response.text.strip()
        except Exception as e:
            return f"Terjadi kesalahan: {str(e)}"

    def ChatBot(self, text, chat_id):
        try:
            if chat_id not in self.chat_history:
                self.chat_history[chat_id] = []

            self.chat_history[chat_id].append({"role": "user", "parts": text})

            chat_session = self.model.start_chat(history=self.chat_history[chat_id])
            response = chat_session.send_message({"role": "user", "parts": text}, safety_settings=self.safety_rate)

            self.chat_history[chat_id].append({"role": "model", "parts": response.text})

            return response.text
        except Exception as e:
            return f"Terjadi kesalahan: {str(e)}"

    def clear_chat_history(self, chat_id):
        if chat_id in self.chat_history:
            del self.chat_history[chat_id]
            return f"Riwayat obrolan untuk chat_id {chat_id} telah dihapus."
        else:
            return "Maaf, kita belum pernah ngobrol sebelumnya.."


class ImageGen:
    def __init__(self, url: str = "https://nolimit-api.netlify.app/api/bing-image-gen"):
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
