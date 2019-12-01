"""
katz.py

Richard E. Rawson
2019-11-21

Program Description:
command-line zip archiving utility
    1. list all files, including files in subfolders, within the archive
    2. add one, many, or all files, optionally including subfolders
    3. extract one, many, or all files from the archive, including subfolders
    4. remove one file at a time from the archive
    5. test the integrity of the archive
"""

import glob
import os
import shutil
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path

# todo -- version 2, add support for other archiving formats, including tar and gzip

# todo -- version 3: add support for importing into other scripts so that downloaded archives are extracted automatically

# declare global variables
dsh, slsh = '=', '/'


def create_new():
    """
    Create a new zip file.
    """
    # get a valid filename from the user
    full_path, file_name = get_filename()

    # if no file name was entered, return to the menu
    if not file_name:
        return '', ''

    # if file already exists, issue "overwrite" warning
    try:
        with zipfile.ZipFile(file_name, 'r') as f:
            msg = '\n' + file_name + ' already exists. Overwrite? '
            overwrite = input(msg).upper()

            if overwrite == 'Y':
                with zipfile.ZipFile(file_name, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', file_name, 'created as new archive.\n')
                return full_path, file_name

            else:
                print(file_name, 'not created.\n')
                return '', ''

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        with zipfile.ZipFile(file_name, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            print('\n', file_name, 'created as new archive.\n')
        return full_path, file_name


def open_archive():
    """
    Open an archive and list the files in the archive.
    """
    # get a file name from user
    full_path, file_name = get_filename()

    # if no file_name was entered, return to menu
    if not file_name:
        return '', ''

    # sort out possible errors in file_name
    try:
        with zipfile.ZipFile(file_name, 'r') as f:
            pass
    except FileNotFoundError:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        print('\nFile not found.')
        return '', ''
    except OSError:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        print('\nInvalid file name.')
        return '', ''
    except zipfile.BadZipFile:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        print('\nFile is not a zip file.')
        return '', ''
    except:
        print('\nEncountered an unpredicable error.')
        return '', ''

    return full_path, file_name


def get_filename():
    """
    Get a filename from user and check the entry for validity.
    """
    while True:
        # get a file name from the user
        full_path = input("\nName of archive: ").strip()
        file_name = Path(full_path).name

        # if no file name was entered, return to menu
        if not full_path.strip():
            return '', ''

        # zip files don't require a .zip extension, but it's a bad idea
        if file_name[-4:] != '.zip':
            print('\nMust enter a ".zip" extension.')
            continue

        break

    # change the cwd() to the path for this file
    try:
        _working_directory_ = os.path.dirname(full_path)
        if _working_directory_:
            os.chdir(_working_directory_)
    except:
        print('\nPath or filename is invalid.')
        return '', ''

    return full_path, file_name


def list_files(full_path, file_name):
    """
    Generate a numbered list of all the files in the archive.
    """
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()

        # if the first item in namelist() is a directory, get the name
        # else... use root/ as the starting directory
        try:
            if '/' in zip_files[0]:
                slash_location = zip_files[0].find('/')
                current_directory = zip_files[0][:slash_location]
            else:
                current_directory = 'root/'
        except:
            current_directory = 'root/'

        print(current_directory)

        # print a list of files in the archive
        for ndx, file in enumerate(zip_files):

            # when the directory changes, print it (left-justified)
            if current_directory != os.path.dirname(file):
                current_directory = os.path.dirname(file)
                if current_directory:
                    print(current_directory)
                else:
                    print('root/')

            # print files indented 5 spaces
            this_directory, this_file = os.path.split(file)
            print(' '*5, ndx+1, '. ', this_file, sep='')

    return full_path, file_name


def add_file(full_path, file_name):
    """
    Add one, many, or all files from the user-designated folder, and optionally include subfolders of that folder. Uses various methods for choosing files to add, optimized for speed of selection.
    """
    glob_it = False  # flag needed because which_files is treated differently
    msg = 'FILES IN THE CURRENT DIRECTORY'

    # preserve absolute and relative paths to current directory
    current_directory = os.getcwd()
    rel_dir = os.path.relpath(current_directory, '')

    # ==================================================
    # GENERATE A LIST OF ALL FILES IN THE USER-CHOSEN FOLDER
    # ==================================================

    # get directory containing files that you want to add
    while True:
        print('\nEnter "." to use current directory.')
        dir = input("Directory containing files to add: ").strip()

        # if user enters nothing, return to the menu
        if not dir:
            return full_path, file_name

        if dir == '.':
            dir = current_directory

        if not os.path.exists(dir):
            print('\nDirectory does not exist. Re-enter.')
            continue
        else:
            subs = input('Include subdirectories (Y/N): ').strip().upper()
            subs = True if subs == 'Y' else False
            break

    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

    # print a list of eligible files in the chosen directory and subdirectories
    if subs:
        # Iterate over all the files in the root directory
        file_list, file_cnt = [], 1
        for folderName, subfolders, filenames in os.walk(rel_dir):
            for filename in filenames:
                # create complete filepath of file in directory
                filePath = os.path.relpath(os.path.join(folderName, filename))
                if file_name[0] != '.':
                    file_list.append(filePath)
                    print(file_cnt, '. ', filePath, sep='')
                file_cnt += 1

    # print a list of all files in just the chosen directory
    else:
        file_list = [f for f in os.listdir(
            dir) if os.path.isfile(os.path.join(dir, f))]
        for ndx, file in enumerate(file_list):
            print(ndx+1, '. ', file, sep='')

    # ==================================================
    # GET A LIST OF THE FILES THAT THE USER WANTS TO ADD
    # ==================================================

    while True:
        # let user choose which file(s) to add
        # example user input: 1, 3-5, 28, 52-68, 70 or *.t?t
        print('\nEnter:\n(1) a comma-separated combination of:\n    -- the number of the file(s) to add\n    -- a hyphenated list of sequential numbers\n(2) enter "all" to add all files\n(3) use wildcard characters (*/?) to designate files')

        choice = input("File(s) to add: ").strip()

        # if nothing is entered, return to menu
        if not choice:
            return full_path, file_name

        # which_files is a list of digits user entered (type:string)
        # else if choice="ALL", then generate a list of all file numbers
        if choice.upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(file_list)+1)]

        # see https://pymotw.com/2/glob/
        elif '*' in choice or '?' in choice:
            # print('\nWildcards not functional at present.')
            glob_it, which_files = True, []
            rel_dir = os.path.relpath('.', '')
            if subs:
                for folderName, subfolders, filenames in os.walk(rel_dir):
                    f = os.path.join(folderName, choice)
                    for name in glob.glob(f):
                        if name != os.path.join(folderName, file_name):
                            which_files.append(name)
                            print(name)
            else:
                for name in glob.glob(choice):
                    if name != os.path.join(folderName, file_name):
                        which_files.append(name)
                        print(name)

        # extract all the file numbers from the user's list:
        else:
            # split user's entry at commas
            # list now contains integers &/or ranges
            selected_files = choice.split(',')

            which_files = []
            for i in selected_files:
                # treating ranges, i.e., 2-8
                if '-' in i:
                    r = i.split('-')
                    try:
                        n = [str(x) for x in range(int(r[0]), (int(r[1]))+1)]
                        for x in n:
                            which_files.append(x)
                    except:
                        print(
                            '\nInvalid range of numbers was excluded. Did you comma-separate values?')
                # treating all other single digits
                else:
                    try:
                        n = int(i)
                        which_files.append(str(n))
                    except:
                        print(
                            '\nInvalid number(s) excluded. Did you comma-separate values?')
        break

    # ==================================================
    # WRITE THE SELECTED FILES INTO THE ARCHIVE
    # ==================================================

    if not glob_it:
        # which_files contains all of the integers for the selected files
        which_files = [int(x) for x in which_files]

        # for each integer in which_files, add the corresponding file to archive
        for ndx, file in enumerate(file_list):
            if file != file_name and ndx+1 in which_files:
                print(file)
                write_one_file(file, file_name)
    else:
        for file in which_files:
            write_one_file(file, file_name)

    return full_path, file_name


