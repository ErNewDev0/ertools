from io import BytesIO
from pyrogram import enums


class Extract:
    async def getUserId(self, message, username):
        entities = message.entities

        if entities:
            entity_index = 1 if message.text.startswith("/") else 0
            entity = entities[entity_index]

            if entity.type == enums.MessageEntityType.MENTION:
                return (await message._client.get_chat(username)).id
            elif entity.type == enums.MessageEntityType.TEXT_MENTION:
                return entity.user.id
        return username

    async def userId(self, message, text):
        if text.isdigit():
            return int(text)
        else:
            return await self.getUserId(message, text)

    async def getRid(self, message, sender_chat=False):
        text = message.text.strip()
        args = text.split()

        if message.reply_to_message:
            reply = message.reply_to_message
            if reply.from_user:
                user_id = reply.from_user.id
            elif sender_chat and reply.sender_chat and reply.sender_chat.id != message.chat.id:
                user_id = reply.sender_chat.id
            else:
                return None, None

            reason = text.split(None, 1)[1] if len(args) > 1 else None
            return user_id, reason

        if len(args) == 2:
            user = args[1]
            return await self.userId(message, user), None

        if len(args) > 2:
            user, reason = args[1], " ".join(args[2:])
            return await self.userId(message, user), reason

        return None, None

    async def getAdmin(self, message):
        member = await message._client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)

    async def getId(self, message):
        return (await self.getRid(message))[0]

    def getMention(self, user, no_tag=False):
        name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        link = f"tg://user?id={user.id}"
        return name if no_tag else f"[{name}]({link})"


class Handler:
    def getArg(self, message):
        if message.reply_to_message and len(message.command) < 2:
            return message.reply_to_message.text or message.reply_to_message.caption or ""
        return message.text.split(None, 1)[1] if len(message.command) > 1 else ""

    def getMsg(self, message, is_chatbot=False):
        reply_text = message.reply_to_message.text or message.reply_to_message.caption if message.reply_to_message else ""
        user_text = message.text if is_chatbot else (message.text.split(None, 1)[1] if len(message.text.split()) >= 2 else "")
        return f"{user_text}\n\n{reply_text}".strip() if reply_text and user_text else reply_text + user_text

    async def kirim_pesan(self, message, output):
        if len(output) <= 4000:
            await message.reply(output)
        else:
            with BytesIO(output.encode()) as out_file:
                out_file.name = "result.txt"
                await message.reply_document(document=out_file)

    async def getTime(self, seconds):
        time_units = [(60, "s"), (60, "m"), (24, "h"), (7, "d"), (4.34812, "w")]
        result = []

        for unit_seconds, suffix in time_units:
            if seconds == 0:
                break
            seconds, value = divmod(seconds, unit_seconds)
            if value > 0:
                result.append(f"{int(value)}{suffix}")

        if not result:
            return "0s"

        return ":".join(result[::-1])
