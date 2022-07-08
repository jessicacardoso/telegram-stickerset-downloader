# from pyrogram import Client
# from pyrogram.enums import ChatType

# app = Client("my_account")

# async def main():
#     async with app:
#         async for dialog in app.get_dialogs():
#             if dialog.chat.type is ChatType.CHANNEL:
#                 print(dialog.chat.title or dialog.chat.first_name, ":", dialog.chat.id)


# app.run(main())


# from pyrogram import Client
# from pyrogram.enums import MessageMediaType
# from pprint import pprint

# app = Client("my_account")
# stickersets = set()

# async def main():

#     async with app:
#         async for message in app.get_chat_history("-1001194960114"):
#             if message.media is MessageMediaType.STICKER:
#                 sticker = message.sticker
#                 # print(sticker)
#                 if sticker.set_name not in stickersets:
#                     stickersets.add(message.sticker.set_name)
#                     await app.send_message("me", f"tg://addstickers?set={sticker.set_name}")
#                     await app.send_message("me", message.date)
#                 break


# app.run(main())

from rich.progress import track
from pyrogram import Client
from pyrogram.file_id import FileId, FileType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import (
    InputStickerSetShortName,
)


# Create a new Client instance
app = Client("my_account")


async def main():
    # https://stackoverflow.com/questions/70141745/get-sticker-set-by-link-shot-namepyrogram
    # https://github.com/pyrogram/pyrogram/issues/975
    async with app:
        # Send a message, Markdown is enabled by default
        # await app.send_message("me", "Hi there! I'm using **Pyrogram**")
        sticker_set = await app.invoke(
            GetStickerSet(
                stickerset=InputStickerSetShortName(short_name="AnyaVid"), hash=0
            )
        )
        for sticker_doc in track(
            sticker_set.documents,
            description=f"[green]Processing {sticker_set.set.title}",
        ):

            file_id = FileId(
                file_type=FileType.STICKER,
                dc_id=sticker_doc.dc_id,
                file_reference=sticker_doc.file_reference,
                access_hash=sticker_doc.access_hash,
                media_id=sticker_doc.id,
            ).encode()

            await app.download_media(file_id)
            # image_bytes_io = await app.download_media(file_id, in_memory=True)
            # with open(image_bytes_io.name, "wb") as f:
            #     f.write(image_bytes_io.getbuffer())


app.run(main())
