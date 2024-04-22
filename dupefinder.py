import hashlib
from mimetypes import guess_type
from pathlib import Path

from sqlalchemy import Integer, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

BASE_DIR = Path(__file__).resolve().parent

# DATA_DIR = BASE_DIR.joinpath("data")
# DBFILE = BASE_DIR.joinpath("dingo.db")

DATA_DIR = Path("/Volumes/media/Pictures")
DBFILE = BASE_DIR.joinpath("media.db")


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))

    def __repr__(self):
        return f"File: {self.name}\nSize {self.size}\nSHA256: {self.sha256}"


def is_media(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith(("image", "video")) else False


def is_image(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith("image") else False


def is_video(filename: Path):
    guessed_type = guess_type(filename)[0]
    return True if guessed_type and guessed_type.startswith("video") else False


def get_sha256(filename):
    print(f"Getting sha256 of {filename}")
    with open(filename, "rb") as f:
        file_hash = hashlib.sha256()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

    return file_hash.hexdigest()


# def get_info_dir(dir):
#     info = [(get_sha256(file), file.stat().st_size, file) for file in dir.rglob("*") if file.is_file()]
#     return info


def fill_database(session, dir: Path, commit_every=10):
    # all_files = [file for file in dir.rglob("*") if file.is_file()]
    # print("Got all_files")
    existing_paths = [path.name for path in session.query(File.name).all()]

    # for file in all_files:
    counter = 0
    for root, dirs, files in dir.walk():
        if len(files) > 0:
            print(root)
            paths = [Path(root).joinpath(file) for file in files]
            for file in paths:
                pathname = str(file)
                # print(pathname)
                if pathname not in existing_paths and (is_media(pathname)):
                    size = file.stat().st_size
                    sha256 = get_sha256(file)
                    this_file = File(name=pathname, size=size, sha256=sha256)
                    session.add(this_file)
                    counter += 1
                    if counter == commit_every:
                        session.commit()
                        counter = 0
            session.commit()


def find_duplicate_checksums(session: Session):
    stmt = text("select sha256 from (select sha256, count(sha256) as qty from file group by sha256) WHERE qty>1;")
    checksums = (checksum.sha256 for checksum in session.execute(stmt))
    return checksums


def process_duplicates(session):
    duplicate_checksums = [checksum for checksum in find_duplicate_checksums(session)]
    for checksum in duplicate_checksums:
        statement = select(File).filter_by(sha256=checksum)
        dupe_sets = [row.File for row in session.execute(statement).all()]
        for dupe_set in dupe_sets:
            print(dupe_set.name)
        print()


def main():
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        fill_database(session, DATA_DIR)
        # process_duplicates(session)


if __name__ == "__main__":
    main()
