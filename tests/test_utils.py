from datetime import datetime
from pathlib import Path

from utils import (
    MediaType,
    datestamp_to_filename_stem,
    get_datestamp,
    get_media_type,
    get_sha256,
    is_image,
    is_media,
    is_video,
    recommended_filename,
)


def test_get_sha256():
    assert (
        get_sha256(Path("/Users/dottey/git/dupefinder/data/Rose/20210612_091422.jpg"))
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
    assert get_datestamp("/Users/dottey/git/dupefinder/data/Rose/20210612_091420.jpg") == datetime.strptime(
        "2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S"
    )
    assert get_datestamp(
        "/Users/dottey/git/dupefinder/data/problems/20181125_070907_IMG_2933.JPG"
    ) == datetime.strptime("2018-11-25 07:09:07.547", "%Y-%m-%d %H:%M:%S.%f")
    assert get_datestamp("/Users/dottey/git/dupefinder/data/problems/IMG_9846.PNG") is None


def test_datestamp_to_filenam_stem():
    assert (
        datestamp_to_filename_stem(datetime.strptime("2021-06-12 09:14:20", "%Y-%m-%d %H:%M:%S")) == "20210612_091420"
    )


def test_recommended_filename():
    assert recommended_filename(
        Path("/Users/dottey/git/dupefinder/data/Rose/20210612_091420_cap_extension.JPG")
    ) == Path("/Users/dottey/git/dupefinder/data/Rose/20210612_091420.jpg")
    assert recommended_filename(Path("/path/does/not/exist.txt")) is None
