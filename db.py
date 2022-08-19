#!/usr/bin/python
import psycopg2
from datetime import datetime, timezone
import confuse


def config(section="postgresql"):
    params = confuse.Configuration("StickerApp", __name__)

    if params[section]:
        return params[section]
    else:
        raise Exception("Section {0} not found in the yaml".format(section))


db = config()


def create_tables(cur):
    """As tabelas usadas na aplicação são:
    - channels
    - stickersets
    - stickers
    """
    commands = (
        """
        CREATE TABLE channels (
            channel_id BIGSERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            access_date TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE stickersets (
            id BIGSERIAL PRIMARY KEY,
            access_hash BIGINT NOT NULL,
            title TEXT NOT NULL,
            short_name TEXT NOT null,
            count INTEGER NOT NULL,
            hash BIGINT NOT NULL,
            official BOOLEAN,
            animated BOOLEAN,
            videos BOOLEAN
        )
        """,
        """
        CREATE TABLE stickers (
            file_unique_id TEXT NOT NULL PRIMARY KEY,
            file_id TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            is_animated BOOLEAN NOT NULL,
            is_video BOOLEAN NOT NULL,
            emoji TEXT NOT NULL,
            set_name TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
        """,
    )
    print("Criando tabelas...")
    for command in commands:
        cur.execute(command)


def query_channel(cur, channel_id):
    """Consulta a última data de acesso a um canal"""
    query = """
        SELECT access_date
        FROM channels
        WHERE channel_id = %s
    """
    cur.execute(query, (channel_id,))
    row = cur.fetchone()
    if not row:
        return datetime.fromtimestamp(0, timezone.utc)
    return row[0]


def create_or_update_channel(cur, channel_id, title):
    current_timestamp = datetime.utcnow()

    query = """
        SELECT access_date
        FROM channels
        WHERE channel_id = %s
    """
    cur.execute(query, (channel_id,))
    row = cur.fetchone()
    created = False

    if not row:
        created = True
        cur.execute(
            """
        INSERT INTO channels
        (channel_id, title, access_date)
        VALUES(%s, %s, %s);

        """,
            (channel_id, title, current_timestamp.isoformat()),
        )
    else:
        cur.execute(
            """
        UPDATE channels
        SET title=%s, access_date=%s
        WHERE channel_id=%s;
        """,
            (title, current_timestamp.isoformat(), channel_id),
        )
    return created


def create_or_update_stickerset(cur, attrs):
    query = """
        SELECT id, access_hash, title, short_name, count, hash, official, animated, videos
        FROM stickersets
        WHERE id = %s and short_name = %s;
    """
    cur.execute(query, (attrs["id"], attrs["short_name"]))
    row = cur.fetchone()
    created = False

    if not row:
        created = True
        cur.execute(
            """
        INSERT INTO stickersets
        (id, access_hash, title, short_name, count, hash, official, animated, videos)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);

        """,
            (
                attrs["id"],
                attrs["access_hash"],
                attrs["title"],
                attrs["short_name"],
                attrs["count"],
                attrs["hash"],
                attrs["official"],
                attrs["animated"],
                attrs["videos"],
            ),
        )
    else:
        cur.execute(
            """
        UPDATE stickersets
        SET access_hash=%s, title=%s, count=%s, hash=%s, official=%s, animated=%s, videos=%s
        WHERE id = %s and short_name = %s;
        """,
            (
                attrs["access_hash"],
                attrs["title"],
                attrs["count"],
                attrs["hash"],
                attrs["official"],
                attrs["animated"],
                attrs["videos"],
                attrs["id"],
                attrs["short_name"],
            ),
        )
    return created


def select_sticker(cur, file_unique_id: str) -> str:
    """Retorna o caminho onde foi salvo o sticker no disco"""
    query = """
        SELECT file_unique_id, file_id, "date", width, height, is_animated, is_video, emoji, set_name, image_path
        FROM stickers
        WHERE file_unique_id = %s
    """
    cur.execute(query, (file_unique_id,))
    row = cur.fetchone()
    if not row:
        return ""
    return row[9]


def insert_sticker(cur, attrs):
    sql = """
    INSERT INTO stickers
    (file_unique_id, file_id, "date", width, height, is_animated, is_video, emoji, set_name, image_path)
    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    cur.execute(
        sql,
        (
            attrs["file_unique_id"],
            attrs["file_id"],
            attrs["date"],
            attrs["width"],
            attrs["height"],
            attrs["is_animated"],
            attrs["is_video"],
            attrs["emoji"],
            attrs["set_name"],
            attrs["image_path"],
        ),
    )


def connect(func, *args, **kwargs):
    """Connect to the PostgreSQL database server"""
    conn = None
    data = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)

        # create a cursor
        cur = conn.cursor()

        data = func(*args, **kwargs, cur=cur)

        # Commit the changes to the database
        conn.commit()

        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return data


if __name__ == "__main__":
    connect(create_tables)
