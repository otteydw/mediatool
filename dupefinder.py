import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from logging_setup import logging_setup
from models import Base, File
from utils import recommended_filename

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
        process_duplicates(session)


if __name__ == "__main__":
    main()
