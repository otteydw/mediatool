import logging
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from logging_setup import logging_setup
from models import Base, File
from utils import get_datestamp, get_media_type, get_sha256, is_image

logging_setup()
logger = logging.getLogger(__name__)


debug = True
if debug:
    logger.setLevel(logging.DEBUG)

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR.joinpath("data")
DBFILE = BASE_DIR.joinpath("dingo.db")

# DATA_DIR = Path("/Volumes/media/Pictures")
# DBFILE = BASE_DIR.joinpath("media.db")


def fill_database(session: Session, dir: Path, commit_every=10):
    # all_files = [file for file in dir.rglob("*") if file.is_file()]
    # print("Got all_files")
    existing_paths = [path.name for path in session.query(File.name).all()]

    # for file in all_files:
    counter = 0
    for root, dirs, files in dir.walk():
        if len(files) > 0:
            logger.info(f"Root: {root}")
            paths = [Path(root).joinpath(file) for file in files]
            for file in paths:
                pathname = str(file)
                # print(pathname)
                logger.debug(f"Inspecting file {pathname}")
                if pathname not in existing_paths and (is_image(pathname)):
                    logger.info(f"Processing file {pathname}")
                    size = file.stat().st_size
                    sha256 = get_sha256(file)
                    media_type = get_media_type(pathname)
                    datestamp = get_datestamp(pathname) if is_image(pathname) else None
                    this_file = File(name=pathname, size=size, sha256=sha256, filetype=media_type, datestamp=datestamp)
                    session.add(this_file)
                    counter += 1
                    if counter == commit_every:
                        session.commit()
                        counter = 0
                # elif pathname in existing_paths and (is_media(pathname)):
                #     # stmt = select(File.name).where(File.name==pathname)
                #     # this_file = session.execute(stmt).scalar_one()
                #     # this_file = session.query(File.name, File.size).where(File.name == pathname).first()
                #     # this_file = session.query(File.name, File.size).get(File.name==pathname)
                #     this_file = File.query.filter_by(name=pathname).first()
                #     print(f"Found {this_file.name} with size {this_file.size}")
                #     this_file.size=10
                #     session.update(this_file)
                #     session.commit()
                #     print()
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
            logger.info(dupe_set.name)
        logger.info()


def main():
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        fill_database(session, DATA_DIR)
        # process_duplicates(session)


if __name__ == "__main__":
    main()
    # image_path = Path("/Users/dottey/git/dupefinder/data/Rose/20210612_091422.jpg")
    # print(get_datestamp(image_path))
