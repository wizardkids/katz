"""
katz.py

Richard E. Rawson
2019-12-10

command-line zip archiving utility
    1. list all files, including files in subfolders, within the archive
    2. print a directory listing for a directory on disk
    3. add one, many, or all files, optionally including subfolders from any directory on disk
    4. extract one, many, or all files from the archive, including subfolders
    5. remove one file at a time from the archive
    6. test the integrity of the archive
"""

import glob
import os
import shutil
import string
import sys
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path
from subprocess import check_output

# the following if... prevents a warning being issued to user if they try to add a duplicate file to an archive; this warning is handled in add_file()
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# todo -- review all the functions in this program and see if you can make them more efficient

# todo -- version 2: Create an interface that behaves largely like a Windows command window (cmd.exe) with special (but limited) capabilities regarding management of zip files.

# todo -- Version 3: Add support for other archiving formats, including tar and gzip

# todo -- Version 4:
#       -- 1. Write katz so it can be used as an importable module.
#       -- 2. Add support for importing into other scripts so that, for example, downloaded archives are extracted automatically

# declare global variables
dsh, slsh = '=', '/'

# shell_cmds dict holds help information for commands
shell_cmds = {
    'DIR': 'Displays a list of files and subdirectories in a directory.\n\nDIR [drive:][path][filename]\n',
    'CD': 'Displays the name of or changes the current directory.\n\nCD [/D][drive:][path]\n\n".." changes to the parent directory.\n',
    'CLS': 'Clears the screen. ("CLEAR" on Unix systems.)\n',
    'OPEN': 'Open an existing zip file. Optionally include a path.\n',
    'O': 'Open an existing zip file. Optionally include a path.\n',
    'NEW': 'katz 1.0 archives files using only the zip file format (not gzip or tar). File compression is automatic. For easiest usage, use the "cd" command to change the current directory to the directory containing the zip file that you want to work with.\n',
    'N': 'Create a new zip file. Optionally include a path.\n',
    'LIST': '<L>ist all the files in the archive. <DIR> lists files in a directory on disk, while <L>ist produces a list of files in the archive.\n',
    'ADD': '-- <A>dd provides a list of files that you can <A>dd to the archive.\n\n-- Enter a "." to get a list of files from the same directory holding the zip file, or enter a path to another directory. Files in the same directory as the zip file will be added to a folder with the same name as the folder holding the zip file.\n\n-- You can optionally include files in all subdirectories. The subdirectory structure containing the files you want to add will be preserved in the archive file. Even if you include the name of your archive in the list of files to <A>dd, "katz" cannot add a zip file to itself.\n\n-- For speed, three methods are provided for identifying files that you want to <A>dd. Don\'t mix methods! You can mix numbers and ranges, though. See the second item under <E>xtract, below, for details.\n',
    'EXTRACT': '-- Files are extracted to a subfolder with the same name as the archive file. This location is not configurable.\n-- <E>xtract provides a numbered list of files to <E>xtract. To select files for extraction, you can mix individual "file numbers" and ranges. Examples of different ways of identifying files for extraction:\n(1) 1, 2, 8, 4  [order does not matter]\n(2) 3-8, 11, 14  [mix a range and individual numbers]\n(3) enter a folder name\n(4) all  [extracts all files]\nSYMLINKS:\n"katz" will archive file and folder symlinks. When extracted, files/folders will not extract as a symlinks but as the original files/folders.\n',
    'REMOVE': '<R>emoves files or a single folder from the archive. This operation cannot be reversed! If the specified folder has subfolders, only the files in the folder will be removed; subfolders (and contents) will be retained. "katz" will confirm before removing any files or folders.\nRemoving all files in the archive by attempting to remove the "root" folder is disallowed. To remove all files/folders, delete the zip file, instead.\n',
    'TEST': '<T>est the integrity of the archive. SPECIAL NOTE: If you archive a corrupted file, testing will not identify the fact that it is corrupted!\n',
    'EXIT': 'Quits the shell and the current script.\n',
    'QUIT': 'Quits the shell and the current script.\n',
}

# used to translate command abbreviations into full command strings
translate = {
    'D': 'DIR',
    'DIR': 'DIR',
    'CLS': 'CLS',
    'CLEAR': 'CLS',
    'EXIT': 'EXIT',
    'N': 'NEW',
    'NEW': 'NEW',
    'O': 'OPEN',
    'OPEN': 'OPEN',
    'CD': 'CD',
    'CD.': 'CD',
    'CD..': 'CD',
    '.': 'CD',
    '..': 'CD',
    'H': 'HELP',
    'HELP': 'HELP',
    'Q': 'QUIT',
    'QUIT': 'QUIT',
    'A': 'ADD',
    'ADD': 'ADD',
    'L': 'LIST',
    'LIST': 'LIST',
    'A': 'ADD',
    'ADD': 'ADD',
    'E': 'EXTRACT',
    'EXTRACT': 'EXTRACT',
    'R': 'REMOVE',
    'REMOVE': 'REMOVE',
    'T': 'TEST',
    'TEST': 'TEST'}

