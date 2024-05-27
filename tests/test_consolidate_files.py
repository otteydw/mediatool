from pathlib import Path

import pytest

from utils import consolidate_files

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.joinpath("data")

SOURCE_FILES = [DATA_DIR.joinpath(f"source{num}.txt") for num in range(5)]
TARGET_FILE_FROM_SOURCES = SOURCE_FILES[0]


@pytest.fixture(params=[True, False])
def testfiles(request):
    target_from_source = request.param
    source_files = [DATA_DIR.joinpath(f"source{num}.txt") for num in range(5)]
    [path.touch() for path in source_files]

    if target_from_source:
        target_file = source_files[0]
    else:
        target_file = DATA_DIR.joinpath("target.txt")

    yield (source_files, target_file)

    all_test_files = source_files + [target_file]
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
    print(f"Sources: {sources}")
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