def write_one_file(file_to_add, file_name):
    # determine if the file already exists in the archive;
    # an archive cannot have duplicate files
    with zipfile.ZipFile(file_name) as f:
        zip_files = f.namelist()

    # add the compressed file if it does not exist in archive already
    if file_to_add not in zip_files:
        with zipfile.ZipFile(file_name, 'a', compression=zipfile.ZIP_DEFLATED) as f:
            f.write(file_to_add)

    # zipfile doesn't update files and cannot add duplicate files
    # print message if file already resides in archive
    else:
        print('\n', file_to_add,
              ' already exists in archive.\nRemove this file before adding a new version.', sep='')
    return


def extract_file(full_path, file_name):
    """
    Extract one or more files from an archive.
    """
    # get a list files in the archive and number them
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_info = f.infolist()
        num_files = [str(x) for x in range(1, len(zip_info)+1)]
        num_files.append(' ')

    while True:
        # print a list of files in the archive
        full_path, file_name = list_files(full_path, file_name)

        # let user choose which file(s) to extract
        # sample user input: 1, 3-5, 28, 52-68, 70
        print(
            '\nEnter a comma-separated combination of:\n  -- the number of the file(s) to extract\n  -- a hyphenated list of sequential numbers\n  -- or enter "all" to extract all files\n')
        choice = input("File number(s) to extract: ")

        # if no choice is made, return to menu
        if not choice.strip():
            return full_path, file_name

        # which_files is a list of user-entered digits (type:string)
        # if choice="ALL", then generate a list of all file numbers
        if choice.strip().upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(zip_info)+1)]

        else:
            # extract all the file numbers from the user's list:
            selected_files = choice.split(',')
            which_files = []
            for i in selected_files:
                # treating ranges, i.e., 2-8
                if '-' in i:
                    r = i.split('-')
                    try:
                        n = [str(x) for x in range(int(r[0]), (int(r[1]))+1)]
                        for x in n:
                            which_files.append(x)
                    except:
                        print(
                            '\nInvalid range of numbers was excluded. Did you comma-separate values?')
                # treating all other single digits
                else:
                    try:
                        n = int(i)
                        which_files.append(str(n))
                    except:
                        print(
                            '\nInvalid number(s) excluded. Did you comma-separate values?')
        break

    # convert which_files from a list of strings to a list of integers
    which_files = [int(x) for x in which_files]

    # extract the files the user has chosen to path=file_name
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        print('\nExtracting...')
        # extract designated files and print the files on screen
        for ndx, file in enumerate(zip_files):
            if ndx+1 in which_files:
                this_file = zip_files[ndx]
                print(this_file)
                # prevent an unintentional file overwrite...
                if os.path.isfile(this_file):
                    ok = input('\nOverwrite file on disk? (Y/N): ').strip().upper()
                    if ok == 'N':
                        print('\nSkipping', this_file)
                        continue
                # extract the file here
                f.extract(this_file, path=file_name[:-4])

    return full_path, file_name