# the following list is used in sub_menu() to filter zip-file commands
command_list = ['DIR', 'CLS', 'CLEAR', 'EXIT', 'N', 'NEW', \
                'O', 'OPEN', 'CD', 'CD.', 'CD..', '.', '..', \
                'H', 'HELP','Q', 'QUIT', 'A', 'L', 'A', 'E', 'R', 'T']

def parse_full_filename(path):
    """
    Takes a full path (path, including a file name) and parses it into a file name and a path (without the filename).

    Arguments:
        path {str} -- an absolute path plus a file name

    Returns:
        three {str} - file name, path only, path plus file name
    """
    file_name = Path(path).name
    full_path = str(Path(path).parent.absolute())
    full_filename = str(Path(path).absolute())

    return file_name, full_path, full_filename


def valid_path(path):
    """
    Is the given path a valid OS path?

    Arguments:
        path {str} -- a proposed absolute path plus a file name, to be tested

    Returns:
        [bool] -- [True if (1) the path/file exists; (2) it's a valid OS path and (3) it must include a file name]
    """
    try:
        with zipfile.ZipFile(path, 'r') as f:
            pass
        if Path(path).name[-4:].upper() == '.ZIP':
            return True
        else:
            return False
    except (FileNotFoundError, PermissionError, OSError):
        return False


def new(switch):
    """
    Create a new zip file.

    Paths entered by users can contain a plethora of errors including spelling errors, non-existant paths, and file names that don't meet OS requirements. Also, the python zipfile module does not require that zip files have a .zip extension, but such an extension makes life easier for the user and is required by this program.

    A simple testing strategy is employed: see if the path/file can be opened. A multitude of errors are tested all at once.

    Arguments:
        switch {[str]} -- [assumed to be path/filename, stripped of leading and trailing spaces]

    Returns:
        [str] -- [a validated path/filename or an empty string]
    """
    # "cmd switch" pattern may be entered the command line. "cmd" is assumed to be "new";"switch", if present, is assumed to be a path/file.
    # if "switch" is an empty string, get a [path]/filename from the user
    if not switch:
        full_filename = input("\nName of archive: ").strip()

        file_name, full_path, full_filename = parse_full_filename(switch)

    # if user entered a "switch", test it, then parse it
    else:
        # if user did not enter an extension, add .zip
        switch = switch + '.zip' if switch[-4].upper() != '.ZIP' else switch

        if valid_path(switch):
            file_name, full_path, full_filename = parse_full_filename(switch)

        else:
            print('The system cannot find the path specified.\n')
            return ''

    # if user entered an empty string or parse_full_filename() returned an empty string, return to the menu
    if not file_name:
        return ''

    # if file already exists, overwrite only is user agrees
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            msg = file_name + ' already exists. Overwrite? (Y/N) '
            overwrite = input(msg).upper()

            if overwrite == 'Y':
                with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', file_name, 'created as new archive.\n')
                return full_filename

            else:
                print(file_name, 'not created.\n')
                return ''

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            print('\n', file_name, 'created as new archive.\n')

        return full_filename


def open(full_filename):
    """
    Open an archive. If a path is entered, chdir() to that path.

    Paths entered by users can contain a plethora of errors including spelling errors, non-existant paths, and file names that don't meet OS requirements. A simple testing strategy is employed: see if the path/file can be opened. A multitude of errors are tested all at once.

    Arguments:
        switch {str} -- [path]/file

    Returns:
        str -- path/file
    """

    # if no "full_filename" was entered, get user input
    if not full_filename:
        f = input("\nName of archive: ").strip()

        # if no path was entered (only a file name), get full path
        if '\\' not in f:
            switch = str(Path(f).absolute())

    # if user entered only path at the command line, get the absolute path
    else:
        if '\\' not in full_filename:
            full_filename = str(Path(full_filename).absolute())

    # test validity of what the user entered either at the command line or at input()
    if not valid_path(full_filename):
        print('The system cannot find the path specified.\n')
        return ''

    # change the working directory to directory containing the zip file
    file_name, full_path, full_filename = parse_full_filename(full_filename)
    os.chdir(full_path)

    return full_filename


def list_files(file_name, full_path, full_filename):
    """
    Generate a numbered list of all the files and folders in the archive.
    """
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        zip_files = sorted(zip_files, reverse=True)

        # get the directory of the first item in zip_files
        try:
            current_directory = Path(zip_files[0]).parent
        except:
            current_directory = ''
            if len(zip_files) == 0:
                print('No files in archive.')
                return file_name, full_path, full_filename

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
            print(' '*3, ndx+1, '. ', this_file, sep='')

            # pause after every 25 files
            cnt = ndx+1
            if len(zip_files) >= 25 and cnt >= 25 and cnt % 25 == 0:
                more = input(
                    '--ENTER to continue; Q to quit--').strip().upper()
                if more == 'Q':
                    break

    return file_name, full_path, full_filename


