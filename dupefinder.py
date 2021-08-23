import hashlib
import os

def get_md5(filename):
    # https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python/16876405
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        # file_hash = hashlib.blake2b()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

    return file_hash.hexdigest()

def get_md5_dir(dir):
    md5sums = []
    for root, _, files in os.walk(dir, topdown = False):
        for name in files:
            file = os.path.join(root, name)
            md5sums.append((get_md5(file), file))

    return md5sums

# print(get_md5('data/20210713-amfilm_cover_crack1.jpeg'))
# print()
for md5sum_pair in get_md5_dir('data'):
    print(md5sum_pair[0], md5sum_pair[1])
