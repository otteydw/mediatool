import logging
from pathlib import Path

from more_itertools import first
from rich.console import Console
from rich.prompt import IntPrompt
from rich.table import Table
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from logging_setup import logging_setup
from models import Base, File
from utils import get_recommended_filename, load_config

logging_setup()
logger = logging.getLogger(__name__)


debug = False
if debug:
    logger.setLevel(logging.DEBUG)
# else:
#     logger.setLevel(logging.WARN)


def find_duplicate_checksums(session: Session):
    stmt = text("select sha256 from (select sha256, count(sha256) as qty from file group by sha256) WHERE qty>1;")
    checksums = (checksum.sha256 for checksum in session.execute(stmt))
    return checksums


def process_duplicates(session):
    logger.debug("Searching for duplicate checksums from the database.")
    duplicate_checksums = [checksum for checksum in find_duplicate_checksums(session)]
    logger.info(f"Found {len(duplicate_checksums)} duplicate checksums.")
    console = Console()

    # logger.debug("Loop through each duplicate checksum")
    # duplicates = {}
    for checksum in duplicate_checksums:
        statement = select(File).filter_by(sha256=checksum)
        duplicates_of_checksum = [dupe_set.name for dupe_set in [row.File for row in session.execute(statement).all()]]
        # duplicates[checksum] = duplicates_of_checksum

        number_of_files_found = len(duplicates_of_checksum)
        table = Table(title=f"Duplicates of {checksum}")
        table.add_column("")
        table.add_column("Parent")
        table.add_column("Filename")
        # table.add_column("Recommend")
        for file_number, file in enumerate(duplicates_of_checksum, start=1):
            this_file = Path(file)
            parent = str(this_file.parent)
            name = str(this_file.name)
            # recommend = recommended_filename(this_file)
            # recommend = str(recommend.name) if recommend else ""
            table.add_row(str(file_number), parent, name)
        console.print(table)

        while True:
            keep_number = IntPrompt.ask("Which one to keep?", default=1)
            if keep_number >= 1 and keep_number <= number_of_files_found:
                break

        console.print(f"We want to keep file {keep_number} which is {duplicates_of_checksum[keep_number-1]}")

        recommended_filenames = [get_recommended_filename(Path(file)) for file in duplicates_of_checksum]
        recommended_filenames = {str(file.name) for file in recommended_filenames if file}

        recommended_filename = str(first(recommended_filenames, "N/A"))
        console.print(f"Recommended filenames: {recommended_filename}")


def main():
    DATA_DIR, DBFILE = load_config("mediatool.ini")
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        process_duplicates(session)


if __name__ == "__main__":
    main()
