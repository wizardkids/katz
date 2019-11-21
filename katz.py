"""
katz.py

Richard E. Rawson
2019-11-21

Program Description:
zip archiving program
"""

import zipfile
from pprint import pprint


def create_new():
    """
    Create a new archive, given a file name for the archive.
    """
    pass


def open_archive():
    """
    Open an archive and list the files in the archive
    List all the files in a zip archive:
        1. pomodoro_I.py
        2. pomodoro_II.py
        3. Windows Notify.wav
    """
    f = input("Name of archive to open: ")
    prohibited = ['<', '>', ':', '\"', '?', '\\', '/', '|', '*']

    for i in prohibited:
        print(i)


def add_file():
    """
    Add one or more files to an existing archive:
        1. pomodoro_I.py
        2. pomodoro_II.py
        3. Windows Notify.wav

    becomes:
        1. alert.txt
        2. pomodoro_I.py
        3. pomodoro_II.py
        4. Windows Notify.wav
    """
    pass


def remove_file():
    """
    Remove a single file from an archive:
        1. pomodoro_I.py
        2. pomodoro_II.py
        3. Windows Notify.wav

    becomes:
        1. pomodoro_I.py
        2. Windows Notify.wav
    """
    pass


def test_archive():
    """
    Test the integrity of the archive.
    """
    pass


def extract_file():
    """
    Extract one or more files from an archive.
    """
    pass


if __name__ == '__main__':
    open_archive()