def remove_file(full_path, file_name):
    """
    This utility removes only one file at a time.

    Technical info: To remove a file, this function first create a temporary archive that holds all the original files except the one targeted for removal. The temporary archive is tested for integrity; the original archive is deleted; the temporary archive is renamed as the original.
    """
    # unlikely, but check if "temporary" directory already exists
    this_path = '_temp_' + file_name[:-4] + '_'
    if os.path.isdir(this_path):
        print('\nCannot remove files from archive, since ',
              this_path, ' directory exists.', sep='')
        return full_path, file_name

    # get a list of files in the archive and their total number
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        num_files = len(f.namelist())

    while True:
        # for the user, print a list of files in the archive
        full_path, file_name = list_files(full_path, file_name)

        # get from the user the file that should be removed
        choice = input("\nEnter the number of file to remove: ")

        # if no file name is entered, return to menu
        if not choice.strip():
            return full_path, file_name

        # make sure user entered a valid integer
        try:
            choice = int(choice)
            if choice <= num_files:
                break
        except:
            print('\nEnter only an integer, in range 1-',
                  num_files, '.\n', sep='')
            continue

    # get confirmation from the user about the file to be removed
    with zipfile.ZipFile(file_name, 'r') as f:
        print()
        for ndx, file in enumerate(zip_files):
            if ndx+1 == choice:
                print(ndx+1, '. ', file, sep='')

    confirmed = input('\nRemove file? (Y/N) ').strip().upper()
    if confirmed == 'Y':
        # create the directory that will hold files temporarily
        os.mkdir(this_path)

        # extract all the files to "this_path" except
        # the file user has chosen
        with zipfile.ZipFile(file_name, 'r') as f:
            for ndx, file in enumerate(zip_files):
                if ndx+1 != choice:
                    this_file = zip_files[ndx]
                    f.extract(this_file, path=this_path)

        # preserve absolute and relative paths to current directory
        current_directory = os.getcwd()
        rel_dir = os.path.relpath(current_directory, '')

        # add all the extracted files to _temp_zipfile_.zip
        with zipfile.ZipFile('_temp_zipfile_.zip', 'w', compression=zipfile.ZIP_DEFLATED) as f:
            # change directory to the temporary directory which will be
            # the location of our temporary zip file
            os.chdir(this_path)
            # Iterate over all the files in the root directory
            for folderName, subfolders, filenames in os.walk(rel_dir):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # add file to zip
                    f.write(filePath)

        # change back to the directory holding file_name
        os.chdir(current_directory)

        # test the temporary archive before deleting the original one
        if not zipfile.is_zipfile('_temp_zipfile_.zip'):
            print('\nUnknown error. Aborting removal of file.')
        # open the archive and test it using testzip()
        try:
            with zipfile.ZipFile('_temp_zipfile_.zip', 'r') as f:
                if f.testzip():
                    print('\nUnknown error. Aborting removal of file.')
        except:
            print('\nUnknown error. Aborting removal of file.')

        # delete file_name
        try:
            os.remove(file_name)
        except:
            print('\nCannot complete file removal.')

        # rename _temp_zipfile_.zip to file_name
        os.rename('_temp_zipfile_.zip', file_name)

        # delete the "temporary" directory
        shutil.rmtree(this_path)

    return full_path, file_name


