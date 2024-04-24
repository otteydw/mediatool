import enum
import hashlib
import logging
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path

from exif import Image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MediaType(enum.Enum):
    image = 1
    video = 2
    unknown = 3


def is_media(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith(("image", "video")) else False


def is_image(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith("image") else False


def is_video(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith("video") else False


def get_media_type(filename: Path):
    if is_image(filename):
        return MediaType.image
    elif is_video(filename):
        return MediaType.video
    else:
        return MediaType.unknown


def get_sha256(filename):
    print(f"Getting sha256 of {filename}")
    with open(filename, "rb") as f:
        file_hash = hashlib.sha256()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

    return file_hash.hexdigest()


def get_datestamp(image_path: Path):
    logger.info(f"Attempting get_datastamp of {image_path}")
    image_type = guess_type(image_path)[0]
    if not image_type.endswith(("jpeg", "png")):
        return None

    try:
        with open(image_path, "rb") as image_file:
            image = Image(image_file)
    except (
        Exception
    ) as e:  # This is not good, but I can't figure out exactly what exception is being raised. I will deal with it later.
        if "TiffByteOrder" in str(e):
            logger.exception(f"Invalid byte order encountered in image {image_path}. Ignoring Exif data.")
            return None
        else:
            logger.exception("Encountered unknown exception")
            raise e

    if not image.has_exif:
        return None

    if hasattr(image, "datetime"):
        date_obj = datetime.strptime(image.datetime, "%Y:%m:%d %H:%M:%S")
    else:
        date_obj = None
    return date_obj


# def get_info_dir(dir):
#     info = [(get_sha256(file), file.stat().st_size, file) for file in dir.rglob("*") if file.is_file()]
#     return info
