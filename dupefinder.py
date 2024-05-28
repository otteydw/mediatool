import logging
from pathlib import Path

from more_itertools import first
from rich.console import Console
from rich.prompt import IntPrompt
from rich.table import Table
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from db_utils import consolidate_files_db
from logging_setup import logging_setup
from models import Base, File
from utils import consolidate_files, get_recommended_filename, load_config

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

    for checksum in duplicate_checksums:
        statement = select(File).filter_by(sha256=checksum)
        duplicates_of_checksum = [
            Path(dupe_set.name) for dupe_set in [row.File for row in session.execute(statement).all()]
        ]

        number_of_files_found = len(duplicates_of_checksum)
        table = Table(title=f"Duplicates of {checksum}")
        table.add_column("")
        table.add_column("Parent")
        table.add_column("Filename")
        for file_number, file in enumerate(duplicates_of_checksum, start=1):
            parent = str(file.parent)
            name = str(file.name)
            table.add_row(str(file_number), parent, name)
        console.print(table)

        while True:
            keep_number = IntPrompt.ask("Which one to keep?", default=1)
            if keep_number >= 1 and keep_number <= number_of_files_found:
                break

        file_to_keep = duplicates_of_checksum[keep_number - 1]
        console.print(f"We want to keep file {keep_number} which is {file_to_keep}")

        # For now we're just going to display a single recommended filename, but not do anything with it.
        recommended_filenames = [get_recommended_filename(path) for path in duplicates_of_checksum]
        recommended_filenames = {str(file.name) for file in recommended_filenames if file}
        recommended_filename = str(first(recommended_filenames, "N/A"))
        console.print(f"Recommended filenames: {recommended_filename}")

        consolidate_files(duplicates_of_checksum, file_to_keep)
        consolidate_files_db(session, duplicates_of_checksum, file_to_keep)


def main():
    DATA_DIR, DBFILE = load_config("mediatool.ini")
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        process_duplicates(session)


if __name__ == "__main__":
    main()