def test_archive(full_path, file_name):
    """
    Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testzip() will not detect a problem and you will extract a corrupted file.
    """
    # first, test if it is a valid zip file
    if not zipfile.is_zipfile(file_name):
        print('\nNot a valid zip file.')
        return full_path, file_name

    # open the archive and test it using testzip()
    with zipfile.ZipFile(file_name, 'r') as f:
        tested_files = f.testzip()
        num_files = len(f.infolist())

    if tested_files:
        print('Bad file found:', tested_files)
    else:
        print('\nTested ', num_files, ' files:  ',
              num_files, ' OK.  0 failed.', sep='')

    return full_path, file_name


def about():
    """
    Provide a very little history behing the name "katz".
    """
    about1 = '"katz" is named after Phil Katz, the founder of'
    about2 = 'PKWARE in 1989, the company that originated the'
    about3 = 'ZIP file format that is still in popular use today.'

    print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
    print(about1, '\n', about2, '\n', about3, '\n', sep='')

    return


def fold(txt):
    """
    Textwraps 'txt'; used by help() to wrap help text at column 45.
    """
    return textwrap.fill(txt, width=45)


def help():
    """
    A help function.
    """
    print('\n', dsh*45, sep='')
    print(slsh*20, ' HELP ', slsh*20, sep='')
    print(dsh*45, sep='')

    txt = """
Main menu:
    katz 1.0 archives files using only the zip file format (not gzip or tar). File compression is automatic. If you open a zip file or create a new zip file with a path (e.g., c:\\mydata\\foo.zip), the path to that zip file will be considered the root directory for all operations in the sub-menu.

Sub-menu:
    <L>ist
        -- List all the files in the archive

    <A>dd
        -- Add files to the archive.
        -- Enter a "." to get a list of files from the same directory holding the zip file, or enter a path to another directory.
        -- You can optionally include files in all subdirectories. The subdirectory structure containing the files you want to add will be preserved in the archive file.
        -- For speed, three methods are provided for identifying files that you want to add. Don't mix methods! You can mix numbers and ranges, though. See the first item under <E>tract, below.

    <E>xtract
        -- You can mix individual "file numbers" and ranges. Examples of using numbers to identify individual files:
            -- 1, 2, 8, 4  [order does not matter]
            -- 3-8, 11, 14 [mix a range and individual numbers]
            -- all  [extracts all files]
        -- Files are extracted to a subfolder with the same name as the archive file. This location is not configurable.

    <R>emove
        -- Removes a file from the archive. This operation is not undoable!

    <T>est
        -- Test the integrity of the archive. If you archive a corrupted file, testing will not identify the fact that it is corrupted!
"""
    print("\n".join([fold(txt) for txt in txt.splitlines()]))
    print(dsh*45)

    return


