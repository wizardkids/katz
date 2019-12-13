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
from pathlib import Path, PurePath
from subprocess import check_output

# the following if... prevents a warning being issued to user if they try to add
# a duplicate file to an archive; this warning is handled in add_file()
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# todo -- version 2: Create an interface that behaves largely like a Windows command window (cmd.exe) with special (but limited) capabilities regarding management of zip files.

# todo -- version 3: Add support for other archiving formats, including tar and gzip

# todo -- version 4: Add support for importing into other scripts so that, for example, downloaded archives are extracted automatically

# declare global variables
dsh, slsh = '=', '/'

shell_cmds = {
    'DIR': 'Displays a list of files and subdirectories in a directory.\n\nDIR [drive:][path][filename]\n',
    'CD': 'Displays the name of or changes the current directory.\n\nCD [/D][drive:][path]\n\n".." changes to the parent directory.\n',
    'CLS': 'Clears the screen. ("CLEAR" on Unix systems.\n)',
    'OPEN': 'Open an existing zip file. Optionally include a path.\n',
    'O': 'Open an existing zip file. Optionally include a path.\n',
    'NEW': 'Create a new zip file. Optionally include a path.\n',
    'N': 'Create a new zip file. Optionally include a path.\n',
    'EXIT': 'Quits the shell and the current script.\n',
    }

command_list = ['DIR', 'CLS', 'CLEAR', 'EXIT', 'N', 'NEW', 'O', 'OPEN', 'CD', 'CD.', 'CD..', '.', '..',  'H', 'HELP','Q', 'QUIT', 'A', 'L', 'A', 'E', 'R', 'T']


def create_new(switch):
    """
    Create a new zip file.
    """
    # if the user included a path/file on the command line...
    if switch:
        file_name = Path(switch).name
        full_path = str(Path(switch).parent.absolute())
        full_filename = str(Path(Path(full_path) / file_name))
    # otherwise, get a filename from the user
    else:
        full_path = input("\nName of archive: ").strip()
        file_name = Path(full_path).name
        full_path = str(Path(full_path).parent.absolute())
        full_filename = str(Path(Path(full_path) / file_name))
        print()

    # if there's no full_path, return to the menu
    if not file_name:
        return '', '', ''
    # if a file was entered, but not a zip file...
    if Path(full_filename).suffix.upper() != '.ZIP':
        print('File is not a zip file.\n')
        return '', '', ''

    try:
        os.chdir(full_path)
    except:
        print('The system cannot find the path specified.')
        return '', '', ''

    # if file already exists, issue "overwrite" warning
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            msg = file_name + ' already exists. Overwrite? (Y/N) '
            overwrite = input(msg).upper()

            if overwrite == 'Y':
                with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', file_name, 'created as new archive.\n')
                return full_path, file_name

            else:
                print(file_name, 'not created.\n')
                return '', '', ''

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            print('\n', file_name, 'created as new archive.\n')

        return file_name, full_path, full_filename


def open_archive(switch):
    """
    Open an archive and list the files in the archive. If a path is entered, chdir() to that path and then save the filename as file_name.
    """
    # if a path/file was entered, then use the path to chdir()
    if switch and Path(switch).is_file():
        file_name = Path(switch).name
        full_path = str(Path(switch).parent.absolute())
        full_filename = str(Path(Path(full_path) / file_name))
        os.chdir(full_path)

    # if an only a path was entered, or not argument was entered...
    else:
        print('File not found.')
        full_path = input("\nName of archive: ").strip()
        print()
        file_name = Path(full_path).name
        full_path = str(Path(full_path).parent.absolute())
        full_filename = str(Path(Path(full_path) / file_name))
        os.chdir(full_path)

    # if no file_name was entered, return to menu
    if not file_name:
        return '', '', ''

    # sort out possible errors in file_name
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            pass
    except FileNotFoundError:
        print('File not found.\n')
        return '', '', ''
    except OSError:
        print('Invalid file name.\n')
        return '', '', ''
    except zipfile.BadZipFile:
        print('File is not a zip file.\n')
        return '', '', ''
    except:
        print('Encountered an unpredicable error.\n')
        return '', '', ''

    return file_name, full_path, full_filename


