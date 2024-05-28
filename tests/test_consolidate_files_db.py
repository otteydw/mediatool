from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db_utils import consolidate_files_db
from models import Base, File

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.joinpath("testdata")


@pytest.mark.datafiles(DATA_DIR)
def test_consolidate_files_db(datafiles: Path):
    DBFILE = datafiles.joinpath("dingo.db")
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    sha256 = "3dcbca269c67a28a75c25d8e04b97172379af92eb23c764123adbd6271476cd0"
    with Session(engine) as session:
        duplicates = session.query(File).filter(File.sha256 == sha256).all()
        duplicates_as_paths = [Path(file.name) for file in duplicates]
        path_to_keep = duplicates_as_paths[0]

        removed_count = consolidate_files_db(session, duplicates_as_paths, path_to_keep)
        assert removed_count == len(duplicates) - 1

        remaining = session.query(File).filter(File.sha256 == sha256).all()
        assert len(remaining) == 1