def add_files(file_name, full_path, full_filename):
    """
    Add one, many, or all files from the user-designated folder, and optionally include subfolders of that folder. Uses various methods for choosing files to add, optimized for speed of selection.
    """
    current_directory = os.getcwd()

    # ==================================================
    # GET THE SOURCE DIRECTORY FROM THE USER
    # ==================================================

    while True:
        print('\nEnter "." to use current directory.')
        user_dir = input("Directory containing files to add: ").strip()

        # if user enters nothing, return to the menu
        if not user_dir:
            return file_name, full_path, full_filename

        if user_dir == '.':
            user_dir = str(Path(full_path).absolute())

        # confirm that user's entry is valid
        msg = 'The system cannot find the path specified.'
        if '*' in user_dir or '?' in user_dir:
            if Path(user_dir).parent.exists():
                msg = ''
        elif Path(user_dir).exists():
            if Path(user_dir).is_file():
                msg = ''
            else:
                msg = ''
        if not msg:
            subs = input('Include subdirectories (Y/N): ').strip().upper()
            subs = True if subs == 'Y' else False
            print()
            break

    # ==================================================
    # GENERATE A NUMBERED LIST OF ALL FILES IN THE USER-CHOSEN FOLDER
    #       AND PRINT THE LIST ON SCREEN
    # ==================================================

    if subs:
        # dir_list contains subfolders
        if '*' in user_dir or '?' in user_dir:
            dir_filter = '**/' + str(Path(user_dir).name)
            dir_list = sorted(Path(user_dir).parent.glob(dir_filter))
            user_dir = str(Path(user_dir).parent)
        else:
            dir_filter = '**/*.*'
            dir_list = sorted(Path(user_dir).glob(dir_filter))
            user_dir = str(Path(user_dir))

    else:
        # dir_list contains contents of only the "dir" folder
        if '*' in user_dir or '?' in user_dir:
            dir_filter = Path(user_dir).name
            dir_list = sorted(Path(user_dir).parent.glob(dir_filter))
        else:
            dir_filter = '*.*'
            dir_list = sorted(Path(user_dir).glob(dir_filter))

    cnt = 1
    for file in dir_list:
        # this code finds the relative folder name
        file_parts = Path(file).parts
        for ndx, i in enumerate(file_parts):
            if i not in Path(user_dir).parent.parts:
                loc = ndx
                break
        # rel_folder is the relative path to the current file (in selected_files)
        rel_folder = '\\'.join(file_parts[loc:-1])
        rel_folder = Path(rel_folder, Path(file).name)
        print(cnt, '. ', rel_folder, sep='')
        cnt += 1

    # ==================================================
    # GET FROM USER THE FILES TO ADD TO THE ARCHIVE
    # ==================================================

    while True:
        # example user input: 1, 3-5, 28, 52-68, 70 or *.t?t
        print('\nEnter:\n(1) a comma-separated combination of:\n    -- the number of the file(s) to add\n    -- a hyphenated list of sequential numbers\n(2) enter "all" to add all files\n(3) use wildcard characters (*, ?) to designate files')

        user_selection = input("\nFile(s) to add: ").strip()

        # if nothing is entered, return to menu
        if not user_selection:
            return file_name, full_path, full_filename

        # ========================================================
        # BASED ON USER'S CHOICES, CREATE A LIST OF THE ELIGIBLE FILES
        # ========================================================

        selected_files = []
        if user_selection.upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(dir_list)+1)]
            for file_number in which_files:
                selected_files.append(str(dir_list[int(file_number)-1]))

        # see https://pymotw.com/2/glob/
        elif '*' in user_selection or '?' in user_selection:
            folders = set()

            # generate a list of all folders in dir_list
            for file in dir_list:
                folders.add(str(Path(file).parent))

            # get all files in folders/subfolders that match "user_selection"
            for folder in folders:
                os.chdir(folder)
                f = glob.glob(user_selection)
                for i in f:
                    file = Path(folder, i)
                    selected_files.append(file)
                    print(i)

        # create a list of the user's chosen files
        else:
            selected_files = get_chosen_files(
                selected_files, user_selection, dir_list, file_name, full_path, full_filename)

        break

    os.chdir(current_directory)

    # ==================================================
    # ADD THE FILES:
    #   files ALWAYS go into named folders
    # ==================================================

    # get a list of all the files that are in the archive
    with zipfile.ZipFile(full_filename) as f:
        zip_files = f.namelist()
        zip_files = sorted(zip_files, reverse=True)

    # namelist() formats paths as: foo/bar/bar.txt
    # need to change"/" into "\\""
    zip_files_temp = zip_files.copy()
    for ndx, file in enumerate(zip_files_temp):
        file = file.replace('/', '\\')
        zip_files[ndx] = file

    with zipfile.ZipFile(file_name, 'a', compression=zipfile.ZIP_DEFLATED) as f:
        for file in selected_files:
            # this code finds the relative folder name
            file_parts = Path(file).parts
            for ndx, i in enumerate(file_parts):
                if i not in Path(user_dir).parent.parts:
                    loc = ndx
                    break
            # rel_folder is the relative path to the current file (in selected_files)
            rel_folder = '\\'.join(file_parts[loc:-1])
            rel_folder = Path(rel_folder, Path(file).name)

            if Path(file).name.upper() != file_name.upper():  # katz won't add the zip to itself
                # if the current file (in selected_files) is already in zip file, skip adding it
                if str(rel_folder) not in zip_files:
                    f.write(file, arcname=rel_folder)

    return file_name, full_path, full_filename


