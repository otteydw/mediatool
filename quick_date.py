from pathlib import Path

import click

from utils import get_datestamp


@click.command()
@click.argument("pathname")
def quick_date(pathname):
    pathname = Path(pathname)
    # pathname = Path("/Volumes/media/Pictures/2021/2022-10-14_from_cam_card/IMG_2943.JPG")
    datestamp = get_datestamp(pathname)
    print(datestamp)


if __name__ == "__main__":
    quick_date()
