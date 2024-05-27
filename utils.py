import enum
import hashlib
import itertools
import logging
import re
import sys
from configparser import ConfigParser
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path, PosixPath
from typing import List

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import Base as ExifBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

debug = False
if debug:
    logger.setLevel(logging.DEBUG)

pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.INFO)


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


def datestring_to_date(datestring: str):
    """Convert a string seeming to contain a timestamp into a datetime object.

    This function helps to convert odd timestamps coming from exif data. Some such stamps have
    * hyphens or colons seperating the year, month and date
    * a decimal containing the microseconds

    Args:
        datestring (str): A timestamp-like value
    """

    logger.debug(f"Original datetime is {datestring}")

    if datestring == "" or "0000" in datestring:
        return None

    PATTERNS = [
        {"regex": r"([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})$", "format": "%Y-%m-%d %H:%M:%S"},
        {"regex": r"([0-9]{4}):([0-9]{2}):([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})$", "format": "%Y:%m:%d %H:%M:%S"},
        {
            "regex": r"([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]{0,6})$",
            "format": "%Y-%m-%d %H:%M:%S.%f",
        },
        {
            "regex": r"([0-9]{4}):([0-9]{2}):([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]{0,6})$",
            "format": "%Y:%m:%d %H:%M:%S.%f",
        },
    ]

    for pattern in PATTERNS:
        if re.match(pattern["regex"], datestring):
            date_obj = datetime.strptime(datestring, pattern["format"])
            return date_obj

    raise ValueError(f"Unknown datetime format for {datestring}")


def get_datestamp(image_path: Path):
    logger.debug(f"Attempting get_datastamp of {image_path}")
    image_type = guess_type(image_path)[0]
    if not image_type.endswith(("jpeg", "png")):
        return None

    try:
        with open(image_path, "rb") as image_file:
            logger.debug(f"Opening image {image_path}")
            exif = Image.open(image_file).getexif()
            # logger.debug("Opened")
    except UnidentifiedImageError:
        logger.warning(f"UnidentifiedImageError while opening {image_path}")
        return None
    except Exception as e:
        logger.error(f"Unknown exception: {e} while opening {image_path}")
        return None

    if not exif:
        return None

    if ExifBase.DateTimeOriginal in exif.keys():
        date_obj = datestring_to_date(exif[ExifBase.DateTimeOriginal])
    elif ExifBase.DateTime in exif.keys():
        date_obj = datestring_to_date(exif[ExifBase.DateTime])
    else:
        return None

    return date_obj


def datestamp_to_filename_stem(date_obj: datetime):
    return date_obj.strftime("%Y%m%d_%H%M%S")


def get_recommended_filename(image_path: Path):
    image_type = guess_type(image_path)[0]
    if image_type.endswith("jpeg"):
        new_extension = "jpg"
    elif image_type.endswith("png"):
        new_extension = "png"
    else:
        return None

    datestamp_from_image = get_datestamp(image_path)
    if not datestamp_from_image:
        return None

    new_stem = datestamp_to_filename_stem(datestamp_from_image)
    parent_directory = image_path.parent

    new_filename = parent_directory.joinpath(f"{new_stem}.{new_extension}")
    return new_filename


# def get_info_dir(dir):
#     info = [(get_sha256(file), file.stat().st_size, file) for file in dir.rglob("*") if file.is_file()]
#     return info


def load_config(config_file, force_previous_database=True):
    config = ConfigParser()
    try:
        config.read(config_file)
    except Exception as e:
        logger.error(f"Unable to load configuration from {config_file}. {e}")
        sys.exit(1)

    DATA_DIR = Path(config.get("mediatool", "data_dir"))
    if not DATA_DIR.is_dir():
        logger.error(f"{DATA_DIR} is not a valid directory.")
        sys.exit(1)

    DBFILE = Path(config.get("mediatool", "db_file"))
    if force_previous_database and not DBFILE.is_file():
        logger.error(f"{DBFILE} is not available.")
        sys.exit(1)

    return DATA_DIR, DBFILE


def consolidate_files(paths_to_consolidate: List[Path | PosixPath], target_path: Path, dry_run: bool = False) -> int:
    """Consolidates a set of files into a single file. Essentially it deletes all files that are not the target file. If the target file is not one of the source files, then the first source file is moved to the target file path.

    Args:
        paths_to_consolidate (List[Path  |  PosixPath]): List of paths that should be consolidated.
        target_path (Path): The single path that should remain afterward.
        dry_run (bool, optional): In a dry run, the source files will be removed (unless the source is the same as the target). Defaults to False.

    Raises:
        TypeError: When the source or target is not a Path object.
        ValueError: If the source or target is not a valid file.

    Returns:
        int: The number of files that were deleted. (In a dry_run it would be the number of files that would have been deleted.)
    """

    # Other error conditions I could handle...
    # paths_to_consolidate is an empty list

    # Ensure all inputs are valid files
    for path in itertools.chain([target_path], paths_to_consolidate):
        if not isinstance(path, Path):
            raise TypeError(f"Invalid type for {str(path)}. Path expected, got '{type(path).__name__}'")
    for path in paths_to_consolidate:
        if not path.is_file():
            raise ValueError(f"{path} is not a valid file.")

    if target_path in paths_to_consolidate:
        # Create paths_to_remove by removing target path from paths_to_consolidate
        paths_to_remove = set(paths_to_consolidate) - set([target_path])
        logger.debug(f"T in P: Paths to remove = {paths_to_remove}")
    else:
        logger.debug(f"T not in P: Paths to consolidate = {paths_to_consolidate}")

        temp_source = paths_to_consolidate.pop()
        if not dry_run:
            temp_source.rename(target_path)
        paths_to_remove = paths_to_consolidate
        logger.debug(f"T not in P: Paths to remove = {paths_to_remove}")

    total_files_deleted = 0
    # Delete paths_to_remove
    for path in paths_to_remove:
        logger.debug(f"Deleting file {path}")
        if not dry_run:
            path.unlink()
        total_files_deleted += 1

    return total_files_deleted