def list_files(file_name, full_path, full_filename):
    """
    Generate a numbered list of all the files and folders in the archive.
    """
    with zipfile.ZipFile(full_filename, 'r') as f:
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
            # print(' '*3, ndx+1, '. ', this_file, sep='')
            print(' '*3, this_file, sep='')

            # pause after every 25 files
            cnt = ndx+1
            if len(zip_files) >= 25 and cnt >= 25 and cnt % 25 == 0:
                more = input(
                    '--ENTER to continue; Q to quit--').strip().upper()
                if more == 'Q':
                    break

    return file_name, full_path, full_filename


def add_file(file_name, full_path, full_filename):
    """
    Add one, many, or all files from the user-designated folder, and optionally include subfolders of that folder. Uses various methods for choosing files to add, optimized for speed of selection.
    """
    current_directory = os.getcwd()

    msg = 'CURRENT DIRECTORY: ' + current_directory
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

    # ==================================================
    # GET THE SOURCE DIRECTORY FROM THE USER
    # ==================================================

    # get directory containing files that you want to add
    while True:
        print('\nEnter "." to use current directory.')
        dir = input("Directory containing files to add: ").strip()

        # if user enters nothing, return to the menu
        if not dir:
            return file_name, full_path, full_filename

        if dir == '.':
            dir = Path(full_path).absolute()

        if not Path(dir).exists() or not Path(dir).is_dir():
            print('\nEntry does not exist or is not a directory. Re-enter.')
            continue
        else:
            subs = input('Include subdirectories (Y/N): ').strip().upper()
            subs = True if subs == 'Y' else False
            print()
            break

    # ==================================================
    # GENERATE A NUMBERED LIST OF ALL FILES IN THE USER-CHOSEN FOLDER
    # ==================================================

    if subs:
        # file_list contains subfolders
        file_list = sorted(Path(dir).glob('**/*.*'))
    else:
        # file_list contains contents of only the "dir" folder
        file_list = sorted(Path(dir).glob('*.*'))

    with zipfile.ZipFile(file_name, 'a', compression=zipfile.ZIP_DEFLATED) as f:
        cnt = 1
        for file in file_list:
            # this code finds the relative folder name
            file_parts = Path(file).parts
            for ndx, i in enumerate(file_parts):
                if i not in Path(dir).parent.parts:
                    loc = ndx
                    break
            # first rel_folder is the part of the "dir" path
            # INCLUDING AND AFTER the folder holding the zip file
            rel_folder = '\\'.join(file_parts[loc:-1])
            rel_folder = Path(rel_folder, Path(file).name)
            print(cnt, '. ', rel_folder, sep='')
            cnt += 1

    # ==================================================
    # GET FROM USER THE FILES TO ADD TO THE ARCHIVE
    #   user can choose individual files or "all" files
    # ==================================================

    while True:
        # let user choose which file(s) to add
        # example user input: 1, 3-5, 28, 52-68, 70 or *.t?t
        print('\nEnter:\n(1) a comma-separated combination of:\n    -- the number of the file(s) to add\n    -- a hyphenated list of sequential numbers\n(2) enter "all" to add all files\n(3) use wildcard characters (*, ?) to designate files')

        choice = input("\nFile(s) to add: ").strip()

        # if nothing is entered, return to menu
        if not choice:
            os.chdir(current_directory)
            return file_name, full_path, full_filename

        # ========================================================
        # BASED ON USER'S CHOICES, CREATE A LIST OF THE ELIGIBLE FILES
        # ========================================================

        add_files = []  # list that contains file names w/ paths to add
        if choice.upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(file_list)+1)]
            for file_number in which_files:
                add_files.append(str(file_list[int(file_number)-1]))

        # see https://pymotw.com/2/glob/
        elif '*' in choice or '?' in choice:
            folders = set()

            # generate a list of all folders in file_list
            for file in file_list:
                folders.add(str(Path(file).parent))

            # get all files in subfolders that match "choice"
            if subs:
                for folder in folders:
                    os.chdir(folder)
                    f = glob.glob(choice)
                    for i in f:
                        file = Path(folder, i)
                        add_files.append(file)
                        print(i)
            # get all files that match "choice" but only in "dir"
            else:
                os.chdir(dir)
                f = glob.glob(choice)
                for i in f:
                    file = Path(folder, i)
                    add_files.append(file)
                    print(f)

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
                add_files.append(file_list[int(file_number)-1])

        break

    os.chdir(current_directory)

    # ==================================================
    # ADD THE FILES:
    #   files ALWAYS go into named folders
    # ==================================================

    # get a list of all the files that are in the archive
    with zipfile.ZipFile(full_filename) as f:
        zip_files = f.namelist()

    # namelist() formats paths as: foo/bar/bar.txt
    # need to change"/" into "\\""
    zip_files_temp = zip_files.copy()
    for ndx, file in enumerate(zip_files_temp):
        file = file.replace('/', '\\')
        zip_files[ndx] = file

    with zipfile.ZipFile(file_name, 'a', compression=zipfile.ZIP_DEFLATED) as f:
        for file in add_files:
            # this code finds the relative folder name
            file_parts = Path(file).parts
            for ndx, i in enumerate(file_parts):
                if i not in Path(dir).parent.parts:
                    loc = ndx
                    break
            # first rel_folder is the part of the "dir" path
            # INCLUDING AND AFTER the folder holding the zip file
            rel_folder = '\\'.join(file_parts[loc:-1])
            rel_folder = Path(rel_folder, Path(file).name)

            if Path(file).name != file_name:  # katz won't add the zip to itself
                f.write(file, arcname=rel_folder)

    return file_name, full_path, full_filename


