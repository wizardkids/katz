"""
katz.py

Richard E. Rawson
2019-11-21

Program Description:
zip archiving program
"""

import os
import shutil
import zipfile
from pprint import pprint

# todo -- Review each function to see if it can be shortened


def create_new():
    """
    Create a new zip file.
    """

    file_name = get_filename()

    try:
        # if file already exists, issue warning
        with zipfile.ZipFile(file_name, 'r') as f:
            msg = '\n' + file_name + ' already exists. Overwrite? '
            overwrite = input(msg).upper()
            if overwrite == 'Y':
                with zipfile.ZipFile(file_name, 'w') as f:
                    print('\n', file_name, 'created as new archive.\n')
            else:
                print(file_name, 'not created.\n')
    except FileNotFoundError:
        # create a new zip file
        with zipfile.ZipFile(file_name) as f:
            print('\n', file_name, 'created as new archive.\n')
    return file_name


def get_filename():
    """
    Get a filename from user and check the entry for validity.
    """
    while True:
        print()
        file_name = input("Name of archive: ").strip()
        if not file_name.strip():
            break
        prohibited = ['<', '>', ':', '\"', '?', '\\', '/', '|', '*']

        # check filename for bad characters and bad form
        if file_name[-4:] != '.zip':
            print('\nNot a zip file.\n')
            continue
        for i in file_name:
            if i in prohibited:
                print('\nBad file name', i, 'not allowed.')
                continue
        break
    return file_name


def open_archive():
    """
    Open an archive and list the files in the archive
    List all the files in a zip archive:
        1. pomodoro_I.py
        2. pomodoro_II.py
        3. Windows Notify.wav
    """
    """
    modes:
        'x' -- to exclusively create and write a new "file". If "file" already exists, a FileExistsError will be raised.
        'r' -- read an existing "file"
        'a' -- if "file" refers to an existing ZIP file, then additional files are added to it. If "file" does not refer to a ZIP file, then a new ZIP archive is appended to the file.
    """
    print()
    file_name = get_filename()

    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        for ndx, file in enumerate(zip_files):
            print(ndx+1, '. ', file, sep='')
    return file_name


def add_file(file_name):
    """
    Add a file to an existing archive.
    """
    while True:
        # get a file name to add
        file_to_add = input('\nFile name: ').strip()
        if not file_to_add:
            break
        try:
            with open(file_to_add):
                pass
        except:
            print('\nFile name is bad or file does not exist.\n')

        # determine if the file exists on disk
        try:
            with open(file_to_add, 'r') as f:
                pass
        except:
            print('\nFile does not exist.')
            break

        # determine if the file already exists in the archive
        with zipfile.ZipFile(file_name) as f:
            zip_files = f.namelist()

        if file_to_add in zip_files:
            print(
                '\nFile already exists in archive.\nRemove this file before adding a new version.')
            break
        else:
            with zipfile.ZipFile(file_name, 'a') as f:
                f.write(file_to_add)
    return file_name


def remove_file(file_name):
    """
    To remove a file, create a new archive with the removed file missing. This utility removes only one file at a time.
    """
    # check to see if the "temporary" directory already exists
    if os.path.isdir(file_name[:-4]):
        print('\nCannot remove files from archive, since ',
              file_name[:-4], ' directory exists.', sep='')
        return file_name

    # for the user, print a list of files in the archive
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        num_files = len(zip_files)
        for ndx, file in enumerate(zip_files):
            print(ndx+1, '. ', file, sep='')

    # get from the user the file that should be removed
    while True:
        file_name = list_files(file_name)
        choice = input("\nEnter the number of file to remove: ")

        if not choice.strip():
            return file_name

        # make sure user entered a valid integer
        try:
            choice = int(choice)
            if choice <= num_files:
                break
        except:
            print('\nEnter only an integer, in range 1-',
                  num_files, '.\n', sep='')
            continue

    # print a list of files that the user has chosen, for confirmation
    with zipfile.ZipFile(file_name, 'r') as f:
        print()
        for ndx, file in enumerate(zip_files):
            if ndx+1 == choice:
                print(ndx+1, '. ', file, sep='')

    confirmed = input('\nRemove file? ').upper()
    if confirmed == 'Y':
        # extract all the files except the file user has chosen
        with zipfile.ZipFile(file_name, 'r') as f:
            zip_files = f.namelist()
            this_path = '_' + file_name[:-4] + '_'
            for ndx, file in enumerate(zip_files):
                if ndx+1 != choice:
                    this_file = zip_files[ndx]
                    f.extract(this_file, path=this_path)

        current_directory = os.getcwd()
        rel_dir = os.path.relpath(current_directory, '')

        # add all the extracted files to _temp_zipfile_.zip
        with zipfile.ZipFile('_temp_zipfile_.zip', 'w') as f:
            os.chdir(this_path)
            # Iterate over all the files in directory
            for folderName, subfolders, filenames in os.walk(rel_dir):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # Add file to zip
                    f.write(filePath)

        # change back to the directory holding file_name
        os.chdir(current_directory)

        # delete file_name
        os.remove(file_name)

        # rename _temp_zipfile_.zip to file_name
        os.rename('_temp_zipfile_.zip', file_name)

        # delete the "temporary" directory
        shutil.rmtree(this_path)
    return file_name


