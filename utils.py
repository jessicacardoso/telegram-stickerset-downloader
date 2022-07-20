import os
import confuse
from rich.console import Console
from InquirerPy import inquirer
from datetime import datetime, timezone

from db import (
    connect,
    create_or_update_channel,
    create_or_update_stickerset,
    insert_sticker,
    query_channel,
    select_sticker,
)


console = Console()

config = confuse.Configuration("StickerApp", __name__)
CHANNEL_ID = str(config["channel_id"])


async def prompt_channels(channels_choice: list):
    """Lista todos os canais da conta fornecida do telegram, e solicita
    a seleção daqueles utilizados para o download dos Stickers.
    """
    console.print("[green]:speaker: StickerSetDownloader")
    channels = await inquirer.checkbox(
        message="Selecione um ou mais canais para download dos Stickers:",
        choices=channels_choice,
        validate=lambda result: len(result) >= 1,
        invalid_message="should be at least 1 selection",
        instruction="(select at least 1)",
    ).execute_async()
    return channels


def register_channel(chat) -> datetime:
    """Dado um chat, cadastra se não existir, caso contrário atualiza a data
    de acesso. Essa função retorna a data anteriormente registrada, caso haja
    cadastro.
    """
    last_access = connect(query_channel, channel_id=chat.id)
    created = connect(create_or_update_channel, channel_id=chat.id, title=chat.title)
    if created:
        console.print(f":speaker: - O canal {chat.title} foi inserido a base de dados", style="bold cyan")
    return last_access


def register_sticket_set(sticker_set):
    """Registra um Stickerset ao banco de dados"""
    sticker_set_fields = {
        "id": sticker_set.id,
        "access_hash": sticker_set.access_hash,
        "title": sticker_set.title,
        "short_name": sticker_set.short_name,
        "count": sticker_set.count,
        "hash": sticker_set.hash,
        "official": sticker_set.official,
        "animated": sticker_set.animated,
        "videos": sticker_set.videos,
    }
    created = connect(create_or_update_stickerset, attrs=sticker_set_fields)
    if created:
        console.print(f":framed_picture: - O stickerset {sticker_set.short_name} foi inserido a base de dados", style="bold cyan")


async def register_sticker(app, file_id: str):
    message = await app.send_sticker(CHANNEL_ID, file_id)

    file_path = connect(select_sticker, file_unique_id=message.sticker.file_unique_id)

    if file_path != "":
        return

    image_path = await app.download_media(
        message.sticker.file_id,
        os.path.join(config["output_dir"].get(), message.sticker.set_name) + "/",
    )

    sticker_fields = {
        "file_id": message.sticker.file_id,
        "file_unique_id": message.sticker.file_unique_id,
        "date": message.sticker.date,
        "width": message.sticker.width,
        "height": message.sticker.height,
        "is_animated": message.sticker.is_animated,
        "is_video": message.sticker.is_video,
        "emoji": message.sticker.emoji,
        "set_name": message.sticker.set_name,
        "image_path": image_path,
    }

    connect(insert_sticker, attrs=sticker_fields)

    # image_bytes_io = await app.download_media(message.sticker.file_id, in_memory=True)
    # with open(image_bytes_io.name, "wb") as f:
    #     f.write(image_bytes_io.getbuffer())
