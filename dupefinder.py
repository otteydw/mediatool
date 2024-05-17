import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from logging_setup import logging_setup
from models import Base, File
from utils import (
    get_datestamp,
    get_media_type,
    get_sha256,
    is_image,
    recommended_filename,
)

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


def fill_database(session: Session, dir: Path, commit_every=20):
    logger.debug(f"Beginning investigation of {dir}")
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
                    logger.debug(f"Adding file {pathname}")
                    size = file.stat().st_size
                    sha256 = get_sha256(file)
                    media_type = get_media_type(pathname)
                    datestamp = get_datestamp(pathname) if is_image(pathname) else None
                    this_file = File(name=pathname, size=size, sha256=sha256, filetype=media_type, datestamp=datestamp)
                    session.add(this_file)
                    counter += 1
                elif pathname in existing_paths and (is_image(pathname)):
                    updated = False
                    logger.debug(f"Checking {pathname} for updates.")
                    existing_record = session.query(File).filter(File.name == pathname).one_or_none()
                    if not existing_record.datestamp:
                        # Check if the file has a datestamp and update it in the database only if it does.
                        this_datestamp = get_datestamp(pathname) if is_image(pathname) else None
                        if this_datestamp:
                            existing_record.datestamp = this_datestamp
                            updated = True
                    if not existing_record.filetype:
                        existing_record.filetype = get_media_type(pathname)
                        updated = True
                    if updated:
                        logger.debug(f"Updating file {pathname}")
                        counter += 1
                if counter == commit_every:
                    session.commit()
                    counter = 0
            session.commit()
    logger.info("Completed database fill.")


def find_duplicate_checksums(session: Session):
    stmt = text("select sha256 from (select sha256, count(sha256) as qty from file group by sha256) WHERE qty>1;")
    checksums = (checksum.sha256 for checksum in session.execute(stmt))
    return checksums


def process_duplicates(session):
    duplicate_checksums = [checksum for checksum in find_duplicate_checksums(session)]

    console = Console()

    duplicates = {}
    for checksum in duplicate_checksums:
        statement = select(File).filter_by(sha256=checksum)
        duplicates_of_checksum = [dupe_set.name for dupe_set in [row.File for row in session.execute(statement).all()]]
        duplicates[checksum] = duplicates_of_checksum

    for checksum, files in duplicates.items():
        table = Table(title=f"Duplicates of {checksum}")
        table.add_column("Parent")
        table.add_column("Filename")
        table.add_column("Recommend")
        for file in files:
            this_file = Path(file)
            parent = str(this_file.parent)
            name = str(this_file.name)
            recommend = recommended_filename(this_file)
            recommend = str(recommend.name) if recommend else ""
            table.add_row(parent, name, recommend)
        console.print(table)


def main():
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        fill_database(session, DATA_DIR)
        # process_duplicates(session)


if __name__ == "__main__":
    main()
