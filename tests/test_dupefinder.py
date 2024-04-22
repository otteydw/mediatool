from pathlib import Path

from dupefinder import get_sha256, is_image, is_media, is_video


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
