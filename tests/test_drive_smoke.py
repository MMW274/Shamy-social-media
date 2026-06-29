import os
from pathlib import Path
import pytest

from pipeline.drive import authorize, list_folder_recursive


@pytest.mark.skipif(
    not Path("credentials.json").exists() or not os.getenv("DRIVE_ROOT_FOLDER_ID"),
    reason="Drive credentials not set up locally",
)
def test_can_list_root_folder():
    svc = authorize()
    files = list_folder_recursive(svc, os.environ["DRIVE_ROOT_FOLDER_ID"])
    folders = {f.folder for f in files}
    assert any(name.startswith("01_safe") for name in folders), folders
