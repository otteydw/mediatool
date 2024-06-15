from pathlib import Path
from tempfile import gettempdir

import pytest

from utils import consolidate_files

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.joinpath("data")

SOURCE_FILES = [DATA_DIR.joinpath(f"source{num}.txt") for num in range(5)]
TARGET_FILE_FROM_SOURCES = SOURCE_FILES[0]
NEW_TARGET = Path(gettempdir()).joinpath("new_target.txt")


@pytest.fixture(params=["source", "same_dir", "temp_dir"])
def testfiles(request):
    target_from = request.param
    source_files = [DATA_DIR.joinpath(f"source{num}.txt") for num in range(5)]
    [path.touch() for path in source_files]

    match target_from:
        case "source":
            target_file = source_files[0]
        case "same_dir":
            target_file = DATA_DIR.joinpath("target.txt")
        case "temp_dir":
            target_file = NEW_TARGET
        case _:
            raise ValueError

    yield (source_files, target_file)

    all_test_files = source_files + [target_file] + [NEW_TARGET]
    [path.unlink() for path in all_test_files if path.is_file()]


@pytest.mark.parametrize(
    "dry_run",
    [
        (True),
        (False),
    ],
)
def test_consolidate_files(testfiles, dry_run):
    sources, target = testfiles
    expected = len(sources) - 1
    print()
    print(f"{sources=}")
    print(f"{target=}")
    assert consolidate_files(sources, target, dry_run) == expected

    for path in sources:
        if path != target:
            assert path.is_file() is dry_run

    if dry_run:
        assert target.is_file() is (target in sources)
    else:
        assert target.is_file() is True


@pytest.mark.parametrize(
    "sources,target,expected_exception",
    [
        (SOURCE_FILES, "/looks/like/a/path.jpg", TypeError),
        (
            SOURCE_FILES + ["/looks/like/a/path.jpg"],
            TARGET_FILE_FROM_SOURCES,
            TypeError,
        ),
        (
            SOURCE_FILES,
            Path("/path/does/not/exist.txt"),
            FileNotFoundError,
        ),
    ],
)
def test_consolidate_files_exceptions(testfiles, sources, target, expected_exception):
    # testfiles is called to create and destroy the test files reference in the global variables.
    # I would like to clean that up later.
    with pytest.raises(expected_exception):
        consolidate_files(sources, target)
