from datetime import datetime
import logging
import pyrogram.errors
from pyrogram.enums import MessageMediaType, MessageEntityType
from pyrogram import Client
from pyrogram.file_id import FileId, FileType, FileUniqueId, FileUniqueType
from pyrogram.enums import ChatType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.types import Sticker
from InquirerPy.base.control import Choice
from rich.progress import track
from rich.logging import RichHandler
from rich.console import Console
import os

from utils import (
    prompt_channels,
    register_channel,
    register_sticker,
    CHANNEL_ID,
    register_sticket_set,
)

ADD_STICKERS_URLS = ["http://t.me/addstickers"]
app = Client("my_account")


FORMAT = "%(message)s"
logging.basicConfig(format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

log = logging.getLogger("rich")
console = Console()


async def get_sticker_set_by_short_name(app, short_name):
    try:
        return await app.invoke(
            GetStickerSet(
                stickerset=InputStickerSetShortName(short_name=short_name),
                hash=0,
            )
        )
    except pyrogram.errors.exceptions.not_acceptable_406.StickersetInvalid:
        log.error(
            f"[bold red]Stickerset {short_name} not found![/]",
            extra={"markup": True},
        )


async def get_stickerset_from_link(entities, stickersets):
    entities = [] if not entities else entities
    for entity in entities:
        if entity.type is MessageEntityType.TEXT_LINK:
            base_url, short_name = os.path.split(entity.url)
            if base_url in ADD_STICKERS_URLS and short_name not in stickersets:
                sticker_set = await get_sticker_set_by_short_name(app, short_name)
                if sticker_set:
                    stickersets[short_name] = sticker_set


async def get_stickersets_from_chat(channel: str, start_date: datetime):
    """Obtém todos os StickerSets de um dado canal do Telegram."""
    stickersets = {}
    index = 1
    with console.status(f"[bold green]Scanning {channel} channel messages..."):
        async for message in app.get_chat_history(str(channel), offset_date=start_date):
            if message.media is MessageMediaType.STICKER:
                sticker = message.sticker
                if not sticker.set_name:
                    continue
                if sticker.set_name not in stickersets:
                    stickersets[
                        message.sticker.set_name
                    ] = await get_sticker_set_by_short_name(app, sticker.set_name)
                    console.log(f"Added {sticker.set_name}")
            else:
                await get_stickerset_from_link(message.entities, stickersets)
            index += 1
            if index % 1000 == 0:
                console.clear()
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
        file_unique_id = FileUniqueId(
            file_unique_type=FileUniqueType.DOCUMENT, media_id=sticker_doc.id
        ).encode()

        sticker = Sticker(
            file_unique_id=file_unique_id,
            file_id=file_id,
            date=datetime.fromtimestamp(sticker_doc.date),
            width=sticker_doc.attributes[0].w,
            height=sticker_doc.attributes[0].h,
            is_animated=sticker_set.set.animated,
            is_video=sticker_set.set.videos,
            set_name=sticker_set.set.short_name,
            emoji=sticker_doc.attributes[1].alt,
        )
        await register_sticker(app, sticker)


async def main():
    async with app:
        selected_channels = await prompt_channels(
            [
                Choice(dialog.chat.username or dialog.chat.id, name=dialog.chat.title)
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
