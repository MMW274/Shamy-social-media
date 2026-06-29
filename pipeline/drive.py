"""Google Drive client — list a folder, download files, move files between folders."""
from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]

DEFAULT_TOKEN_PATH = Path("token.json")
DEFAULT_CREDS_PATH = Path("credentials.json")


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    folder: str
    mime_type: str


def authorize(
    creds_path: Path = DEFAULT_CREDS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
):
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def list_folder_recursive(service, root_folder_id: str) -> list[DriveFile]:
    """Walk subfolders one level (01_safe_amy, 01_safe_sheldon, etc.) and list files."""
    folders = _list_subfolders(service, root_folder_id)
    files: list[DriveFile] = []
    for f_id, f_name in folders.items():
        page_token = None
        while True:
            resp = service.files().list(
                q=f"'{f_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                pageSize=200,
            ).execute()
            for item in resp.get("files", []):
                files.append(
                    DriveFile(
                        id=item["id"],
                        name=item["name"],
                        folder=f_name,
                        mime_type=item["mimeType"],
                    )
                )
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    return files


def _list_subfolders(service, parent_id: str) -> dict[str, str]:
    resp = service.files().list(
        q=f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)",
        pageSize=100,
    ).execute()
    return {item["id"]: item["name"] for item in resp.get("files", [])}


def download_file(service, file_id: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with dest.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def move_file(service, file_id: str, new_parent_folder_id: str) -> None:
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    service.files().update(
        fileId=file_id,
        addParents=new_parent_folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()
