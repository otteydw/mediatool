from pathlib import Path

from dupefinder import get_sha256


def test_get_sha256():
    assert (
        get_sha256(Path("/Users/dottey/git/dupefinder/data/Rose/20210612_091422.jpg"))
        == "80df98de279606939044478237271172399005e1d0b9cd8087fbfea704934020"
    )
