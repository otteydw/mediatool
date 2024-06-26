import logging
from pathlib import Path, PosixPath
from typing import List

from sqlalchemy.orm import Session

from models import File

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def consolidate_files_db(
    session: Session, paths_to_consolidate: List[Path | PosixPath], target_path: Path, dry_run: bool = False
) -> int:
    if target_path in paths_to_consolidate:
        # Create paths_to_remove by removing target path from paths_to_consolidate
        paths_to_remove = set(paths_to_consolidate) - set([target_path])
        logger.debug(f"T in P: Paths to remove = {paths_to_remove}")
    else:
        logger.debug(f"T not in P: Paths to consolidate = {paths_to_consolidate}")

        temp_source = paths_to_consolidate.pop()
        if not dry_run:
            temp_source.rename(target_path)
        paths_to_remove = paths_to_consolidate
        logger.debug(f"T not in P: Paths to remove = {paths_to_remove}")

    # Delete paths_to_remove
    total_files_deleted = 0
    for path in paths_to_remove:
        logger.debug(f"Deleting {str(path)} from database.")
        if not dry_run:
            session.query(File).filter(File.name == str(path)).delete()
        total_files_deleted += 1

    session.commit()
    return total_files_deleted