def extract_file(file_name, full_path, full_filename):
    """
    Extract one or more files from an archive.
    """
    # get a list files in the archive and number them
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_info = f.infolist()
        num_files = [str(x) for x in range(1, len(zip_info)+1)]
        num_files.append(' ')

    while True:
        # print a list of files in the archive
        file_name, full_path, full_filename = list_files(
            file_name, full_path, full_filename)

        # let user choose which file(s) to extract
        # sample user input: 1, 3-5, 28, 52-68, 70
        print(
            '\nEnter a comma-separated combination of:\n  -- the number of the file(s) to extract\n  -- a hyphenated list of sequential numbers\n  -- or enter "all" to extract all files\n')
        choice = input("File number(s) to extract: ")

        # if no choice is made, return to menu
        if not choice.strip():
            return file_name, full_path, full_filename

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
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        print('\nExtracting...')
        extract_location = full_path + '\\' + file_name[:-4]

        # extract designated files and print the files on screen
        for ndx, file in enumerate(zip_files):
            if ndx+1 in which_files:
                this_file = zip_files[ndx]
                print('\n', this_file, sep='')

                # prevent an unintentional file overwrite of this_file
                # in the directory where files will be extracted
                if os.path.isfile(os.path.join(extract_location, this_file)):
                    ok = input(
                        'Overwrite file on disk? (Y/N): ').strip().upper()
                    if ok == 'N':
                        print('\nSkipping', this_file)
                        continue
                # extract the file here
                f.extract(this_file, path=extract_location)

    return file_name, full_path, full_filename


