import logging
import random
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from google_library import get_authorized_session, upload_photos
from logging_setup import logging_setup
from models import Base, File
from utils import load_config

logging_setup()
logger = logging.getLogger(__name__)

google_logger = logging.getLogger("google_library")
google_logger.setLevel(logging.INFO)

urllib3_logger = logging.getLogger("urllib3.connectionpool")
urllib3_logger.setLevel(logging.INFO)


def get_random_images(session: Session, qty=5):
    # It is inefficient to load all the images and then take a random subset, but it works for now.
    statement = select(File).filter_by(filetype="image")
    all_images = [image.name for image in [row.File for row in session.execute(statement).all()]]
    random_images = random.choices(all_images, k=qty)

    return random_images


def main():
    _, DBFILE = load_config("mediatool.ini")
    engine = create_engine(f"sqlite+pysqlite:///{DBFILE}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as sql_session:
        images = get_random_images(sql_session, 5)

    auth_file = Path(".authtoken")
    google_session = get_authorized_session(auth_file)

    upload_photos(google_session, images, "mediatool")


if __name__ == "__main__":
    main()
