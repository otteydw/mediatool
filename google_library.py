# This code taken and modified from https://github.com/eshmu/gphotos-upload/
import json
import logging
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from logging_setup import logging_setup

logging_setup()
logger = logging.getLogger(__name__)

debug = True
if debug:
    logger.setLevel(logging.DEBUG)


def save_cred(cred, auth_file):
    cred_dict = {
        "token": cred.token,
        "refresh_token": cred.refresh_token,
        "id_token": cred.id_token,
        "scopes": cred.scopes,
        "token_uri": cred.token_uri,
        "client_id": cred.client_id,
        "client_secret": cred.client_secret,
    }

    with open(auth_file, "w") as f:
        print(json.dumps(cred_dict), file=f)


def auth(scopes):
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=scopes)

    credentials = flow.run_local_server(
        host="localhost",
        port=8080,
        authorization_prompt_message="",
        success_message="The auth flow is complete; you may close this window.",
        open_browser=True,
    )

    return credentials


def get_authorized_session(auth_token_file):
    scopes = [
        "https://www.googleapis.com/auth/photoslibrary",
        "https://www.googleapis.com/auth/photoslibrary.sharing",
    ]

    cred = None

    if auth_token_file:
        try:
            cred = Credentials.from_authorized_user_file(auth_token_file, scopes)
        except OSError as err:
            logger.debug("Error opening auth token file - {0}".format(err))
        except ValueError:
            logger.debug("Error loading auth tokens - Incorrect format")

    if not cred:
        cred = auth(scopes)

    session = AuthorizedSession(cred)

    if auth_token_file:
        try:
            save_cred(cred, auth_token_file)
        except OSError as err:
            logger.debug("Could not save auth tokens - {0}".format(err))

    return session


def getAlbums(session, appCreatedOnly=False):
    params = {"excludeNonAppCreatedData": appCreatedOnly}

    while True:
        albums = session.get("https://photoslibrary.googleapis.com/v1/albums", params=params).json()

        logger.debug("Server response: {}".format(albums))

        if "albums" in albums:
            for a in albums["albums"]:
                yield a

            if "nextPageToken" in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                return

        else:
            return


def create_or_retrieve_album(session, album_title):
    # Find albums created by this app to see if one matches album_title

    # The appCreatedOnly=True does not seem to be finding the previous album, so setting to False for now.
    for a in getAlbums(session, False):
        if a["title"].lower() == album_title.lower():
            album_id = a["id"]
            logger.info("Uploading into EXISTING photo album -- '{0}'".format(album_title))
            return album_id

    # No matches, create new album

    create_album_body = json.dumps({"album": {"title": album_title}})
    # print(create_album_body)
    response = session.post("https://photoslibrary.googleapis.com/v1/albums", create_album_body).json()

    logger.debug(f"Server response: {response}")

    if "id" in response:
        logger.info(f"Uploading into NEW photo album -- '{album_title}'")
        return response["id"]
    else:
        logger.error(f"Could not find or create photo album '{album_title}'. Server Response: {response}")
        return None


def upload_photos(session, photo_file_list, album_name):
    album_id = create_or_retrieve_album(session, album_name) if album_name else None

    # interrupt upload if an upload was requested but could not be created
    if album_name and not album_id:
        return

    session.headers["Content-type"] = "application/octet-stream"
    session.headers["X-Goog-Upload-Protocol"] = "raw"

    for photo_file_name in photo_file_list:
        try:
            with open(photo_file_name, mode="rb") as photo_file:
                photo_bytes = photo_file.read()
        except OSError as err:
            logger.error(f"Could not read file '{photo_file_name}' -- {err}")
            continue

        session.headers["X-Goog-Upload-File-Name"] = os.path.basename(photo_file_name)

        logger.info("Uploading photo -- '{}'".format(photo_file_name))

        upload_token = session.post("https://photoslibrary.googleapis.com/v1/uploads", photo_bytes)

        if (upload_token.status_code == 200) and (upload_token.content):
            create_body = json.dumps(
                {
                    "albumId": album_id,
                    "newMediaItems": [
                        {
                            "description": "",
                            "simpleMediaItem": {"uploadToken": upload_token.content.decode()},
                        }
                    ],
                },
                indent=4,
            )

            response = session.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                create_body,
            ).json()

            logger.debug(f"Server response: {response}")

            if "newMediaItemResults" in response:
                status = response["newMediaItemResults"][0]["status"]
                if status.get("code") and (status.get("code") > 0):
                    logger.error(
                        f"Could not add '{os.path.basename(photo_file_name)}' to library -- {status["message"]}"
                    )
                else:
                    logger.info(f"Added '{os.path.basename(photo_file_name)}' to library and album '{album_name}'")
            else:
                logger.error(
                    f"Could not add '{os.path.basename(photo_file_name)}' to library. Server Response -- {response}"
                )

        else:
            logger.error(f"Could not upload '{os.path.basename(photo_file_name)}'. Server Response - {upload_token}")

    try:
        del session.headers["Content-type"]
        del session.headers["X-Goog-Upload-Protocol"]
        del session.headers["X-Goog-Upload-File-Name"]
    except KeyError:
        pass
