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

# todo -- need a better way to add files to an archive rather than naming them one by one
# ! -- have an "add all" option, and it must include sub-directories
# ! -- generate a list of files in the directory where the zip file lives


def create_new():
    """
    Create a new zip file.
    """

    # get a valid filename from the user
    file_name = get_filename()

    # if not file name was entered, return to the menu
    if not file_name:
        return

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

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        # create a new zip file
        with zipfile.ZipFile(file_name, 'w') as f:
            print('\n', file_name, 'created as new archive.\n')
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
    # get a valid file name from user
    file_name = get_filename()

    # open the archive and list all the files in it
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        for ndx, file in enumerate(zip_files):
            print(ndx+1, '. ', file, sep='')

    return file_name


def get_filename():
    """
    Get a filename from user and check the entry for validity.
    """
    while True:
        # get a file name from the user
        file_name = input("\nName of archive: ").strip()

        # if no file name was entered, return to menu
        if not file_name.strip():
            return file_name

        # "escape" any backslashes
        file_name = file_name.replace('\\', '\\\\')

        # check filename for bad characters and bad extension
        prohibited = ['<', '>', '\"', '?', '|', '*']
        if file_name[-4:] != '.zip':
            print('\nFile name is not a zip file.\n')
            continue
        bad_file = False
        for i in file_name:
            if i in prohibited:
                print("\nBad file name: '", i, "' not allowed.", sep='')
                bad_file = True
        if bad_file:
            continue

        break

    # to make thing easier, change the cwd() to the path for this file
    _working_directory_ = os.path.dirname(file_name)
    if _working_directory_:
        os.chdir(_working_directory_)
    file_name = os.path.basename(file_name)

    return file_name


def list_files(file_name):
    """
    Generate a numbered list of all the files in the archive.
    """
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
        file_to_add = input('\nFile name to add to archive: ').strip()

        # if no file name was entered, return to menu
        if not file_to_add:
            break

        # make sure file exists
        if not os.path.isfile(file_to_add):
            print('\nFile name is incorrect\nor file does not exist.\n')
            continue

        # determine if the file already exists in the archive;
        # an archive cannot have duplicate files
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


def extract_file(file_name):
    """
    Extract one or more files from an archive.
    """
    # get a list files in the archive
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_info = f.infolist()

    # num_files is a list of numbers (type:string), one for each file
    num_files = [str(x) for x in range(1, len(zip_info)+1)]
    num_files.append(' ')

    while True:
        # generate a list of files in the archive
        file_name = list_files(file_name)

        # let user choose which files to extract
        print(
            '\nEnter the number of the file to extract,\na comma-separated list of numbers,\nor enter "all" to extract all files.\n')
        choice = input("File number(s) to extract: ")

        # if no choice is made, return to menu
        if not choice.strip():
            return file_name

        # which_files is a list of digits user entered (type:string)
        # if choice="ALL", then generate a list of all file numbers
        if choice.strip().upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(zip_info)+1)]
        else:
            which_files = choice.split(',')

        # confirm that numbers user entered are valid
        for i in which_files:
            if i.strip() not in num_files:
                print('\nPlease use integers within the range: 1-',
                      num_files[-2], sep='')
                print()
                continue

        break

    # convert which_files from a list of strings to a list of integers
    which_files = [int(x) for x in which_files]

    # extract the files the user has chosen to path=file_name
    with zipfile.ZipFile(file_name, 'r') as f:

        zip_files = f.namelist()

        for ndx, file in enumerate(zip_files):
            if ndx+1 in which_files:
                this_file = zip_files[ndx]
                f.extract(this_file, path=file_name[:-4])

    return file_name


def remove_file(file_name):
    """
    To remove a file, create a new archive with the removed file missing. This utility removes only one file at a time.

    To remove a file, create a new archive that holds all the original files except the one targeted for removal. This necessitates creating a new, but "temporary" archive, then renaming it.
    """
    # unlikely, but check if "temporary" directory already exists
    this_path = '_temp_' + file_name[:-4] + '_'
    if os.path.isdir(this_path):
        print('\nCannot remove files from archive, since ',
              this_path, ' directory exists.', sep='')
        return file_name

    # get a list of files in the archive and their total number
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        num_files = len(f.namelist())

    while True:
        # for the user, print a list of files in the archive
        file_name = list_files(file_name)

        # get from the user the file that should be removed
        choice = input("\nEnter the number of file to remove: ")

        # if no file name is entered, return to menu
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

    # get confirmation from the user about the chosen file
    with zipfile.ZipFile(file_name, 'r') as f:
        print()
        for ndx, file in enumerate(zip_files):
            if ndx+1 == choice:
                print(ndx+1, '. ', file, sep='')

    confirmed = input('\nRemove file? (Y/N) ').strip().upper()
    if confirmed == 'Y':
        # extract all the files to "this_path" except
        # the file user has chosen
        with zipfile.ZipFile(file_name, 'r') as f:
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

        try:
            # delete file_name
            os.remove(file_name)
        except:
            print('\nCannot complete file removal.')

        # rename _temp_zipfile_.zip to file_name
        os.rename('_temp_zipfile_.zip', file_name)

        # delete the "temporary" directory
        shutil.rmtree(this_path)

    return file_name


def test_archive(file_name):
    """
    Test the integrity of the archive.
    """
    # open the archive and test it using testzip()
    with zipfile.ZipFile(file_name, 'r') as f:
        tested_files = f.testzip()
        num_files = len(f.infolist())

    if tested_files:
        print('Bad file found:', tested_files)
    else:
        print('\nTested ', num_files, ' files.  ',
              num_files, ' OK.  0 failed.', sep='')

    return file_name


def main_menu():
    """
    Menu for opening a file or creating a new file, which the user can then manipulate via the sub-menu.

    Variables:
        open_file, new_file: whether or not we are opening an existing file or creating a new one
    """
    # store the user's current working directory
    _user_directory_ = os.getcwd()

    # generate the main menu
    while True:
        while True:
            choice = input(
                '\n<O>pen file    <N>ew file\nQ>uit\n\nChoice: ').upper()
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

    # change back to original user directory
    os.chdir(_user_directory_)


def sub_menu(open_file, new_file):
    """
    Menu of actions on the file that the user has opened or created.
    """
    if open_file:
        file_name = get_filename()
    else:
        file_name = create_new()

    # go back to the main menu if no file name is entered
    if not file_name:
        return

    # use the following to delimit output from sequential commands
    sp1 = '\n====================================================\n' \
        + os.getcwd() + '\\' + file_name + '\n' \
        + '===================================================='
    print(sp1)

    file_name = list_files(file_name)

    while True:
        # generate the sub-menu
        print('\n<L>ist    <A>dd   <E>xtract\n<R>emove  <T>est  <M>ain menu')
        user_choice = input('\nChoose an action: ').strip().upper()

        if user_choice not in 'LAERTM':
            print('\n"', user_choice, '" ', 'is an invalid action.', sep='')
            continue

        print(sp1)

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
