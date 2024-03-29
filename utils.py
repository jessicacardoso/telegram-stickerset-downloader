from copyreg import pickle
import os
import pickle
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
TEMP_FILE = config["temp_file"].get()


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


def get_channel_access_date(id) -> datetime:
    """Obtém a última data de acesso de um dado canal, caso não tenha
    cadastro então retorna a data 0 da biblioteca datetime.
    """
    return connect(query_channel, channel_id=id)


def register_channel(chat) -> bool:
    """Dado um chat, cadastra se não existir, caso contrário atualiza a data
    de acesso. Essa função retorna verdadeiro se houve cadastro.
    """
    created = connect(create_or_update_channel, channel_id=chat.id, title=chat.title)
    if created:
        console.print(
            f":speaker: - O canal {chat.title} foi inserido a base de dados",
            style="bold cyan",
        )
    return created


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
        console.print(
            f":framed_picture: - O stickerset {sticker_set.short_name} foi inserido a base de dados",
            style="bold cyan",
        )


async def register_sticker(app, sticker):

    file_path = connect(select_sticker, file_unique_id=sticker.file_unique_id)

    if file_path != "":
        return

    image_path = await app.download_media(
        sticker.file_id,
        os.path.join(config["output_dir"].get(), sticker.set_name) + "/",
    )

    sticker_fields = {
        "file_id": sticker.file_id,
        "file_unique_id": sticker.file_unique_id,
        "date": convert_datetime_to_utc(sticker.date),
        "width": sticker.width,
        "height": sticker.height,
        "is_animated": sticker.is_animated,
        "is_video": sticker.is_video,
        "emoji": sticker.emoji,
        "set_name": sticker.set_name,
        "image_path": image_path,
    }

    connect(insert_sticker, attrs=sticker_fields)


def zero_datetime() -> datetime:
    return datetime.fromtimestamp(0, timezone.utc)


def save_temporary_file(obj, prefix: str):
    with open(TEMP_FILE.format(prefix=prefix), "wb") as f:
        pickle.dump(obj, f)


def load_temporary_file(prefix: str):
    if os.path.exists(TEMP_FILE.format(prefix=prefix)):
        with open(TEMP_FILE.format(prefix=prefix), "rb") as f:
            return pickle.load(f)


def remove_temporary_file(prefix: str):
    if os.path.exists(TEMP_FILE.format(prefix=prefix)):
        os.remove(TEMP_FILE.format(prefix=prefix))


def convert_datetime_to_utc(date) -> datetime:
    return datetime.fromtimestamp(date.timestamp(), timezone.utc)
