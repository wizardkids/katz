"""
katz.py

Richard E. Rawson
2019-12-10

command-line zip archiving utility
    1. list all files within the archive
    3. add file(s), optionally including subfolders, from any directory on disk
    4. extract all or selected file(s) from the archive
    5. remove file(s) or folders from the archive
    6. test the integrity of the archive
    7. perform shell commands including dir, cls, and cd
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

# todo -- Change all docstrings to that the information in them is useful
# todo -- for someone who wants to use these functions in another script

# feature: add a config file that, among possibly other things, configures a starting directory

# feature: add ability to save last os.getcwd()


# feature: -- Version 3:
#       -- 1. Write katz so it can be used as an importable module.
#       -- 2. Add support for importing into other scripts so that, for example, downloaded archives are extracted automatically

# feature: -- Version 4:
#       -- Add support for other archiving formats, including tar and gzip


# declare global variables
dsh, slsh = '=', '/'

# shell_cmds dict holds help information for commands
shell_cmds = {
    'DIR': 'Displays a list of files and subdirectories in a directory.\n\nDIR [drive:][path][filename]\n',
    'CD': 'Displays the name of or changes the current directory.\n\nCD [/D][drive:][path]\n\n".." changes to the parent directory.\n',
    'CLS': 'Clears the screen. ("CLEAR" on Unix systems.)\n',
    'OPEN': '-- Open an existing zip file. Optionally include a path. The zip extension does need to be entered:\n         prompt> o data    # opens data.zip.\n\n-- For easiest usage, use the "cd" command to change the current directory to the directory containing the zip file that you want to work with.\n',
    'NEW': 'Create a new zip file in the current directory or, if a path is supplied, in another directory. katz 1.0 archives files using only the zip file format (not gzip or tar). File compression is automatic.\n',
    'LIST': '<L>ist all the files in the archive. In contrast, <DIR> lists files in a directory on disk, while <L>ist produces a list of files in the archive.\n',
    'ADD': '-- Use the "cd" command to navigate to the directory holding files you want to add.\n\n-- Even if you include the name of your archive in the list of files to <A>dd, "katz" cannot add a zip file to itself.\n\n-- For speed, three methods are provided for identifying files that you want to <A>dd. Don\'t mix methods! You can mix numbers and ranges, though. Examples:\n     (1) a comma-separated list of numbers or ranges\n     (2) "all" to add all files\n     (3) wildcard characters (*, ?) details.\n\n--<A>dding folders by naming a folder is not permitted.',
    'EXTRACT': '-- Files are extracted to a subfolder of the directory holding the open zip file, and the new folder has the same name as the archive file. This location/name is not configurable.\n\n--If the directory already exists, <E>xtract will not overwrite files without the user\'s permission.\n\n-- <E>xtract provides a numbered list of files to <E>xtract. To select files for extraction, you can mix individual "file numbers" and ranges. Examples of different ways of identifying files for extraction:\n     (1) 1, 2, 8, 4  [order does not matter]\n     (2) 3-8, 11, 14  [mix a range and numbers]\n     (3) enter a folder name\n     (4) all  [extracts all files]\n\nSYMLINKS:\n"katz" will archive file and folder symlinks. When extracted, files/folders will not extract as a symlink but as the original files/folders.\n',
    'REMOVE': '-- <R>emoves files or a single folder from the archive. This operation cannot be reversed! If the specified folder has subfolders, only the files in the folder will be removed; subfolders (and contents) will be retained. "katz" will confirm before removing any files or folders from the archive.\n\n-- Generally, "katz" retains folder structure when <A>dding files. Files in the same directory as the archive file are placed in a folder of the same name holding the archive file. However, some archive files may have files in the "root"directory. <L>ist will designate the "folder" for these files with a ".". To remove these files, use "." as the folder name. \n',
    'TEST': '<T>est the integrity of the archive. SPECIAL NOTE: If you archive a corrupted file, testing will not identify the fact that it is corrupted! Presumably, it was archived perfectly well as a corrupted file!\n',
    'MENU': '<M>enu shows a formatted menu of available commands.\n',
    'HELP': 'HELP is helpless.\n',
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
    'TEST': 'TEST',
    'M': 'MENU',
    'MENU': 'MENU',
    'B': 'ABOUT',
    'ABOUT': 'ABOUT'}

# the following list is used in sub_menu() to filter zip-file commands
command_list = ['DIR', 'CLS', 'CLEAR', 'EXIT', 'N', 'NEW', \
                'O', 'OPEN', 'CD', 'CD.', 'CD..', '.', '..', \
                'H', 'HELP','Q', 'QUIT', 'A', 'L', 'A', 'E', 'R', 'T', 'M', "MENU"]

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


def newFile(file):
    """
    Create a new zip file. If a path is included, the current directory will be changed to that path. If "file" does not include an extension, ".zip" is added to "file".

    Paths entered by users can contain a plethora of errors including spelling errors, non-existant paths, and names that don't meet OS requirements. Also, the python zipfile module does not require that zip files have a .zip extension, but such an extension makes life easier for the user and is required by this program.

    A simple testing strategy is employed: see if the new file can be opened. A multitude of errors are tested all at once.

    Arguments:
        file {str} -- assumed to be [path/]filename

    Returns:
        full_filename {str} -- a validated absolute path/filename.zip
                               or an empty string
    """

    # "cmd file" pattern may be entered at the command line. In this
    # function, "cmd" is assumed to be "new"
    # "file", if present, is assumed to be a [path/]file.
    # if "file" is an empty string, get a [path/]filename from the user
    if not file:
        file = input("\nName of archive: ").strip()

    # if user entered a "file", test it, then parse it
    else:
        # if user did not enter an extension, add .zip
        # if user entered the wrong extension, change it
        try:
            if Path(file).suffix == '':
                file = file + '.zip'
            elif len(file) >= 4:
                if file[-4:].upper() != '.ZIP':
                    file = file[:-4] + '.zip'

        except:
            # This exception will be raised if user entered an extension contains less than 3 characters, such as zipfile.?/ or zipfile.zp
            print('The system cannot find the path specified.\n')
            return ''

    file_name, full_path, full_filename = parse_full_filename(file)

    # if user entered an empty string or parse_full_filename() returned an empty string, return to the menu
    if not file_name:
        return ''

    # if file already exists, overwrite only if user agrees
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            msg = file_name + ' already exists. Overwrite? (Y/N) '
            overwrite = input(msg).upper()

            if overwrite == 'Y':
                with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', full_filename, 'created as new archive.\n')

            else:
                print(file_name, 'not created.\n')
                return ''

    # if file_name was not found, then we can create it!
    except (FileNotFoundError, OSError):
        try:
            with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                print('\n', full_filename, 'created as new archive.\n')

        except:
            print(file_name, 'not created.\n')
            return ''

    os.chdir(full_path)

    return full_filename


def openFile(file):
    """
    Open the archive "file". If a path is included, the current directory will be changed to that path. If "file" does not include an extension, ".zip" is added to "file" and the result is tested for validity to assure that a zip file is being opened.

    Paths entered by users can contain a plethora of errors including spelling errors, non-existant paths, and names that don't meet OS requirements. A simple testing strategy is employed: see if the file can be opened. A multitude of errors are tested all at once.

    Arguments:
        file {str} -- [path/]filename

    Returns:
        full_filename {str} -- absolute path/filename.zip
                               (e.g., c:\\mydata\\foo.zip)
    """

    # if no "file" was entered, get user input
    if not file:
        file = input("\nName of archive: ").strip()

    # if only a file.ext was entered, get the full path
    if '\\' not in file:
        file = str(Path(file).absolute())

        # if only a filename without an extention was entered, add .zip
        # we'll have to make sure it's a zip file, though
        if Path(file).suffix == '':
            file += '.zip'
            if not valid_path(file):
                print('File not a zip file.')
                return ''

    # test validity of what the user entered
    if not valid_path(file):
        print('The system cannot find the path specified.\n')
        return ''

    # change the working directory to directory containing the zip file
    file_name, full_path, full_filename = parse_full_filename(file)
    os.chdir(full_path)

    return full_filename


def listFiles(full_filename):
    """
    Print a numbered list of all the files and folders in the archive.

    Arguments:
        full_filename {str} -- absolute path/file name of the open archive file

    Returns:
        full_filename
    """
    # prevent user from <list>ing an archive when one isn't open
    if not full_filename:
        print("No archive file is open.")
        return full_filename

    # get the list of files from the archive
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        zip_files = sorted(zip_files, reverse=True)

    # if there are no files in the archive, print a notice, then return
    if len(zip_files) == 0:
        print('No files found in archive.')
        return full_filename

    # before printing the list, get and print the first
    # folder name in the archive
    current_directory = str(Path(zip_files[0]).parent)
    print(current_directory)

    # print a list of files in the archive
    for ndx, file in enumerate(zip_files):

        # when the directory changes, print it (left-justified)
        # by 5 spaces, along with a sequential number
        if current_directory != str(Path(file).parent):
            current_directory = str(Path(file).parent)
            if current_directory:
                print(current_directory)
            else:
                print('root/')

        # print files indented 5 spaces
        this_file = Path(file).name
        print(' '*3, ndx+1, '. ', this_file, sep='')

        # for convenience, pause after every 25 files
        cnt = ndx+1
        if len(zip_files) >= 25 and cnt >= 25 and cnt % 25 == 0:
            more = input(
                '--ENTER to continue; Q to quit--').strip().upper()
            if more == 'Q':
                break

    return full_filename


def addFiles(full_filename):
    """
    Add file(s) to the open archive from the selected directory and sub-directories.

    Tasks:
        (1) user should already have cd'ed to the folder containing files
    to be added
        (2) Print a numbered list of files in the user-selected folder.
        (3) Allow user to select files to add
        (4) Add the files to the archive, preserving the relative folder structure of the files/folders on disk

    Arguments:
        full_filename {str} -- absolute path/filename of archive file

    Returns:
        full_filename
    """
    # prevent user from <A>dding to an archive when one isn't open
    if not full_filename:
        print("No archive file is open.")
        return full_filename

    file_name, full_path, full_filename = parse_full_filename(full_filename)

    cwd = os.getcwd()

    # ==================================================
    # GENERATE A NUMBERED LIST OF ALL FILES IN THE USER-CHOSEN FOLDER
    #       AND PRINT THE LIST ON SCREEN
    # ==================================================

    dir_list = sorted(Path(cwd).glob('**/*.*'))

    cnt = 1
    for file in dir_list:
        # get the folder name relative to the cwd
        rel_path = os.path.relpath(Path(file).parent, Path(cwd).parent)

        # add the current file name to the relative path
        this_file = Path(rel_path, Path(file).name)
        print(cnt, '. ', str(this_file), sep='')
        cnt += 1

    # ==================================================
    # GET FROM USER THE FILES TO ADD TO THE ARCHIVE
    # ==================================================

    # example user input: 1, 3-5, 28, 52-68, 70 or *.t?t
    print('\nEnter:\n(1) a comma-separated combination of:\n    -- the number of the file(s) to add\n    -- a hyphenated list of sequential numbers\n(2) enter "all" to add all files\n(3) use wildcard characters (*, ?) to designate files')

    user_selection = input("\nFile(s) to add: ").strip()

    # if nothing is entered, return to menu
    if not user_selection:
        return full_filename

    # ========================================================
    # BASED ON USER'S CHOICES, CREATE A LIST OF THE ELIGIBLE FILES
    # ========================================================

    # get_chosen_files will work on a different list of files
    # depending on the function. For addFiles(), get_chosen_files
    # will get a list of files from disk, so set
    # source_list = dir_list
    source_list = dir_list.copy()

    # designate that addFiles() should not be able to reference folders
    folder_fnx = False
    selected_files = get_chosen_files(
        user_selection, full_filename, source_list, folder_fxn=False)

    # if selected_files returns empty, then there's no sense continuing
    if not selected_files:
        print('No files selected.')
        return full_filename


    # ==================================================
    # ADD THE FILES:
    #   files ALWAYS go into named folders
    # ==================================================

    # get a list of all the files that are in the archive
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        zip_files = sorted(zip_files, reverse=True)

    # namelist() formats paths as: foo/bar/bar.txt
    # need to change"/" into "\\""
    zip_files_temp_ = zip_files.copy()

    for ndx, file in enumerate(zip_files_temp_):
        file = file.replace('/', '\\')
        zip_files[ndx] = file

    # add files in selected_files to the archive
    # we want files in archive to appear in folders relative to the
    # current working directory. To do this, write the file as:
    #   path/filename
    # but, using "arcname", "rename" the file using a relative path
    with zipfile.ZipFile(full_filename, 'a', compression=zipfile.ZIP_DEFLATED) as f:

        for file in selected_files:

            # get the folder name relative to the cwd
            rel_path = os.path.relpath(Path(file).parent, Path(cwd).parent)

            # add the current file name to the relative path
            this_file = Path(rel_path, Path(file).name)

            # if the current file is not the archive file, itself,
            # add it to the archive
            if Path(file).name.upper() != file_name.upper():

                # if the current file is already in zip file, skip adding it
                if str(this_file) not in zip_files:

                    # archive will store the file not as the original
                    # file name, but as arcname
                    f.write(str(file), arcname=this_file)

    return full_filename


def extractFiles(full_filename):
    """
    Extract one or more files from an archive.

    Tasks:
        (1) Provide a numbered list of archive contents
        (2) Provide various ways for user to select files to extract
        (3) Extract the files to a subdirectory with the same name as the archive

    Arguments:
        full_filename {str} -- absolute path/filename of the opened archive file

    Returns:
        full_filename
    """
    # prevent user from <extract>ing from an archive when one isn't open
    if not full_filename:
        print("No archive file is open.")
        return full_filename

    file_name, full_path, full_filename = parse_full_filename(full_filename)


    # ==============================================
    # GET A LIST FILES IN THE ARCHIVE AND PRINT IT
    # ==============================================

    full_filename = listFiles(full_filename)

    # generate a [list] of files in the archive
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
        return full_filename

    # using wildcard characters is not allowed
    if "*" in user_selection or "?" in user_selection:
        print('Use of wildcard characters is prohibited.')
        return full_filename

    # get_chosen_files will work on a different list of files
    # depending on the function. For extractFiles(), get_chosen_files
    # will get a list of files from the archive, so set
    # source_list = file_list
    source_list = file_list.copy()

    # designate that extractFiles() can reference folders
    folder_fxn = True

    selected_files = get_chosen_files(
        user_selection, full_filename, source_list, folder_fxn)


    # ==============================================
    # CONFIRM THE SELECTION OF FILES
    # ==============================================

    # if "selected_files" contains files, print the list; otherwise, return
    if selected_files:
        for file in selected_files:
            print(file)
    else:
        return full_filename

    confirm = input('\nExtract files (Y/N) ').upper()

    # return to the command line if user enters anything but "Y"
    if confirm != 'Y':
        return full_filename


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

    return full_filename


def removeFiles(full_filename):
    """
    Removes files/folders from the archive.

    Technical info: To remove a file, this function first create a temporary archive that holds all the original files except the one(s) targeted for removal. Then:
            (1) the temporary archive is tested for integrity
            (2) the original archive is deleted
            (3) the temporary archive is renamed as the original

    Arguments:
        full_filename {str} -- absolute path/filename of the opened archive file

    Returns:
        full_filename
    """
    # prevent user from <remove>ing from an archive when one isn't open
    if not full_filename:
        print("No archive file is open.")
        return full_filename

    file_name, full_path, full_filename = parse_full_filename(full_filename)

    # store the user's current working directory so it can be restored later
    cwd = os.getcwd()

    # make sure you are in the same directory as the zip file
    os.chdir(full_path)

    temporary_path = '_temp_' + file_name[:-4] + '_'
    temp_dir = str(Path(full_path, temporary_path))

    # unlikely, but... abort if "temporary" directory already exists
    if os.path.isdir(temporary_path):
        msg = '\nCannot remove files from archive, since ' + temporary_path + ' directory exists.\n'
        print('='*52, msg, '='*52, sep='')

        # return user to original working directory
        os.chdir(cwd)

        return full_filename

    # ===================================================
    # 1. GET AND PRINT A NUMBERED LIST OF FILES IN THE ARCHIVE
    # 2. GET FROM USER EITHER:
    #       A. THE NUMBER(s) OF THE FILE(s) TO REMOVE
    #       B. THE NAME OF THE FOLDER TO REMOVE
    # ===================================================

    # get a list of files in the archive and their total number
    with zipfile.ZipFile(full_filename, 'r') as f:
        file_list = f.namelist()
        file_list = sorted(file_list, reverse=True)
        num_files = len(file_list)

    # for the user, print a list of files and folders in the archive
    listFiles(full_filename)

    # get from the user the file or folder that should be removed
    print("\nEnter file number(s) or range(s) to")
    print('remove or, to remove a whole folder,')
    user_selection = input("type the name of the folder: ").strip()

    # if no file name is entered, return to menu
    if not user_selection.strip():

        # return user to original working directory
        os.chdir(cwd)

        return full_filename

    # get_chosen_files will work on a different list of files
    # depending on the function. For extractFiles(), get_chosen_files
    # will get a list of files from the archive, so set
    # source_list = file_list and set remove=True so get_chosen_files knows
    # that removeFiles() is calling it
    source_list = file_list.copy()

    # designate that removeFiles() can reference folders
    folder_fnx = True
    selected_files = get_chosen_files(
        user_selection, full_filename, source_list, folder_fxn=True)

    # if selected_files returns empty, then either the user
    # selected nothing valid or selected a folder
    if not selected_files:
        print('No files selected.')

        # return user to original working directory
        os.chdir(cwd)
        return full_filename

    # print a list of files destined for removal
    for file in selected_files:
        print(file)

    confirmed = input('\nRemove these files from the archive? (Y/N) ').strip().upper()

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

    # return user to original working directory
    os.chdir(cwd)

    return full_filename


def get_chosen_files(user_selection, full_filename, source_list, folder_fxn='False'):
    """
    Create a list of all the files selected by the user to add, extract, or remove. User enters one of the following, and all are handled differently:
        -- 'all'
        -- 1, 3-5, 28, 52-68, 70
        -- *.t?t
        -- a folder name

    This function must meet the needs of addFiles(), extractFiles(), and removeFiles(), where in addFiles(), we look in a list of files on disk to find selected files, and in extractFiles() and removeFiles() we look in a list of files in the archive to find selected files.

    Arguments:
        user_selection {[str]} -- [user-selected files... see above]
        source_list {[list]}
            - if coming from addFiles(), list of files in the cwd and subfolders (dir_list)
            - if coming from extractFiles() or removeFiles(), list of path/filenames of all files in archive (file_list)
        full_filename {[str]} -- [path+filename of archive file]
        folder_fxn {[boolean]} -- if True, this function will allow selected_files to be populated with relative paths, otherwise, selected_folders will be returned empty

    Returns:
        selected_files {[list]} -- [relative path]/filename of user-selected files]
    """

    # if user entered numbers, splitting creates a [list] of integers
    # &/or ranges; otherwise, it creates a [list] containing "all" or
    # a folder name
    user_files = user_selection.split(',')

    selected_files = []

    # set "folder_name" to True in the following bit of code if user
    # entered a folder name; otherwise "folder_name" will remain False
    folder_name = False

    # extractFiles() and removeFiles() get its files from the archive content
    # look for folders there; addFiles() will also execute this code, but the
    # result is not used since addFiles() does not use folders
    with zipfile.ZipFile(full_filename, 'r') as f:

        file_list = f.namelist()

        # cycle through all the folder names in the archive
        # if user's selection is a folder, we might as well record the files
        # that meet the criterion, for use in "elif folder:" below
        tentative_selected_files = []
        for file in file_list:
            this_path = Path(file).parent
            if str(this_path).upper() == user_selection.upper():
                tentative_selected_files.append(file)
                folder_name = True

    # user_selection='ALL', selected_files contains all files in cwd
    if user_selection.upper() == 'ALL':
        which_files = [str(x) for x in range(1, len(source_list)+1)]
        for file_number in which_files:
            selected_files.append(str(source_list[int(file_number)-1]))

    # if user_selection has wildcards, then filter the list of files
    # see https://pymotw.com/2/glob/
    elif '*' in user_selection or '?' in user_selection:
        folders = set()

        # generate a list of all folders in source_list
        for file in source_list:
            folders.add(str(Path(file).parent))

        # get all files in folders/subfolders that match "user_selection"
        for folder in folders:
            os.chdir(folder)
            f = glob.glob(user_selection)
            for i in f:
                file = Path(folder, i)
                selected_files.append(file)
                print(i)

    # process files if user entered a folder name
    elif folder_name:

        # removeFiles() and extractFiles() work properly with the relative
        # paths that are stored in an archive; addFiles() MUST have absolute
        # paths. The boolean "folder_fxn" flags that using relative paths is ok.
        if folder_fxn:
            selected_files = tentative_selected_files.copy()

        else:
            selected_files = []

    # if user is selecting files using their "file number", find those files
    # in "source_file"
    else:
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
                    return []
            # treating all other single digits
            else:
                try:
                    n = int(i)
                    which_files.append(str(n))
                except:
                    print(
                        '\nInvalid number(s) and folders excluded.')
                    return []

        for file_number in which_files:
            selected_files.append(source_list[int(file_number)-1])

    print()

    return selected_files


def testFiles(full_filename):
    """
    Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testing will not identify the fact that it is corrupted! Presumably, it was archived perfectly well as a corrupted file!
    """
    # prevent user from <test>ing an archive when one isn't open
    if not full_filename:
        print("No archive file is open.")
        return full_filename

    # first, test if it is a valid zip file
    if not zipfile.is_zipfile(full_filename):
        print('\nNot a valid zip file.')
        return full_filename

    # open the archive and test it using testzip()
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            tested_files = f.testzip()
            num_files = len(f.infolist())
    except:
        # if the file can't even be opened, then set tested_file to True
        # which is the same result as if testzip() found bad files in the archive
        tested_files = True

    if tested_files:
        print('Bad file found:', tested_files)
    else:
        print('\nTested ', num_files, ' files:  ',
              num_files, ' OK.  0 failed.', sep='')

    return full_filename


def about():
    """
    Provide a very little history behing the name "katz".
    """
    about = '''"katz" is a command-line zip file utility named after Phil Katz, the founder of PKWARE in 1989, the company that originated the ZIP file format that is still widely used today.'''

    print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
    print(fold(about, '', 52), '\n')

    return


def fold(txt, ndnt='     ', w=52):
    """
    Textwraps 'txt'; used by katzHelp() to wrap help text at column 52.
    """
    return textwrap.fill(txt, subsequent_indent=ndnt, width=w)


def katzHelp():
    """
    Provide basic information about shell commands used in "katz".
    """
    msg = '/'*23 + ' HELP ' + '/'*23
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')
    print('For help: cmd /? (example:  d /?)')
    print('\n', 'AVAILABLE SHELL COMMANDS:', sep='')
    for k, v in shell_cmds.items():
        if k == 'O' or k == 'N' or k == 'M':
            pass
        else:
            if k in ['QUIT', 'Q']:
                pass
            else:
                if k == 'EXIT':
                    print('EXIT, QUIT, Q')
                else:
                    print(k)

    print('\nAll commands are case insensitive. Most can use one\nletter (e.g., "o" instead of "open")')
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

    dir can also be issued with wildcard characters, such as:
        dir *.txt
        dir c:\mydata\*.xl?

    Keyword Arguments:
        switch {str} -- an OS path (default: {''})

    Returns: None
    """
    # preserve the user's current directory
    cwd = os.getcwd()

    # make sure "switch" is an absolute path, especially is
    # user entered ".."  or a subfolder
    file_name, full_path, full_filename = parse_full_filename(switch)

    try:
        # user might use wildcards to filter dir
        if '*' in switch or '?' in switch:
            os.chdir(full_path)
            d = 'dir ' + switch
            output = str(check_output(d, shell=True))

        # if user entered a path, change the cwd to path
        else:
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
        os.chdir(cwd)

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


