import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.joinpath("data")


def get_sha256(filename):
    print(f"Getting sha256 of {filename}")
    with open(filename, "rb") as f:
        file_hash = hashlib.sha256()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

    return file_hash.hexdigest()


def get_sha256_dir(dir):
    sha256sums = [(get_sha256(file), file) for file in dir.rglob("*") if file.is_file()]
    return sha256sums


for md5sum_pair in get_sha256_dir(DATA_DIR):
    print(md5sum_pair[0], md5sum_pair[1])