def extract_file(file_name, full_path, full_filename):
    """
    Extract one or more files from an archive.
    """
    # ==============================================
    # GET A LIST FILES IN THE ARCHIVE AND PRINT IT
    # ==============================================
    file_name, full_path, full_filename = list_files(
        file_name, full_path, full_filename)

    with zipfile.ZipFile(full_filename, 'r') as f:
        # file_list contains relative paths of files in archive
        file_list = f.namelist()
        file_list = sorted(file_list, reverse=True)
        num_files = len(file_list)


    # ==============================================
    # LET USER CHOOSE WHICH FILE(S) TO EXTRACT
    # ==============================================

    # sample user input: 1, 3-5, 28, 52-68, 70
    print(
        '\nEnter a comma-separated combination of:\n  -- the number of the file(s) to extract\n  -- a hyphenated list of sequential numbers\n  -- a folder name\n  -- or enter "all" to extract all files\n')
    user_selection = input("File number(s) to extract: ")

    # ==============================================
    # GENERATE A LIST OF ALL FILES USER WANTS TO EXTRACT
    # ==============================================

    # if no user_selection is made, return to menu
    if not user_selection.strip():
        return file_name, full_path, full_filename

    # determine if "user_selection" is an integer/range or a folder
    for c in user_selection:
        # if the entire string comprises digits or contains '-'
        if c in string.digits or c in [',', ' ', '-']:
            user_selection_isNumbers = True
        else:
            user_selection_isNumbers = False
            break

    if user_selection_isNumbers:

        # selected_files will contain all the files we want to extract
        selected_files = []
        user_selection = user_selection.replace('/', '\\')
        selected_files = get_chosen_files(
            selected_files, user_selection, file_list, file_name, full_path, full_filename)

    # otherwise, process "user_selection" as a folder or 'all'
    else:
        # deny ability to delete root/ folder
        if 'ROOT' in user_selection.upper():
            msg = '\nOperation cannot be completed.\nFor help, type: "extract /?".\n'
            print('='*52, msg, '='*52, sep='')
            return file_name, full_path, full_filename

        user_selection = user_selection.replace('/', '\\')

        # if user_selection="ALL", then generate a list of all file numbers
        if user_selection.strip().upper() == 'ALL':
            # add all files in user_selected folder to selected_files
            selected_files = file_list
            # for file in file_list:
            #     if str(Path(file).parent).upper() == user_selection.upper():
            #         selected_files.append(file)
        else:
            # confirm the user's selection of a folder to extracty by
            # looking for it within file_list
            selected_files = []
            for ndx, file in enumerate(file_list):
                # if "file" contains the path in "user_selection"
                file_path = str(Path(file).parent)
                if user_selection.upper() == file_path.upper():
                    selected_files.append(file)
            if not selected_files:
                print('File not found.')

    # ==============================================
    # CONFIRM THE SELECTION OF FILES
    # ==============================================
    for ndx, file in enumerate(selected_files):
        print(ndx+1, '. ', file, sep='')

    confirm = input('\nExtract files (Y/N) ').upper()
    if confirm != 'Y':
        return file_name, full_path, full_filename

    # ==============================================
    # EXTRACT THE FILES THE USER HAS CHOSEN AND
    #       PRINT FILE NAMES ON SCREEN
    # ==============================================

    with zipfile.ZipFile(full_filename, 'r') as f:
        print('\nExtracting...')
        extract_location = str(Path(full_path, file_name[:-4]))

        for file in selected_files:
            # prevent an unintentional file overwrite of this_file
            # in the directory where files will be extracted
            if Path(extract_location, file).is_file():
                ok = input(
                    'Overwrite file on disk? (Y/N): ').strip().upper()
                if ok == 'N':
                    print('Skipping', file)
                    continue
            print(file)
            # extract the file to extract_location
            f.extract(file, path=extract_location)

    return file_name, full_path, full_filename


