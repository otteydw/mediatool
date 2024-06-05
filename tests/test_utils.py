from datetime import datetime
from pathlib import Path

import pytest

from utils import (
    MediaType,
    datestamp_to_filename_stem,
    datestamp_to_folder,
    datestring_to_date,
    get_datestamp,
    get_media_type,
    get_recommended_filename,
    get_sha256,
    is_image,
    is_media,
    is_video,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.joinpath("data")


def test_get_sha256():
    assert (
        get_sha256(Path(DATA_DIR.joinpath("Rose/20210612_091422.jpg")))
        == "80df98de279606939044478237271172399005e1d0b9cd8087fbfea704934020"
    )


def test_is_image():
    assert is_image(Path("/path/does/not/matter/filename.jpg")) is True
    assert is_image(Path("/path/does/not/matter/filename.mov")) is False
    assert is_image(Path("/path/does/not/matter/filename.txt")) is False
    assert is_image(Path("/path/does/not/matter/filename.ini")) is False


def test_is_video():
    assert is_video(Path("/path/does/not/matter/filename.mov")) is True
    assert is_video(Path("/path/does/not/matter/filename.jpg")) is False
    assert is_video(Path("/path/does/not/matter/filename.txt")) is False
    assert is_video(Path("/path/does/not/matter/filename.init")) is False


def test_is_media():
    assert is_media(Path("/path/does/not/matter/filename.mov")) is True
    assert is_media(Path("/path/does/not/matter/filename.jpg")) is True
    assert is_media(Path("/path/does/not/matter/filename.txt")) is False
    assert is_media(Path("/path/does/not/matter/filename.ini")) is False


def test_get_media_type():
    assert get_media_type(Path("/path/does/not/matter/filename.jpg")) == MediaType.image
    assert get_media_type(Path("/path/does/not/matter/filename.mov")) == MediaType.video
    assert get_media_type(Path("/path/does/not/matter/filename.txt")) == MediaType.unknown


def test_get_datestamp():
    assert get_datestamp(DATA_DIR.joinpath("Rose/20210612_091420.jpg")) == datetime.strptime(
        "2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S"
    )
    assert get_datestamp(DATA_DIR.joinpath("problems/20181125_070907_IMG_2933.JPG")) == datetime.strptime(
        "2018-11-25 07:09:07.547000", "%Y-%m-%d %H:%M:%S.%f"
    )
    assert get_datestamp(DATA_DIR.joinpath("problems/IMG_9846.PNG")) is None
    assert get_datestamp(DATA_DIR.joinpath("problems/hidden_PICT0200.JPG")) is None

    # Hockey and stuff 014.JPG may be corrupt. Revisit later.
    # OSError: Unsupported BMP header type (65536)
    assert get_datestamp(DATA_DIR.joinpath("problems/Hockey and stuff 014.JPG")) is None


def test_datestamp_to_filenam_stem():
    assert (
        datestamp_to_filename_stem(datetime.strptime("2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S")) == "20210612_091420"
    )


def test_datestamp_to_folder():
    assert datestamp_to_folder(datetime.strptime("2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S")) == "2021/06/12"


def test_get_recommended_filename():
    assert get_recommended_filename(DATA_DIR.joinpath("Rose/20210612_091420_cap_extension.JPG")) == DATA_DIR.joinpath(
        "Rose/20210612_091420.jpg"
    )
    assert get_recommended_filename(
        DATA_DIR.joinpath("Rose/20210612_091420_cap_extension.JPG"), date_folders=True
    ) == DATA_DIR.joinpath("Rose/2021/06/12/20210612_091420.jpg")
    assert get_recommended_filename(
        DATA_DIR.joinpath("Rose/20210612_091420_cap_extension.JPG"), root_dir=Path("/dingo")
    ) == Path("/dingo/20210612_091420.jpg")
    assert get_recommended_filename(
        DATA_DIR.joinpath("Rose/20210612_091420_cap_extension.JPG"), root_dir=Path("/dingo"), date_folders=True
    ) == Path("/dingo/2021/06/12/20210612_091420.jpg")
    assert get_recommended_filename(Path("/path/does/not/exist.txt")) is None


def test_datestring_to_date():
    assert datestring_to_date("2021-06-12 09:14:20") == datetime.strptime("2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S")
    assert datestring_to_date("2021:06:12 09:14:20") == datetime.strptime("2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S")
    assert datestring_to_date("2021:06:12 09:14:20.345000") == datetime.strptime(
        "2021-06-12 09:14:20.345000", "%Y-%m-%d %H:%M:%S.%f"
    )
    assert datestring_to_date("2021:06:12 09:14:20.345") == datetime.strptime(
        "2021-06-12 09:14:20.345000", "%Y-%m-%d %H:%M:%S.%f"
    )
    assert datestring_to_date("") is None
    assert datestring_to_date("0000:00:00 00:00:00") is None

    with pytest.raises(ValueError):
        datestring_to_date("2021x06x12 09:14:20.345000")