def get_revision_number():
    """
    Returns the revision number, which is the number of days since the initial coding of "ida" began on November 12, 2019.
    """
    start_date = datetime(2019, 11, 21)
    tday = datetime.today()
    revision_delta = datetime.today() - start_date

    return revision_delta.days


def main_menu():
    """
    Menu for opening a file or creating a new file, which the user can then manipulate via the sub-menu.

    Variables:
        open_file, new_file: whether or not we are opening an existing file or creating a new one; passed to sub_menu()
    """
    # store the user's current working directory
    _user_directory_ = os.getcwd()

    # generate the main menu until the user presses "Q"
    while True:

        # print the program header
        version_num = "1.0"
        revision_number = 5
        print("\nkatz ", version_num,
              " - a command-line archiving utility", sep='')

        # reset user-entered file names/paths
        full_path, file_name = '', ''

        while True:
            choice = input(
                '\n<O>pen file    <N>ew file    <A>bout\n<H>elp     Q>uit\n\nChoice: ').strip().upper()
            if choice in 'ONAHQ':
                break
            else:
                print('\nEnter only "O", "N", "A", "H", or "Q".')
                continue

        if choice == 'O':
            open_file, new_file = True, False
            sub_menu(open_file, new_file)

        elif choice == 'N':
            open_file, new_file = False, True
            sub_menu(open_file, new_file)

        elif choice == 'A':
            about()

        elif choice == 'H':
            help()

        elif choice == 'Q':
            break

        # change back to original user directory
        os.chdir(_user_directory_)


def sub_menu(open_file, new_file):
    """
    Menu of actions on the file that the user has opened or created.
    """
    # either open the file or create a new file
    if open_file:
        full_path, file_name = open_archive()
    else:
        full_path, file_name = create_new()

    # go back to the main menu if no file name is entered
    if not file_name:
        return

    # if we are opening a zip file, show its contents
    if open_file:
        full_path, file_name = list_files(full_path, file_name)

    # use the following to delimit output from sequential commands
    if len(full_path) >= 49:
        msg = '...' + full_path[-49:]
    else:
        msg = full_path
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

    # # print a list of all the files in the archive
    # full_path, file_name = list_files(full_path, file_name)

    while True:
        # generate the sub-menu
        print('\n<L>ist    <A>dd   <E>xtract\n<R>emove  <T>est  <M>ain menu')
        user_choice = input('\nChoose an action: ').strip().upper()

        if user_choice not in 'LAERTM':
            print('\n"', user_choice, '" ', 'is an invalid action.', sep='')
            continue

        print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

        # actions to take on choosing a menu item
        if user_choice == 'L':
            full_path, file_name = list_files(full_path, file_name)

        elif user_choice == 'A':
            full_path, file_name = add_file(full_path, file_name)

        elif user_choice == 'E':
            full_path, file_name = extract_file(full_path, file_name)

        elif user_choice == 'R':
            full_path, file_name = remove_file(full_path, file_name)

        elif user_choice == 'T':
            full_path, file_name = test_archive(full_path, file_name)

        else:
            return

    return


if __name__ == '__main__':
    main_menu()

    # =================================================
    # utility functions for developer only
    # =================================================
    # print('Revision number:', get_revision_number())
    # 2019-11-30: rev 9