def remove_file(file_name, full_path, full_filename):
    """
    This utility removes only one file at a time.

    Technical info: To remove a file, this function first create a temporary archive that holds all the original files except the one targeted for removal. The temporary archive is tested for integrity; the original archive is deleted; the temporary archive is renamed as the original.
    """
    # full path to the user's zip file
    full_filename = os.path.join(full_path, file_name)

    # make sure you are in the same directory as the zip file
    os.chdir(full_path)

    # unlikely, but... abort if "temporary" directory already exists
    temporary_path = '_temp_' + file_name[:-4] + '_'
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

    # get a list of files in the archive and their total number
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        num_files = len(f.namelist())

    while True:
        # for the user, print a list of files and folders in the archive
        file_name, full_path, full_filename = list_files(
            file_name, full_path, full_filename)

        # get from the user the file or folder that should be removed
        print("\nEnter file number(s) or range(s) to")
        print('remove or, to remove a whole folder,')
        choice = input("type the name of the folder: ").strip()

        # if no file name is entered, return to menu
        if not choice.strip():
            return file_name, full_path, full_filename

        # determine if "choice" is an integer/range or a folder
        for c in choice:
            # if the entire string comprised digits or '-'
            if c in string.digits or c in [',', ' ', '-']:
                choice_numbers = True
            else:
                choice_numbers = False
                break

        # if choice is an integer or range, get a list of integers
        if choice_numbers:
            which_files = process_numbers(choice, num_files)
            # if process_numbers returns an empty which_files, then
            # something went wrong
            if not which_files:
                msg = '\nInvalid entry. Try again.\n'
                print('='*52, msg, '='*52, sep='')
                continue

            # otherwise print a list of files destined for removal
            else:
                print()
                for ndx, file in enumerate(zip_files):
                    if ndx+1 in which_files:
                        print(file)
                confirmed = input('\nRemove these files from the archive? (Y/N) ').strip().upper()
                if confirmed == 'Y':
                    break

        # otherwise, process "choice" as a folder
        else:
            # deny ability to delete root/ folder
            if 'ROOT' in choice.upper():
                msg = '\nOperation cannot be completed.\nSee "HELP >> <R>emove Files".\n'
                print('='*52, msg, '='*52, sep='')
                continue
            choice = choice.replace('/', '\\')

            # confirm the user's choice of folders to remove by
            # looking for the path in "choice" within zip_files
            for ndx, line in enumerate(zip_files):
                # if "line" contains the path in "choice"
                line_path = line.split('/')[:-1]
                line_path = '\\'.join(line_path).upper()
                if choice.upper() == line_path:
                    confirmed = input('\nRemove folder: ' + choice + ' (Y/N) ').upper()
                    break
                if ndx == num_files-1:
                    msg = '\nCould not find the folder "' + choice + '" in the archive.\n'
                    print('='*52, msg, '='*52, sep='')
                    confirmed = 'N'
                    continue
            if confirmed == 'Y':
                break

    # ===============================================
    # REMOVE THE FILES DESIGNATED BY THE USER
    # ===============================================

    if confirmed == 'Y':
        # create the directory that will hold files temporarily
        os.mkdir(temporary_path)

        # if "choice" is a list of numbers, extract all numbered files except those in "choice"
        if choice_numbers:
            # which_files contains a list of integers denoting files to remove
            with zipfile.ZipFile(full_filename, 'r') as f:
                # extract all the files to "temporary_path" except
                # the file user has chosen
                for ndx, file in enumerate(zip_files):
                    if ndx+1 not in which_files:
                        f.extract(file, path=temporary_path)

        # if choice is a folder name, extract all files except ones in that folder
        else:
            with zipfile.ZipFile(full_filename, 'r') as f:
                # extract all the files to "temporary_path" except
                # the file user has chosen
                for file in zip_files:
                    line_path = file.split('/')[:-1]
                    line_path = '\\'.join(line_path).upper()
                    if choice.upper() != line_path:
                        f.extract(file, path=temporary_path)

        # get relative path to temporary directory
        cwd = full_path + '\\' + temporary_path
        rel_dir = os.path.relpath(cwd, cwd)

        # add all the extracted files to _temp_zipfile_.zip
        with zipfile.ZipFile('_temp_zipfile_.zip', 'w', compression=zipfile.ZIP_DEFLATED) as f:
            # change directory to the temporary directory, which contains all files in the archive, except the file destined for removal
            os.chdir(temporary_path)

            # Iterate over all the files in the root directory
            # write each file to the temporary zip file
            for folderName, subfolders, filenames in os.walk(rel_dir, followlinks=True):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # add file to zip
                    f.write(filePath)

        # ===============================================
        # CLEAN UP TEMPORARY FILES AND DIRECTORY
        # ===============================================

        # change back to directory with zip file in it
        os.chdir(full_path)

        # test the temporary archive before deleting the original one
        if not zipfile.is_zipfile('_temp_zipfile_.zip'):
            msg = '\nUnknown error. Aborting removal of file.\n'
            print('='*52, msg, '='*52, sep='')

        # open and test temporary archive; if successful, delete original and rename temporary zip
        try:
            with zipfile.ZipFile('_temp_zipfile_.zip', 'r') as f:
                if f.testzip():
                    raise Exception
            # delete file_name
            os.remove(file_name)
            # rename _temp_zipfile_.zip to file_name
            os.rename('_temp_zipfile_.zip', file_name)
        except:
            msg = '\nUnknown error. Aborting removal of file.\n'
            print('='*52, msg, '='*52, sep='')

        # delete "temporary" file even if exception was raised in previous line
        if os.path.isfile('_temp_zipfile_.zip'):
            try:
                os.remove('_temp_zipfile_.zip')
            except:
                msg = '\nCannot complete operation. _temp_zipfile_.zip is being used by another process.\n'
                print('='*52, msg, '='*52, sep='')

        # delete "temporary" dir even if exception was raised in previous line
        if os.path.isdir(temporary_path):
            try:
                shutil.rmtree(temporary_path, ignore_errors=False)
            except PermissionError:
                msg = '\nCannot complete operation. A file or folder in ' + temporary_path + ' is being used by another process.\n'
                print('='*52, msg, '='*52, sep='')

    return file_name, full_path, full_filename