def parse_input(entry, full_filename):
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

    # Format of some commands varies depending on OS.
    # It's easier to process only one version...
    if cmd == 'CD..':
        cmd, switch = 'CD', '..'
    if cmd == 'DIR..':
        cmd, switch = 'DIR', '..'
    if cmd in ['CLS', 'CLS.', 'CLS..', 'CLEAR', 'CLEAR.', 'CLEAR..']:
        cmd = 'CLS'

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

    elif cmd in ['EXIT', 'QUIT', 'Q']:
        pass

    elif (cmd == 'HELP' or cmd == 'H') and not switch:
        clear()
        katzHelp()

    elif cmd == 'CD':
        cd(switch)

    elif cmd[:3] == 'DIR':
        dir(switch)

    elif cmd == 'CLS':
        clear()

    elif cmd == 'N' or cmd == 'NEW':
        full_filename = newFile(switch)

    elif cmd == 'O' or cmd == 'OPEN':
        full_filename = openFile(switch)

    elif cmd == 'L' or cmd == 'LIST':
        full_filename = listFiles(full_filename)

    elif cmd == 'A' or cmd == 'ADD':
        full_filename = addFiles(full_filename)

    elif cmd == 'E' or cmd == 'EXTRACT':
        full_filename = extractFiles(full_filename)

    elif cmd == 'R' or cmd == 'REMOVE':
        full_filename = removeFiles(full_filename)

    elif cmd == 'T' or cmd == 'TEST':
            full_filename = testFiles(full_filename)

    elif cmd == 'B':
        about()

    elif cmd == 'M' or cmd == 'MENU':
        show_menu()

    elif not cmd:
        pass

    print()

    return cmd, full_filename


def show_menu():
    """
    Display a formatted menu of available commands.
    """
    print(
        '\n<O>pen file   <N>ew file   <L>ist  <A>dd\n<E>xtract     <R>emove     <T>est\n<M>enu        <H>elp       a<B>out\n\n<DIR [path]>  <CD [path]>  <CLS>')
    print('')
    return None


def main_menu():
    """
    Display initial "splash" screen, then expose "shell" that accepts shell commands.
    """
    full_filename = ''

    # ===============================================
    # PRINT THE PROGRAM HEADER... JUST ONCE
    # ===============================================
    version_num = "2.0"
    revision_number = get_revision_number()
    print("\nkatz ", version_num, '.', revision_number, " - a command-line archiving utility", sep='')
    show_menu()


    # ===============================================
    # GENERATE THE MAIN MENU IN A LOOP
    # ===============================================

    while True:

        # ===============================================
        # GET A COMMAND FROM THE USER
        # ===============================================
        prompt = "(katz) " + os.getcwd() + ">"
        entry = input(prompt).strip()

        cmd, full_filename = parse_input(entry, full_filename)

        if cmd in ['EXIT', 'QUIT', 'Q']:
            break


if __name__ == '__main__':
    os.chdir("c:\\temp\\one")
    main_menu()
