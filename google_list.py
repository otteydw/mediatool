import logging
from pathlib import Path
from pprint import pprint

from google_library import get_authorized_session, get_photos_from_album
from logging_setup import logging_setup

logging_setup()
logger = logging.getLogger(__name__)

google_logger = logging.getLogger("google_library")
google_logger.setLevel(logging.INFO)

urllib3_logger = logging.getLogger("urllib3.connectionpool")
urllib3_logger.setLevel(logging.INFO)


def main():

    auth_file = Path(".authtoken")
    google_session = get_authorized_session(auth_file)

    for photo in get_photos_from_album(google_session, "mediatool"):
        pprint(photo)
        print()


if __name__ == "__main__":
    main()