def list_files(file_name):
    """
    Generate a list of all the files in the archive.
    """
    print()
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        for ndx, file in enumerate(zip_files):
            print(ndx+1, '. ', file, sep='')

    return file_name


def extract_file(file_name):
    """
    Extract one or more files from an archive.
    """
    # get a list of the numbers for the files in the archive
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_info = f.infolist()
    num_files = [str(x) for x in range(1, len(zip_info)+1)]
    num_files.append(' ')

    # allow user to choose which file(s) to extract
    while True:
        file_name = list_files(file_name)

        print(
            "\nEnter the number of file to extract,\na comma-separated list of numbers,\nor enter 'all' to extract all files.\n")
        choice = input("Choice: ")

        if not choice.strip():
            return file_name

        which_files = [str(x) for x in range(
            1, len(zip_info)+1)] if choice.strip().upper() == 'ALL' else choice.split(',')

        for i in which_files:
            if i.strip() not in num_files:
                print('\nPlease use integers within the range: 1-',
                      num_files[-2], sep='')
                print()
                continue

        break

    which_files = [int(x) for x in which_files]

    # extract the files the user has chosen to path=file_name
    with zipfile.ZipFile(file_name, 'r') as f:

        zip_files = f.namelist()

        for ndx, file in enumerate(zip_files):
            if ndx+1 in which_files:
                this_file = zip_files[ndx]
                f.extract(this_file, path=file_name[:-4])

    return file_name


def test_archive(file_name):
    """
    Test the integrity of the archive.
    """
    with zipfile.ZipFile(file_name, 'r') as f:
        tested_files = f.testzip()
        num_files = len(f.infolist())

    if tested_files:
        print('Bad file found:', tested_files)
    else:
        print('\nTested ', num_files, ' files.  ',
              num_files, ' OK  0 failed', sep='')

    return file_name


def main_menu():
    """
    Menu for opening a file or creating a new file, which the user can then manipulate via the sub-menu.
    """
    while True:
        while True:
            print()
            print('<O>pen file    <N>ew file\nQ>uit\n')
            choice = input('Choice: ').upper()
            if choice in 'ONQ':
                break
            else:
                print('\nEnter only "O", "N", or "Q".')
                continue

        if choice == 'O':
            open_file, new_file = True, False
            sub_menu(open_file, new_file)

        elif choice == 'N':
            open_file, new_file = False, True
            sub_menu(open_file, new_file)

        elif choice == 'Q':
            break


def sub_menu(open_file, new_file):
    """
    Menu of actions on the file that the user has opened or created.
    """
    if open_file:
        file_name = get_filename()
    else:
        file_name = create_new()

    if not file_name:
        return

    file_name = list_files(file_name)

    while True:
        print()
        print('<L>ist    <A>dd   <E>xtract\n<R>emove  <T>est  <M>ain menu')
        print()
        user_choice = input('Choose an action: ').strip().upper()

        if user_choice not in 'LAERTM':
            print('\n"', user_choice, '" ', 'is an invalid action.', sep='')
            continue

        # actions to take on choosing a menu item
        if user_choice == 'L':
            file_name = list_files(file_name)

        elif user_choice == 'A':
            file_name = add_file(file_name)

        elif user_choice == 'E':
            file_name = extract_file(file_name)

        elif user_choice == 'R':
            file_name = remove_file(file_name)

        elif user_choice == 'T':
            file_name = test_archive(file_name)

        else:
            return

    return


if __name__ == '__main__':
    main_menu()
