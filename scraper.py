from datetime import datetime
from pyrogram.enums import MessageMediaType
from pyrogram import Client
from pyrogram.file_id import FileId, FileType
from pyrogram.enums import ChatType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import (
    InputStickerSetShortName,
)
from InquirerPy.base.control import Choice
from rich.progress import track

from utils import (
    prompt_channels,
    register_channel,
    register_sticker,
    CHANNEL_ID,
    register_sticket_set,
)


app = Client("my_account")


async def get_stickersets_from_chat(channel_id: str, start_date: datetime):
    """Obtém todos os StickerSets de um dado canal do Telegram."""
    stickersets = {}
    async for message in app.get_chat_history(str(channel_id), offset_date=start_date):
        if message.media is MessageMediaType.STICKER:
            sticker = message.sticker
            if sticker.set_name not in stickersets:
                stickersets[message.sticker.set_name] = await app.invoke(
                    GetStickerSet(
                        stickerset=InputStickerSetShortName(
                            short_name=message.sticker.set_name
                        ),
                        hash=0,
                    )
                )
    return stickersets


async def process_stickers(sticker_set):
    """Dado um stickerset, essa função realiza a captura de todos os
    Stickers contidos no StickerSet.
    """
    # https://stackoverflow.com/questions/70141745/get-sticker-set-by-link-shot-namepyrogram
    # https://github.com/pyrogram/pyrogram/issues/975
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
        await register_sticker(app, file_id)


async def main():
    async with app:
        selected_channels = await prompt_channels(
            [
                Choice(dialog.chat.id, name=dialog.chat.title)
                async for dialog in app.get_dialogs()
                if dialog.chat.type is ChatType.CHANNEL
            ]
        )
        for channel_id in selected_channels:
            chat = await app.get_chat(channel_id)
            start_date = register_channel(chat)
            stickersets = await get_stickersets_from_chat(channel_id, start_date)
            for sticker_set in stickersets.values():
                register_sticket_set(sticker_set.set)
                await process_stickers(sticker_set)


app.run(main())