def process_numbers(choice, num_files):
    try:
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
                        which_files.append(int(x))
                except:
                    print(
                        '\nrange of numbers was excluded. Did you comma-separate values?')
                    which_files = []
                    break
            # treating all other single digits
            else:
                try:
                    which_files.append(int(i))
                except:
                    print(
                        '\nInvalid number(s) excluded. Did you comma-separate values?')
                    which_files = []
                    break
    except:
        print('nEncountered an error process entry. Try again.')

    # check validity of file numbers in which_files
    valid_numbers = range(1, num_files+1)
    for n in which_files:
        if n not in valid_numbers:
            which_files = []
            break

    return which_files


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
    print(fold(about, '', 52))

    return


def fold(txt, ndnt='     ', w=52):
    """
    Textwraps 'txt'; used by help() to wrap help text at column 52.
    """
    return textwrap.fill(txt, subsequent_indent=ndnt, width=w)

def base_help():
    msg = '/'*23 + ' HELP ' + '/'*23
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')
    print('Help for shell commands: cmd /? (example: dir /?)')
    print('\n', 'AVAILABLE SHELL COMMANDS:', sep='')
    for k, v in shell_cmds.items():
        if k == 'O' or k == 'N':
            pass
        else:
            print(k)
    print()
    print('Help for zip file commands: help [cmd] (example: help o)')
    print('\n', 'AVAILABLE ZIP FILE COMMANDS:', sep='')
    print('L or LIST')
    print('A or ADD')
    print('E or EXTRACT')
    print('R or REMOVE')
    print('T or TEST')
    print('\nAll commands are case insensitive.')
    print( dsh*52, '\n', '/'*52, '\n', dsh*52, sep='')
    print()


def shell_help(command):
    print(shell_cmds[command])


