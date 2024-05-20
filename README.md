
# Catalog

The catalog application scans a directory and records all the media files (images and videos) and metadata (size, checksum) about them into a local database.

## Usage

```shell
python3 ./catalog.py
```

# Duplicate Finder

The dupefinder application uses the catalog previously created to report on which files share the same checksum and are therefore duplicates.

## Usage

```shell
python3 ./dupefinder.py
```

# Configuration

The tools utilize a common configuration file named `mediatool.ini`.

```ini
[mediatool]
data_dir = /path/to/media/folder
db_file = /path/to/database.db
```

# Quick Date

A very simple script that displays the datestamp from an image.

```shell
python3 ./quick_date.py /path/to/image.jpg
```

# Requirements

To run the programs, it is recommended to create a python virtual environment. Use pyenv or whatever tool you prefer to do that.

Then install the requirements:

```shell
pip3 install -r requirements.txt
```

## Developer Requirements

If you would like to manage the database or run the tests, install the developer requirements:

```shell
pip3 install -r requirements-dev.txt
```

This repository also uses pre-commit hooks that are installed with pre-commit:

```shell
pipx install pre-commit
pre-commit install
```

# Alembic

```shell
alembic revision --autogenerate -m "Add filetype column"
alembic upgrade head
```

# Logging configuration

Logging configuration copied from [here](https://gist.github.com/panamantis/5797dda98b1fa6fab2f739a7aacc5e9d).
