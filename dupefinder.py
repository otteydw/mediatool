import hashlib

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

print(get_md5('data/20210713-amfilm_cover_crack1.jpeg'))