def zip_help(switch):
    """
    A help function.
    """
    open1_txt = """
    Enter a filename, including a .zip extension. For easiest usage, use the "cd" command to change the current directory to the directory containing the zip file that you want to work with.
"""

    new_txt = """
    katz 1.0 archives files using only the zip file format (not gzip or tar). File compression is automatic. For easiest usage, use the "cd" command to change the current directory to the directory containing the zip file that you want to work with.
"""

    list_txt = """
    <L>ist all the files in the archive. <DIR> lists files in a directory on disk, while <L>ist produces a list of files in the archive.
"""

    add1_txt = """
    -- <A>dd provides a list of files that you can <A>dd to the archive.
"""
    add2_txt = """
    -- Enter a "." to get a list of files from the same directory holding the zip file, or enter a path to another directory. Files in the same directory as the zip file will be added to a folder with the same name as the folder holding the zip file.
"""
    add3_txt = """
    -- You can optionally include files in all subdirectories. The subdirectory structure containing the files you want to add will be preserved in the archive file. Even if you include the name of your archive in the list of files to <A>dd, "katz" cannot add a zip file to itself.
"""
    add4_txt = """
    -- For speed, three methods are provided for identifying files that you want to <A>dd. Don't mix methods! You can mix numbers and ranges, though. See the second item under <E>tract, below, for details.
"""

    extract1_txt = """
    -- Files are extracted to a subfolder with the same name as the archive file. This location is not configurable.
"""
    extract2_txt = """
    -- <E>xtract provides a numbered list of files to <E>xtract. To select files for extraction, you can mix individual "file numbers" and ranges. Examples of using numbers to identify individual files:
"""
    extract3_txt = """
        (1) 1, 2, 8, 4  [order does not matter]
"""
    extract4_txt = """
        (2) 3-8, 11, 14  [mix a range and individual numbers]
"""
    extract5_txt = """
        (3) all  [extracts all files]
"""
    extract6_txt = """
    SYMLINKS:
"""
    extract7_txt = """
        "katz" will archive file and folder symlinks. When extracted, files/folders will not extract as a symlinks but as the original files/folders.
"""

    remove_txt1 = """
    <R>emoves files or a single folder from the archive. This operation cannot be reversed! If the specified folder has subfolders, only the files in the folder will be removed; subfolders (and contents) will be retained. "katz" will confirm before removing any files or folders.
"""
    remove_txt2 = """
    Removing all files in the archive by attempting to remove the "root" folder is disallowed. To remove all files/folders, delete the zip file, instead.
"""

    test_txt = """
    <T>est the integrity of the archive. SPECIAL NOTE: If you archive a corrupted file, testing will not identify the fact that it is corrupted!
"""
    switch = switch.strip().upper()

    if switch == 'O' or switch == 'OPEN':
        print('\nOpen File')
        print(fold(open1_txt, '          '))

    elif switch == 'N' or switch == 'NEW':
        print('\nNew File')
        print(fold(new_txt))

    elif switch == 'L' or switch == 'LIST':
        print('\nList Files')
        print(fold(list_txt))

    elif switch == 'A' or switch == 'ADD':
        print('\nAdd Files')
        print(fold(add1_txt, '          '))
        print(fold(add2_txt, '          '))
        print(fold(add3_txt, '          '))
        print(fold(add4_txt, '          '))

    elif switch == 'E' or switch == 'EXTRACT':
        print('\nExtract Files')
        print(fold(extract1_txt, '          '))
        print(fold(extract2_txt, '          '))
        print(fold(extract3_txt, '          '))
        print(fold(extract4_txt, '          '))
        print(fold(extract5_txt, '          '))
        print(fold(extract6_txt))
        print(fold(extract7_txt, '          '))

    elif switch == 'R' or switch == 'REMOVE':
        print('\nRemove File')
        print(fold(remove_txt1, '          '))
        print(fold(remove_txt2, '          '))

    elif switch == 'T' or switch == 'TEST':
        print('\nTest Archive')
        print(fold(test_txt))

    else:
        print(switch, 'is not recognized as a valid zip-file command.')

    print()

    return


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


def dir(full_path=''):
    """
    Run a OS dir command.

    Keyword Arguments:
        full_path {str or WindowsPath object} -- contains the path for which to get a directory listing
        default: {''})
    """
     # full_path is passed by parse_input() as a WindowsPath object
    full_path = str(full_path)
    # remove quotes from full_path, if present
    full_path = full_path.replace('"', '')
    full_path = full_path.replace("'", '')

    try:
        # preserve the user's current directory
        current_directory = os.getcwd()
        # change the cwd if a path was entered
        if full_path:
            # if user enteres "dir subfolder", next line
            # provides the whole path
            full_path = Path(full_path).absolute()
            os.chdir(full_path)
        output = str(check_output('dir', shell=True))
        out = output.split('\\r\\n')
        # print the output of 'dir'
        print()
        for ndx, i in enumerate(out[:-1]):
            if ndx == 0:
                print(i[2:])
            else:
                print(i)
        # restore the user's current directory
        os.chdir(current_directory)
    except:
        print('The system cannot find the path specified: ', full_path)
    print()


def cd(cmd='', switch='', full_path=''):
    """
    Run an OS cd (change directory) command.

    Keyword Arguments:
        cmd {str} -- the command to run (cd) (default: {''})
        switch {str} -- the path to cd to; may be .. (default: {''})
        full_path {WindowsPath object} -- the path to cd to; needed in case cd.. is entered (default: {''})
    """
    try:
        if cmd[2:] == '..' or switch == '..':
            os.chdir(full_path.absolute().parent)
        else:
            try:
                full_path = Path(switch).absolute()
                os.chdir(full_path)
            except:
                print('The system cannot find the path specified.')
    except:
        print('The system cannot find the path specified.')
    print()


