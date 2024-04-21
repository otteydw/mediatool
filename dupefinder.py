import hashlib
import os


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
    sha256sums = []
    for root, _, files in os.walk(dir, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            sha256sums.append((get_sha256(file), file))

    return sha256sums


for md5sum_pair in get_sha256_dir("data"):
    print(md5sum_pair[0], md5sum_pair[1])
