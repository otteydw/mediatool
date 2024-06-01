from pathlib import Path

import sqlalchemy as sa
from flask import Flask, render_template, request, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

from models import File
from utils import load_config


class Config:
    DATA_DIR, DBFILE = load_config("mediatool.ini")
    SQLALCHEMY_DATABASE_URI = f"sqlite+pysqlite:///{DBFILE}"


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


@app.route("/pics/<path:filename>")
def pics(filename):
    return send_from_directory("/", filename, as_attachment=False)


@app.route("/dupes")
def process_duplicates(page_number=1):

    page = request.args.get("page", page_number, type=int)
    query = (
        sa.select(File.sha256, sa.func.count(File.sha256).label("qty"))
        .group_by(File.sha256)
        .having(sa.func.count(File.sha256) > 1)
    )

    duplicate_checksums = db.paginate(query, page=page, per_page=1, error_out=False)
    print(duplicate_checksums)

    for checksum in duplicate_checksums:
        statement = select(File).filter_by(sha256=checksum)
        duplicates_of_checksum = [
            Path(dupe_set.name) for dupe_set in [row.File for row in db.session.execute(statement).all()]
        ]

        prev_url = (
            url_for("process_duplicates", page=duplicate_checksums.prev_num) if duplicate_checksums.has_prev else None
        )
        next_url = (
            url_for("process_duplicates", page=duplicate_checksums.next_num) if duplicate_checksums.has_next else None
        )

        return render_template(
            "duplicates.html",
            duplicates_of_checksum=duplicates_of_checksum,
            page=page,
            request=request,
            next_url=next_url,
            prev_url=prev_url,
        )