def clear():
    """
    Run a cls or clear command to clear the terminal.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def parse_input(entry):
    """
    This function takes whatever the user entered at the command line and divides it into a command and then whatever follows. Then it uses the command portion to figure out what to do.

    Once a zip file is opened, or a new zip file is created, submenu commands (zip file commands) become available.

    Arguments:
        entry {str} -- takes whatever the user entered at the command line
    """
    # ===============================================
    # PROCESS THE USER'S ENTRY, WHICH WILL BE EITHER:
    #   1. CMD [/?]
    #   2. CMD [PATH][FILE]
    #   3. AN UNRECOGNIZABLE ENTRY
    # ===============================================

    # command only
    if entry.find(' ') == -1:
        cmd, switch = entry, ''

    # command + space + switch
    else:
        space_ndx = entry.find(' ')
        cmd, switch = entry[:space_ndx], entry[space_ndx+1:]
        # remove quotes from switch, if present
        switch = switch.replace('"', '')
        switch = switch.replace("'", '')

    if cmd and cmd not in command_list:
        msg = cmd + ' is not recognized as a valid command.\n'
        print(msg)

    # Windows OS understands "CD.."" and "CD .."" as equivalent
    # commands, but it's better to process only one version...
    if cmd == 'CD' and switch == '..':
        cmd, switch = 'CD..', ''

    # ===============================================
    # FIRST PART OF ENTRY IS A COMMAND
    # SECOND PART OF ENTRY WILL BE EITHER:
    #   1. A PATH[/FILE]
    #   2 /? (REQUEST FOR HELP)
    #   3. UNRECOGNIZABLE
    # ===============================================

    # get path and, potentially, file name
    if switch == '/?':
        file_name, full_path = '', ''
    else:
        full_path = Path(switch)

        # if it's a directory, then there's no file name
        if full_path.is_dir():
            file_name = ''
        # if there's a file, then the "parent" is the path
        else:
            file_name = full_path.name
            full_path = full_path.parent.absolute()

        # if full_path is not a directory,
        # then full_filename is path\file_name
        if not full_path.is_dir():
            full_filename = Path(full_path / file_name)
        else:
            full_filename = full_path

    # ===============================================
    # PROCESS THE USER'S COMMAND
    # ===============================================

    if switch == '/?':
        try:
            shell_help(cmd)
        except:
            print(cmd, 'is not recognized as a valid shell command.\n')

    elif cmd[:4] in ['EXIT', 'QUIT'] or cmd[0:] == 'Q':
        pass

    elif (cmd == 'HELP' or cmd == 'H') and not switch:
        clear()
        base_help()

    elif (cmd == 'HELP' or cmd == 'H') and switch:
        zip_help(switch)

    elif cmd[:2] == 'CD' or cmd[:4] == 'CD..' or cmd[:5] == 'CD ..':
        cd(cmd, switch, full_path)

    elif cmd[:3] == 'DIR':
        dir(full_path)

    elif cmd in ['CLS', 'CLEAR']:
        clear()

    elif cmd == 'O' or cmd == 'OPEN':
        open_file, new_file = True, False
        file_name, full_path, full_filename = open_archive(switch)
        if file_name:
            sub_menu(file_name, full_path, full_filename)

    elif cmd == 'N':
        open_file, new_file = False, True
        file_name, full_path, full_filename = create_new(switch)
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
    full_path, file_name = '', ''

    # ===============================================
    # PRINT THE PROGRAM HEADER... JUST ONCE
    # ===============================================
    version_num = "2.0"
    revision_number = get_revision_number()
    print("\nkatz ", version_num, '.', revision_number, " - a command-line archiving utility", sep='')
    print('\n<O>pen file    <N>ew file\n<A>bout\n\n<H>elp - from most prompts')
    print('')

    # ===============================================
    # GENERATE THE MAIN MENU IN A LOOP
    # ===============================================

    while True:

        # ===============================================
        # GET A COMMAND FROM THE USER
        # ===============================================
        prompt = "(katz) " + os.getcwd() + ">"
        entry = input(prompt).strip().upper()

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

        # actions to take on choosing a menu item
        if user_choice == 'L' or user_choice == 'LIST':
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
            dir(full_path)

        elif user_choice == 'A' or user_choice == 'ADD':
            file_name, full_path, full_filename = add_file(
                file_name, full_path, full_filename)

        elif user_choice == 'E' or user_choice == 'EXTRACT':
            file_name, full_path, full_filename = extract_file(
                file_name, full_path, full_filename)

        elif user_choice == 'R' or user_choice == 'REMOVE':
            file_name, full_path, full_filename = remove_file(
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