def remove_files(file_name, full_path, full_filename):
    """
    Removes files/folders from the archive.

    Technical info: To remove a file, this function first create a temporary archive that holds all the original files except the one targeted for removal. The temporary archive is tested for integrity; the original archive is deleted; the temporary archive is renamed as the original.
    """
    # make sure you are in the same directory as the zip file
    os.chdir(full_path)

    # unlikely, but... abort if "temporary" directory already exists
    temporary_path = '_temp_' + file_name[:-4] + '_'
    temp_dir = str(Path(full_path, temporary_path))

    if os.path.isdir(temporary_path):
        msg = '\nCannot remove files from archive, since ' + temporary_path + ' directory exists.\n'
        print('='*52, msg, '='*52, sep='')

        return file_name, full_path, full_filename

    # ===================================================
    # 1. GET AND PRINT A NUMBERED LIST OF FILES IN THE ARCHIVE
    # 2. GET FROM USER EITHER:
    #       A. THE NUMBER(s) OF THE FILE(s) TO REMOVE
    #       B. THE NAME OF THE FOLDER TO REMOVE
    # ===================================================

    while True:
        # get a list of files in the archive and their total number
        with zipfile.ZipFile(full_filename, 'r') as f:
            file_list = f.namelist()
            file_list = sorted(file_list, reverse=True)
            num_files = len(file_list)

        # for the user, print a list of files and folders in the archive
        file_name, full_path, full_filename = list_files(
            file_name, full_path, full_filename)

        # get from the user the file or folder that should be removed
        print("\nEnter file number(s) or range(s) to")
        print('remove or, to remove a whole folder,')
        user_selection = input("type the name of the folder: ").strip()

        # if no file name is entered, return to menu
        if not user_selection.strip():
            return file_name, full_path, full_filename

        # determine if "user_selection" is an integer/range or a folder
        for c in user_selection:
            # if the entire string comprises digits or contains '-'
            if c in string.digits or c in [',', ' ', '-']:
                user_selection_isNumbers = True
            else:
                user_selection_isNumbers = False
                break

        # if user_selection is an integer or range, get a list of integers
        if user_selection_isNumbers:
            selected_files = []
            selected_files = get_chosen_files(
            selected_files, user_selection, file_list, file_name, full_path, full_filename)
            # if get_chosen_files returns an empty selected_files, then
            # something went wrong
            if not selected_files:
                msg = '\nInvalid entry. Try again.\n'
                print('='*52, msg, '='*52, sep='')
                continue

            # otherwise print a list of files destined for removal
            else:
                print()
                for ndx, file in enumerate(selected_files):
                    print(ndx+1, '. ', file, sep='')
                confirmed = input('\nRemove these files from the archive? (Y/N) ').strip().upper()
                if confirmed == 'Y':
                    break

        # otherwise, process "user_selection" as a folder
        else:
            # deny ability to delete root/ folder
            if 'ROOT' in user_selection.upper():
                msg = '\nOperation cannot be completed.\nFor help, type: "remove /?".\n'
                print('='*52, msg, '='*52, sep='')
                continue
            user_selection = user_selection.replace('/', '\\')

            # confirm the user's selection of a folder to remove by
            # looking for it within file_list
            for ndx, file in enumerate(file_list):
                # if "file" contains the path in "user_selection"
                file_path = str(Path(file).parent)
                if user_selection.upper() == file_path.upper():
                    confirmed = input('\nRemove folder: ' + user_selection + ' (Y/N) ').upper()
                    break
                if ndx == num_files-1:
                    msg = '\nCould not find the folder "' + user_selection + '" in the archive.\n'
                    print('='*52, msg, '='*52, sep='')
                    confirmed = 'N'
                    continue
            if confirmed == 'Y':
                # add all files in user_selected folder to selected_files
                selected_files = []
                for file in file_list:
                    if str(Path(file).parent).upper() == user_selection.upper():
                        selected_files.append(file)
                break

    # ===============================================
    # REMOVE THE FILES DESIGNATED BY THE USER
    # ===============================================

    if confirmed == 'Y':
        # create the directory that will hold files temporarily
        os.mkdir(temporary_path)

        # extract all files in archive EXCEPT those in selected_files
        with zipfile.ZipFile(full_filename, 'r') as f:
            for file in file_list:
                if file not in selected_files:
                    f.extract(file, path=temporary_path)

        # Make the temporary directory current
        os.chdir(temp_dir)

        dir = str(Path(full_path, temporary_path))
        temp_zip_file = str(Path(temp_dir, '_temp_zipfile_.zip'))
        dir_list = sorted(list(Path(temp_dir).glob('**/*.*')))

        # dir_list contains all the files in the archive EXCEPT
        # those that the user wants to remove; so add them all back
        with zipfile.ZipFile(temp_zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            for file in dir_list:
                # this code finds the relative folder name
                file_parts = Path(file).parts
                for ndx, i in enumerate(file_parts):
                    if i not in Path(temp_dir).parent.parts:
                        loc = ndx
                        break
                # rel_folder is the relative path to the current file (in selected_files)
                rel_folder = '\\'.join(file_parts[loc+1:-1])
                rel_folder = Path(rel_folder, Path(file).name)

                if Path(file).name.upper() != file_name.upper():  # katz won't add the zip to itself
                    f.write(file, arcname=rel_folder)

        # ===============================================
        # CLEAN UP TEMPORARY FILES AND DIRECTORY
        # ===============================================
        os.chdir(full_path)

        # test the temporary archive before deleting the original one
        if not zipfile.is_zipfile(temp_zip_file):
            msg = '\nUnknown error. Aborting removal of file.\n'
            print('='*52, msg, '='*52, sep='')

        # open and test temporary archive;
        # if successful, delete original and rename temporary zip
        try:
            with zipfile.ZipFile(temp_zip_file, 'r') as f:
                if f.testzip():
                    raise Exception
            # delete file_name
            os.remove(full_filename)
            # copy _temp_zipfile_.zip to file_name
            shutil.copyfile(temp_zip_file, full_filename)
        except:
            msg = '\nUnknown error. Aborting removal of file.\n'
            print('='*52, msg, '='*52, sep='')

        # delete "temporary" file even if exception was raised in previous line
        if os.path.isfile(temp_zip_file):
            try:
                os.remove(temp_zip_file)
            except:
                msg = '\nCannot complete operation. _temp_zipfile_.zip is being used by another process.\n'
                print('='*52, msg, '='*52, sep='')

        # change back to original directory
        os.chdir(full_path)

        # delete "temporary" dir even if exception was raised in previous line
        if Path(full_path, temporary_path).is_dir():
            try:
                shutil.rmtree(Path(full_path, temporary_path), ignore_errors=False)
            except PermissionError:
                msg = '\nCannot complete operation. A file or folder in ' + temporary_path + ' is being used by another process.\n'
                print('='*52, msg, '='*52, sep='')

    return file_name, full_path, full_filename


def get_chosen_files(selected_files, user_selection, file_list, file_name, full_path, full_filename):
    """
    User enters one of these and all are handled differently:
        -- 'all'
        -- 1, 3-5, 28, 52-68, 70
        -- *.t?t

    Arguments:
        selected_files {[list]} -- [will contain rel_path/filename of user-selected files]
        user_selection {[str]} -- [user-selected files... see above]
        file_list {[list of str]} -- [path/filenames of all files in archive]
        file_name {[str]} -- [name of the archive file]
        full_path {[str]} -- [path to the archive file]
        full_filename {[str]} -- [path+filename of archive file]

    Returns:
        [list] -- [rel_path/filename of user-selected files]
    """

    # split user's entry at commas
    # list now contains integers &/or ranges
    user_files = user_selection.split(',')

    which_files = []
    for i in user_files:
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
                return file_name, full_path, full_filename
        # treating all other single digits
        else:
            try:
                n = int(i)
                which_files.append(str(n))
            except:
                print(
                    '\nInvalid number(s) excluded. Did you comma-separate values?')
                return file_name, full_path, full_filename

    for file_number in which_files:
        selected_files.append(file_list[int(file_number)-1])

    return selected_files


def test_archive(file_name, full_path, full_filename):
    """
    Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testzip() will not detect a problem and you will extract a corrupted file.
    """
    # first, test if it is a valid zip file
    if not zipfile.is_zipfile(full_filename):
        print('\nNot a valid zip file.')
        return full_path, file_name

    # open the archive and test it using testzip()
    with zipfile.ZipFile(full_filename, 'r') as f:
        tested_files = f.testzip()
        num_files = len(f.infolist())

    if tested_files:
        print('Bad file found:', tested_files)
    else:
        print('\nTested ', num_files, ' files:  ',
              num_files, ' OK.  0 failed.', sep='')

    return file_name, full_path, full_filename


def about():
    """
    Provide a very little history behing the name "katz".
    """
    about = '''"katz" is a command-line zip file utility named after Phil Katz, the founder of PKWARE in 1989, the company that originated the ZIP file format that is still widely used today.
'''

    print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
    print(fold(about, '', 52), '\n')

    return


def fold(txt, ndnt='     ', w=52):
    """
    Textwraps 'txt'; used by help() to wrap help text at column 52.
    """
    return textwrap.fill(txt, subsequent_indent=ndnt, width=w)

def base_help():
    msg = '/'*23 + ' HELP ' + '/'*23
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')
    print('Usage: cmd /? (example: dir /?)')
    print('\n', 'AVAILABLE SHELL COMMANDS:', sep='')
    for k, v in shell_cmds.items():
        if k == 'O' or k == 'N':
            pass
        else:
            if k in ['QUIT', 'Q']:
                pass
            else:
                if k == 'EXIT':
                    print('EXIT, QUIT, Q')
                else:
                    print(k)

    print('\nAll commands are case insensitive.')
    print( dsh*52, '\n', '/'*52, '\n', dsh*52, sep='')
    print()


def shell_help(command):
    if command in ['EXIT', 'QUIT', 'Q']:
        command = 'EXIT'
    print(shell_cmds[command])


def get_revision_number():
    """
    Returns the revision number, which is the number of days since the initial coding of "katz" began on November 12, 2019.
    """
    start_date = datetime(2019, 12, 10)
    tday = datetime.today()
    rd = datetime.today() - start_date
    r_delta = rd.total_seconds() / 60 / 60
    revision_delta = int(r_delta)

    return revision_delta


def dir(switch=''):
    """
    Perform an OS dir command for the current path or the path designated by "switch". Path may be an absolute path, a relative path. or ".."

    Keyword Arguments:
        switch {str} -- an OS path (default: {''})

    Returns: None
    """
    # preserve the user's current directory
    current_directory = os.getcwd()

    # make sure "switch" is an absolute path, especially is
    # user entered ".."  or a subfolder
    file_name, full_path, full_filename = parse_full_filename(switch)

    try:
        # if user entered a path, change the cwd to path
        if switch:
            os.chdir(full_filename)
        output = str(check_output('dir', shell=True))
        out = output.split('\\r\\n')
        # print the output
        print()
        for ndx, i in enumerate(out[:-1]):
            if ndx == 0:
                print(i[2:])
            else:
                print(i)

        # restore the user's current directory
        os.chdir(current_directory)

    # if the path in "switch" can't be found, issue an error message
    except:
        print('The system cannot find the path specified: ', full_filename)
    print()

    return file_name, full_path, full_filename


def cd(switch=''):
    """
    Run an OS cd (change directory) command using the path contained in "switch". The path will be validated since the user may have entered "garbage". The path may be an absolute path or a relative path. "CD.." is a valid command and, in this case, "switch" will be "..". This function will handle that.

    Keyword Arguments:
        switch {str} -- expected to be a path, a relative path, or '..' (default: {''})
    """
    # if user didn't enter a valid cmd or path, there's nothing to do
    if switch == '':
        return None

    try:
        # cd .. --> go "up" one directory level
        if switch == '..':
            p = Path(os.getcwd())
            os.chdir(p.parent)

        # else a path was entered: go wherever "switch" directs;
        else:
            # change the directory as directed
            try:
                p = Path(switch).absolute()
                os.chdir(p)
            # if "switch" is not a real path, or contains a file name,
            # print an error message
            except:
                print('The system cannot find the path specified.')

    except:
        print('The system cannot find the path specified.')
    print()

    return None


def clear():
    """
    Run a cls or clear command to clear the terminal.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    return None


def parse_input(entry):
    """
    "entry"is whatever the user entered at the command line and the expected format is:

            cmd [switch]

    where:
        "cmd" is a recognized command (listed in [translation])
        "switch" is whatever follows cmd. "switch" is expected to be one of:
            (1) path
            (2) [path]/filename
            (3) /?  -- a request for help

    Invalid cmd and unrecognized switch are rejected. Once a zip file is opened, or a new zip file is created, submenu commands (zip file commands) become available.

    Arguments:
        entry {str} -- whatever the user types; must be parsed for sanity
    """
    # ===============================================
    # PROCESS THE USER'S ENTRY, WHICH WILL BE EITHER:
    #   1. CMD [/?]
    #   2. CMD [PATH][FILE]
    #   3. AN UNRECOGNIZABLE ENTRY
    # ===============================================

    # command only
    if entry.find(' ') == -1:
        cmd, switch = entry.upper(), ''

    # command + space + switch

# fixme: getting this error: line 996, in parse_input "if full_path.is_dir():" The error message is: "OSError: [WinError 123] The filename, directory name, or volume label syntax is incorrect: 'c:\\temp\\one\\tem>.zip' and I get it when I enter a bad path"

    else:
        space_ndx = entry.find(' ')
        cmd, switch = entry[:space_ndx].upper(), entry[space_ndx+1:]
        # remove quotes from switch, if present; not required by katz
        switch = switch.replace('"', '')
        switch = switch.replace("'", '')

    # if a cmd was entered, and it's not recognized, generate error msg
    if cmd and cmd not in translate.keys():
        msg = cmd + ' is not recognized as a valid command.\n'
        print(msg)

    # Windows OS understands "CD.."" and "CD .."" OR "DIR.."
    # and "DIR .." as equivalent commands, and Unix only understands
    # "CD .." and "DIR .." ("LS .."). It's easier to process
    # only one version...
    if cmd == 'CD..':
        cmd, switch = 'CD', '..'
    if cmd == 'DIR..':
        cmd, switch = 'DIR', '..'

    # we expect "switch" to be only a request for help or a path
    # ! if switch == '/?':
    # !     full_filename = ''
    # ! else:
    # !     full_filename = parse_full_filename(switch)

    # ===============================================
    # PROCESS THE USER'S COMMAND
    # ===============================================

    if switch == '/?':
        try:
            help_text = shell_cmds[translate[cmd]]
            help_text = help_text.split('\n')
            for i in help_text:
                i = '     ' + i
                print(fold(i, '        '))

            # if cmd == 'EXIT', then add switch so that main_menu()
            # won't quit when cmd is passed back to parse_input()
            cmd += ' /?'
        except:
            print(cmd, 'is not recognized as a valid shell command.\n')

    elif cmd[:4] in ['EXIT', 'QUIT'] or cmd[0] == 'Q':
        pass

    elif (cmd == 'HELP' or cmd == 'H') and not switch:
        clear()
        base_help()

    elif cmd == 'CD':
        cd(switch)

    elif cmd[:3] == 'DIR':
        dir(switch)

    elif cmd[:3] == 'CLS' or cmd[5] == 'CLEAR':
        # Windows does not generate an error with 'cls..' or 'cls ..'
        # so elif... discards everything after 'cls' or 'clear'
        clear()

    elif cmd == 'O' or cmd == 'OPEN':
        open_file, new_file = True, False
        full_filename = open(switch)
        if full_filename:
            sub_menu(file_name, full_path, full_filename)

    elif cmd == 'N':
        open_file, new_file = False, True

# fixme: when i opened an non-existant zipfile, i go tothe submenu (which is inappropritae) and when I go back to main menu, I get "line 1133, in sub_menu if switch == '/?': UnboundLocalError: local variable 'switch' referenced before assignment"

        full_filename = new(switch)
        if file_name:
            sub_menu(file_name, full_path, full_filename)

    elif cmd == 'A':
        about()

    elif cmd == 'H':
        clear()
        base_help()

    elif cmd and cmd in 'LERT':
        print('Command available only in the submenu. Open or create a file first.\n')

    elif not cmd:
        pass

    return cmd


def main_menu():
    """
    Display initial "splash" screen, then expose "shell" that accepts shell commands.
    """
    # INITIALIZE VARIABLES
    # ! file_name, full_path, full_filename = '', '', ''

    # ===============================================
    # PRINT THE PROGRAM HEADER... JUST ONCE
    # ===============================================
    version_num = "2.0"
    revision_number = get_revision_number()
    print("\nkatz ", version_num, '.', revision_number, " - a command-line archiving utility", sep='')
    print('\n<O>pen file   <N>ew file\n<A>bout       <H>elp')
    print('')

    # ===============================================
    # GENERATE THE MAIN MENU IN A LOOP
    # ===============================================

    while True:

        # ===============================================
        # GET A COMMAND FROM THE USER
        # ===============================================
        prompt = "(katz) " + os.getcwd() + ">"
        entry = input(prompt).strip()

        parsed = parse_input(entry)

        if parsed in ['EXIT', 'QUIT', 'Q']:
            break


def sub_menu(file_name, full_path, full_filename):
    """
    Menu of actions on the zip file that the user has opened or created.
    """
    zip_commands = ['L', 'LIST', 'D', 'DIR', 'A', 'ADD', 'E', 'EXTRACT',
        'R' 'REMOVE', 'T', 'TEST', 'H', 'HELP' 'Q', 'QUIT', 'CLS', 'CLEAR', '']
    # use the following to delimit output from sequential commands
    msg = '...' + full_filename[-49:] if len(full_filename.__str__()) >= 49 else full_filename
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

    while True:
        # generate the sub-menu
        print('\n<L>ist     <A>dd     <dir>ectory\n<E>xtract  <R>emove  <T>est\n<H>elp')
        user_choice = input('\nzip-file command> ').strip().upper()

        if user_choice.split(' ')[0] in command_list[3:13]:
            print('Return to shell to use shell commands, except dir and cls.')

        # show the delimiter, but not if we're returning to the "command prompt"
        if user_choice in zip_commands[:13]:
            print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

        # fix user_choice in case user just types <ENTER>

        if user_choice == '':
            user_choice = ' '
        else:
            cmd = user_choice.split(' ')[0]
            try:
                switch = user_choice.split(' ')[1]
            except:
                switch = ''

        # actions to take on choosing a menu item

# fixme: switch is being reference before it's assigned

        if switch == '/?':
                try:
                    help_text = shell_cmds[translate[cmd]]
                    help_text = help_text.split('\n')
                    for i in help_text:
                        i = '     ' + i
                        print(fold(i, '        '))

                    # if cmd == 'EXIT', then add switch so that the program
                    # won't quit when cmd is passed back to parse_input()
                    cmd += ' /?'
                except:
                    print(cmd, 'is not recognized as a valid shell command.\n')

        elif user_choice == 'L' or user_choice == 'LIST':
            file_name, full_path, full_filename = list_files(
                file_name, full_path, full_filename)

        elif user_choice[0] == 'D':
            try:
                if user_choice[0] == 'D' and user_choice[1] == ' ':
                    full_path = user_choice[2:]
                if user_choice[:3] == 'DIR' and user_choice[3] == ' ':
                    full_path = user_choice[4:]
            except:
                full_path = ''
            dir(switch)

        elif user_choice == 'A' or user_choice == 'ADD':
            file_name, full_path, full_filename = add_files(
                file_name, full_path, full_filename)

        elif user_choice == 'E' or user_choice == 'EXTRACT':
            file_name, full_path, full_filename = extract_file(
                file_name, full_path, full_filename)

        elif user_choice == 'R' or user_choice == 'REMOVE':
            file_name, full_path, full_filename = remove_files(
                file_name, full_path, full_filename)

        elif user_choice == 'T' or user_choice == 'TEST':
            file_name, full_path, full_filename = test_archive(
                file_name, full_path, full_filename)

        elif user_choice[0] == 'H':
            if user_choice.find(' ') == 4:
                zip_help(user_choice[5:])
            elif user_choice.find(' ') == 1:
                zip_help(user_choice[2:])
            else:
                clear()
                base_help()

        elif user_choice in ['CLS', 'CLEAR']:
            clear()

        elif user_choice in ['Q', 'QUIT', ' ']:
            clear()
            return

        else:
            continue

    return


if __name__ == '__main__':
    os.chdir('c:\\temp\\one')
    main_menu()
