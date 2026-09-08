import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python_scripts", "functions"))

from ensure_folder import ensure_folder


def test_creates_folder_when_missing(tmp_path):
    folder_path = str(tmp_path)
    folder_name = "new_folder"

    ensure_folder(folder_path, folder_name)

    assert os.path.isdir(os.path.join(folder_path, folder_name))


def test_does_nothing_when_folder_exists(tmp_path):
    folder_path = str(tmp_path)
    folder_name = "existing_folder"
    target = os.path.join(folder_path, folder_name)
    os.makedirs(target)

    ensure_folder(folder_path, folder_name)

    assert os.path.isdir(target)


def test_creates_nested_folder_path(tmp_path):
    folder_path = str(tmp_path)
    folder_name = os.path.join("level1", "level2")

    ensure_folder(folder_path, folder_name)

    assert os.path.isdir(os.path.join(folder_path, folder_name))