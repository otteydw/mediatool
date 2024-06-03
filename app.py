from ast import literal_eval
from pathlib import Path

import sqlalchemy as sa
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

from db_utils import consolidate_files_db
from models import File
from utils import consolidate_files, load_config


class Config:
    _, DBFILE = load_config("mediatool.ini")
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

    if page > duplicate_checksums.total:
        page = duplicate_checksums.total
        return redirect(url_for(request.endpoint, page=page))
    elif page < 1:
        page = 1
        return redirect(url_for(request.endpoint, page=page))

    # Since we paginate 1 item per "page", we only care about that first item.
    checksum = list(duplicate_checksums)[0]

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

    all_files = [str(file) for file in duplicates_of_checksum]

    return render_template(
        "duplicates.html",
        duplicates_of_checksum=duplicates_of_checksum,
        next_url=next_url,
        prev_url=prev_url,
        checksum=checksum,
        current=duplicate_checksums.page,
        total=duplicate_checksums.total,
        all_files=all_files,
    )


@app.route("/process_duplicate", methods=["POST"])
def process_duplicate():
    rq = request.form
    page = int(rq.get("page", "None"))
    file_to_keep = Path(rq.get("keep_file", "None"))
    all_files = [Path(file) for file in literal_eval(rq.get("all_files", "None"))]

    consolidate_files(all_files, file_to_keep)
    consolidate_files_db(db.session, all_files, file_to_keep)
    # return f"We kept {file_to_keep}<br><br>All files {all_files}"
    return redirect(url_for("process_duplicates", page=page))
