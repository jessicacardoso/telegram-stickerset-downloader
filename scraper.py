from datetime import datetime
import logging
import pyrogram.errors
from pyrogram.enums import MessageMediaType, MessageEntityType
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.types import Sticker
from InquirerPy.base.control import Choice
from rich.progress import track
from rich.logging import RichHandler
from rich.console import Console
import os
from db import connect, get_most_recent_stickerset
from utils import (
    convert_datetime_to_utc,
    get_channel_access_date,
    load_temporary_file,
    prompt_channels,
    register_channel,
    register_sticker,
    register_sticket_set,
    remove_temporary_file,
    save_temporary_file,
    zero_datetime,
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


async def get_stickersets_from_chat(
    chat: str, oldest_date: datetime = zero_datetime()
) -> dict:
    """Obtém todos os StickerSets de um dado chat do Telegram. O histórico de
    um chat do telegram é percorrido do mais recente ao mais antigo.

    Args:
        chat (str): Se o chat for público, informe o nome de usuário, caso
        contrário o id.
        oldest_date (datetime, optional): Permite limitar a data mais antiga
        permitida na varredura. Se nada for informado, percorre todo o chat.

    Returns:
        dict: Dicionário contendo todos os stickersets encontrados desde a data
        mais antiga até a atual.
    """
    stickersets = {}
    index = 1
    with console.status(f"[bold green]Scanning {chat} messages..."):
        async for message in app.get_chat_history(str(chat)):
            message_date = convert_datetime_to_utc(message.date).replace(tzinfo=None)
            if message_date < oldest_date:
                break
            if message.media is MessageMediaType.STICKER:
                sticker = message.sticker
                if not sticker.set_name:
                    continue
                if sticker.set_name not in stickersets:
                    stickersets[
                        message.sticker.set_name
                    ] = await get_sticker_set_by_short_name(app, sticker.set_name)
                    console.log(sticker.set_name)
            else:
                await get_stickerset_from_link(message.entities, stickersets)
            index += 1
            if index % 1000 == 0:
                console.clear()
        if stickersets:
            save_temporary_file(stickersets, chat)
    return stickersets


async def process_stickers(sticker_set):
    """Dado um stickerset, essa função realiza a captura de todos os
    Stickers contidos no StickerSet.
    """
    for sticker_doc in track(
        sticker_set.documents,
        description=f"[green]Processing {sticker_set.set.title}",
    ):
        document_attributes = {type(attr): attr for attr in sticker_doc.attributes}
        sticker = await Sticker._parse(app, sticker_doc, document_attributes)
        await register_sticker(app, sticker)


async def get_stickersets(channel_id, oldest_date):
    stickersets = load_temporary_file(channel_id)
    if stickersets:
        latest_stickerset = connect(get_most_recent_stickerset)
        return latest_stickerset, stickersets
    else:
        return None, await get_stickersets_from_chat(channel_id, oldest_date)


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
            access_date = get_channel_access_date(chat.id)
            latest_stickerset, stickersets = await get_stickersets(
                channel_id, access_date
            )
            is_last_stickerset = False
            register_channel(chat)
            for name, sticker_set in stickersets.items():

                if (
                    latest_stickerset
                    and is_last_stickerset == False
                    and name != latest_stickerset
                ):
                    continue
                if name == latest_stickerset:
                    is_last_stickerset = True

                register_sticket_set(sticker_set.set)
                await process_stickers(sticker_set)
            # Remove stickersets salvos temporariamente no disco
            remove_temporary_file(channel_id)


app.run(main())
