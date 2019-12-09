"""
katz.py

Richard E. Rawson
2019-11-12

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
import sys
import textwrap
import zipfile
from datetime import datetime

# the following if... prevents a warning being issued to user if they try to add
# a duplicate file to an archive; this warning is handled in add_file()
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# todo -- In list_files(), pause the screen every 25 files

# todo -- When you do a <D>irectory, make it work like DOS:
# ? <D>
# ? c:\temp\one
# ? cd three   --> c:\temp\one\three
# ? cd .. --> c:\temp\one

# todo -- remove_file()... cannot remove a subfolder

# todo -- remove_file() can remove whole folders except for the root folder. For that folder, if the user types "root" in response to "type the name of the folder:", advise them that removing "root" will remove all files in the archive and that they should simply delete the zip file.

# todo -- I cannot <R>emove a subfolder. If I have:
# ? one/temp/one
# ?      4. one - Copy (2).txt
# ?      5. one - Copy.txt
# ?      6. one.txt
# todo -- ...then I cannot remove the folder "one/temp/one"
# todo -- relatedly, I cannot <R>emove a range of files

# todo -- version 2, add support for other archiving formats, including tar and gzip

# todo -- version 3: add support for importing into other scripts so that, for example, downloaded archives are extracted automatically

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

    full_filename = os.path.join(full_path, file_name)

    # if file already exists, issue "overwrite" warning
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
            msg = '\n' + file_name + ' already exists. Overwrite? (Y/N) '
            overwrite = input(msg).upper()

            if overwrite == 'Y':
                with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', file_name, 'created as new archive.\n')
                return full_path, file_name

            else:
                print(file_name, 'not created.\n')
                return '', ''

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        with zipfile.ZipFile(full_filename, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            print('\n', file_name, 'created as new archive.\n')
        return full_path, file_name


def open_archive():
    """
    Open an archive and list the files in the archive.
    """
    # get a file name from user
    full_path, file_name = get_filename()
    full_filename = os.path.join(full_path, file_name)

    # if no file_name was entered, return to menu
    if not file_name:
        return '', ''

    # sort out possible errors in file_name
    try:
        with zipfile.ZipFile(full_filename, 'r') as f:
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

        # if no file name was entered, return to menu
        if not full_path.strip():
            return '', ''

        file_name = os.path.basename(full_path)
        if os.path.dirname(full_path):
            full_path = os.path.dirname(full_path)
        else:
            full_path = os.getcwd()

        # zip files don't require a .zip extension, but it's a bad idea
        if file_name[-4:] != '.zip':
            print('\nMust enter a ".zip" extension.')
            continue

        break

    # change the cwd() to the path for this file
    try:
        if full_path:
            os.chdir(full_path)
    except:
        print('\nPath or filename is invalid.')
        return '', ''

    return full_path, file_name


def list_files(full_path, file_name):
    """
    Generate a numbered list of all the files and folders in the archive.
    """
    full_filename = os.path.join(full_path, file_name)

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
            print(' '*5, ndx+1, '. ', this_file, sep='')

            # pause after every 25 files
            cnt = ndx+1
            if len(zip_files) >= 25 and cnt >= 25 and cnt % 25 == 0:
                more = input(
                    '--ENTER to continue; Q to quit--').strip().upper()
                if more == 'Q':
                    break

    return full_path, file_name


def dir_files():
    """
    List the files in a directory (not the archive). By default, this changes the working directory if a path is entered.
    """
    print('\nEnter "." for current directory\nor ".." for the parent directory.\nTo go to a subfolder of the current folder\nuse a back-slash (e.g, \sub-folder)')

    cwd = '...'+os.getcwd()[-49:] if len(os.getcwd()) > 49 else os.getcwd()
    print('\nCurrent directory:\n', cwd, sep='')

    current_directory = input("\nEnter a directory: ").strip()

    if not current_directory:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        return os.getcwd()

    if current_directory[0] == '\\' or current_directory[0] == '/':
        current_directory = os.getcwd() + current_directory

    # make sure the directory is valid
    # if so, change the working directory
    try:
        os.chdir(current_directory)
        # list all the files in the current working directory
        # files = os.listdir(current_directory)

    except FileNotFoundError:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        print('\nNo such directory.')
        return os.getcwd()

    except OSError:
        print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
        print('\nNot a valid directory name.')
        return os.getcwd()

    subs = input('Include subdirectories (Y/N): ').strip().upper()
    subs = True if subs == 'Y' else False

    cwd = '...'+os.getcwd()[-49:] if len(os.getcwd()) > 49 else os.getcwd()
    print('\n', dsh*52, '\n', cwd, '\n', dsh*52, sep='')

    # print a list of files in the chosen folder (and, optionally, subfolders)
    stop_listing = False
    if subs:
        cnt = 1
        for folderName, subfolders, filenames in os.walk(current_directory, followlinks=True):
            cnt += 1
            if cnt >= 25 and cnt % 25 == 0:
                more = input(
                    '--ENTER to continue; Q to quit--').strip().upper()
                if more == 'Q':
                    break
            print(folderName)
            for file in filenames:
                cnt += 1
                print('     ', file)
                # pause after every 25 files
                if cnt >= 25 and cnt % 25 == 0:
                    more = input(
                        '--ENTER to continue; Q to quit--').strip().upper()
                    if more == 'Q':
                        stop_listing = True
            if stop_listing:
                break
    else:
        cnt = 0
        for folderName, subfolders, filenames in os.walk(current_directory, followlinks=True):
            # print only the root folder but all the files in that folder
            if cnt == 0:
                print(folderName)
            else:
                break
            for file in filenames:
                cnt += 1
                print('     ', file)
                # pause after every 25 files
                if cnt >= 25 and cnt % 25 == 0:
                    more = input(
                        '--ENTER to continue; Q to quit--').strip().upper()
                    if more == 'Q':
                        break
    return current_directory


def add_file(full_path, file_name):
    """
    Add one, many, or all files from the user-designated folder, and optionally include subfolders of that folder. Uses various methods for choosing files to add, optimized for speed of selection.
    """
    full_filename = os.path.join(full_path, file_name)
    current_directory = os.getcwd()

    msg = 'CURRENT DIRECTORY: ' + current_directory
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')


# fixme: When I <A>dd files using root as c:\temp\one with no subfolders, I get this list of files:
# ? 1. one\one - Copy(2).txt
# ? 2. one\one - Copy.txt
# ? 3. one\one.txt
# ? 5. one\temp\one\one - Copy(2).txt
# ? 6. one\temp\one\one - Copy.txt
# ? 7. one\temp\one\one.txt

    # ==================================================
    # GET THE SOURCE DIRECTORY FROM THE USER
    # ==================================================

    # get directory containing files that you want to add
    while True:
        print('\nEnter "." to use current directory.')
        dir = input("Directory containing files to add: ").strip()

        # if user enters nothing, return to the menu
        if not dir:
            return full_path, file_name

        if dir == '.':
            dir = full_path

        if not os.path.exists(dir) or not os.path.isdir(dir):
            print('\nEntry does not exist or is not a directory. Re-enter.')
            continue
        else:
            subs = input('Include subdirectories (Y/N): ').strip().upper()
            subs = True if subs == 'Y' else False
            print()
            break

    # ==================================================
    # GENERATE A NUMBERED LIST OF ALL FILES IN THE USER-CHOSEN FOLDER
    # EXAMPLES:
    # dir = c:\foo\bar
    # root_folder = c:\foo
    # rel_dir = bar
    # ==================================================
    root_folder = os.path.split(dir)[0]
    rel_dir = os.path.relpath(dir, root_folder)

    os.chdir(root_folder)

    cnt, file_list = 1, []
    for folderName, subfolders, filenames in os.walk(rel_dir, followlinks=True):
        for filename in filenames:
            # create complete filepath of file in directory
            filePath = os.path.join(folderName, filename)
            if os.path.split(filePath)[1] != file_name:
                if subs:
                    file_list.append(filePath)
                    print(cnt, '. ', filePath, sep='')
                else:
                    if filePath.split('\\')[-2] == rel_dir:
                        file_list.append(filePath)
                        print(cnt, '. ', filePath, sep='')
                cnt += 1

    # ==================================================
    # GET FROM USER THE FILES TO ADD TO THE ARCHIVE
    #   user can choose individual files or "all" files
    # ==================================================

    while True:
        # let user choose which file(s) to add
        # example user input: 1, 3-5, 28, 52-68, 70 or *.t?t
        print('\nEnter:\n(1) a comma-separated combination of:\n    -- the number of the file(s) to add\n    -- a hyphenated list of sequential numbers\n(2) enter "all" to add all files\n(3) use wildcard characters (*/?) to designate files')

        choice = input("\nFile(s) to add: ").strip()

        # if nothing is entered, return to menu
        if not choice:
            os.chdir(current_directory)
            return full_path, file_name

        # ========================================================
        # BASED ON USER'S CHOICES, CREATE A LIST OF THE ELIGIBLE FILES
        # ========================================================

        add_files = []  # list that contains file names w/ paths to add
        if choice.upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(file_list)+1)]
            for file_number in which_files:
                add_files.append(file_list[int(file_number)-1])

        # see https://pymotw.com/2/glob/
        elif '*' in choice or '?' in choice:
            if subs:
                for folderName, subfolders, filenames in os.walk(rel_dir, followlinks=True):
                    f = os.path.join(folderName, choice)
                    for name in glob.glob(f):
                        if name != os.path.join(folderName, file_name):
                            add_files.append(name)
                            print(name)
            else:
                for name in glob.glob(choice):
                    if name != os.path.join(folderName, file_name):
                        add_files.append(os.path.join(folderName, name))
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
                        return full_path, file_name
                # treating all other single digits
                else:
                    try:
                        n = int(i)
                        which_files.append(str(n))
                    except:
                        print(
                            '\nInvalid number(s) excluded. Did you comma-separate values?')
                        return full_path, file_name

            for file_number in which_files:
                add_files.append(file_list[int(file_number)-1])

        break

    os.chdir(root_folder)

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

    # puts files in folder
    with zipfile.ZipFile(full_filename, 'a') as f:
        for file in add_files:
            file_to_add = file
            if file_to_add not in zip_files:
                f.write(file_to_add)
            else:
                print('\n', file,
                        ' already exists in archive.\nRemove this file before adding a new version.', sep='')

    os.chdir(current_directory)

    return full_path, file_name


def extract_file(full_path, file_name):
    """
    Extract one or more files from an archive.
    """
    full_filename = os.path.join(full_path, file_name)

    # get a list files in the archive and number them
    with zipfile.ZipFile(full_filename, 'r') as f:
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

    return full_path, file_name


def remove_file(full_path, file_name):
    """
    This utility removes only one file at a time.

    Technical info: To remove a file, this function first create a temporary archive that holds all the original files except the one targeted for removal. The temporary archive is tested for integrity; the original archive is deleted; the temporary archive is renamed as the original.
    """
    full_filename = os.path.join(full_path, file_name)

    # make sure you are in the same directory as the zip file
    os.chdir(full_path)

    # unlikely, abort if "temporary" directory already exists
    this_path = '_temp_' + file_name[:-4] + '_'
    if os.path.isdir(this_path):
        print('\nCannot remove files from archive, since ',
              this_path, ' directory exists.', sep='')
        return full_path, file_name

    # get a list of files in the archive and their total number
    with zipfile.ZipFile(full_filename, 'r') as f:
        zip_files = f.namelist()
        num_files = len(f.namelist())

    while True:
        # for the user, print a list of files and folders in the archive
        full_path, file_name = list_files(full_path, file_name)

        # get from the user the file or folder that should be removed
        print("\nEnter the number of file to remove or")
        print('to remove a whole folder,')
        choice = input("type the name of the folder: ").strip()

        # if no file name is entered, return to menu
        if not choice.strip():
            return full_path, file_name

        # if a non-integer was typed, then check if it's a valid folder name
        # otherwise, make sure it's an integer between 1 and the total
        # number of files in the archive
        try:
            choice = int(choice)
            if choice > 0 and choice <= num_files:
                break
            else:
                print('\nEnter only an integer, in range 1-',
                      num_files, '.\n', sep='')
                continue
        except:
            # deny ability to delete root/ folder
            if 'ROOT' in choice.upper():
                print(
                    '\nDeleting root deletes all files/folders in the archive.\nDelete the archive file itself, instead.')
                continue
            bad_choice, folderName = False, ''
            for line in zip_files:
                pos = line.rfind('/')
                folderName = line[0:pos].upper()
                if pos:
                    if choice.upper() in folderName:
                        break
            if not folderName:
                print('\n', choice, ' is not a folder.')
                continue
            else:
                break

    # get confirmation from the user about the file to be removed
    print()
    for ndx, file in enumerate(zip_files):
        if ndx+1 == choice:
            print(ndx+1, '. ', file, sep='')
        elif isinstance(choice, str):
            pos = file.find('/')
            if choice.upper() == file[0:pos].upper():
                print(file)

    confirmed = input('\nRemove file(s)? (Y/N) ').strip().upper()
    if confirmed == 'Y':
        # create the directory that will hold files temporarily
        os.mkdir(this_path)

        with zipfile.ZipFile(full_filename, 'r') as f:
            zip_files = f.namelist()
            # extract all the files to "this_path" except
            # the file user has chosen
            for ndx, file in enumerate(zip_files):
                if isinstance(choice, int):
                    if ndx+1 != choice:
                        f.extract(file, path=this_path)
                else:
                    pos = file.find('/')
                    if file[0:pos].upper() != choice.upper():
                        f.extract(file, path=this_path)

        # get relative path to temporary directory
        cwd = full_path + '\\' + this_path
        rel_dir = os.path.relpath(cwd, cwd)

        # add all the extracted files to _temp_zipfile_.zip
        with zipfile.ZipFile('_temp_zipfile_.zip', 'w', compression=zipfile.ZIP_DEFLATED) as f:
            # change directory to the temporary directory, which contains all files in the archive, except the file destined for removal
            os.chdir(this_path)

            # Iterate over all the files in the root directory
            # write each file to the temporary zip file
            for folderName, subfolders, filenames in os.walk(rel_dir, followlinks=True):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # add file to zip
                    f.write(filePath)

        # change back to directory with zip file in it
        os.chdir(full_path)

        # test the temporary archive before deleting the original one
        if not zipfile.is_zipfile('_temp_zipfile_.zip'):
            print('\nUnknown error. Aborting removal of file.')

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
            print('\nUnknown error. Aborting removal of file.')

        # delete "temporary" file even if exception was raised in previous line
        if os.path.isfile('_temp_zipfile_.zip'):
            try:
                os.remove('_temp_zipfile_.zip')
            except:
                print(
                    'Cannot complete operation. _temp_zipfile_.zip is being used by another process.', sep='')

        # delete "temporary" dir even if exception was raised in previous line
        if os.path.isdir(this_path):
            try:
                shutil.rmtree(this_path, ignore_errors=False)
            except PermissionError:
                print('Cannot complete operation. A file or folder in ',
                      this_path, ' is being used by another process.', sep='')

    return full_path, file_name


def test_archive(full_path, file_name):
    """
    Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testzip() will not detect a problem and you will extract a corrupted file.
    """
    full_filename = os.path.join(full_path, file_name)

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

    return full_path, file_name


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


def help():
    """
    A help function.
    """
    open1_txt = """
    -- Enter a filename, including a .zip extension. Use a path if you want to <O>pen a file in a non-default directory (which is set using <D>irectory). If you <O>pen a zip file with a path (e.g., c:\\mydata\\foo.zip), the path to that zip file will be considered the root directory for all subsequent operations in the sub-menu.
"""

    new_txt = """
    katz 1.0 archives files using only the zip file format (not gzip or tar). File compression is automatic. If you create a <N>ew zip file with a path (e.g., c:\\mydata\\foo.zip), the path to that zip file will be considered the root directory for all operations in the sub-menu.
"""

    directory_txt = """
    <D>irectory conducts two operations simultaneously.
"""
    directory1_txt = """
        (1) List the files in the specified directory (not an archive!). <D>irectory lists files in a directory on disk, while <L>ist produces a list of files in the archive.
"""
    directory2_txt = """
        (2) Changes the default (working) directory.
"""
    directory3_txt = """
    TIP: Before you <O>pen a file or create a <N>ew file, use <D>irectory to change the current directory. Then, <O>pen and <N>ew will manipulate files without having to enter a full path again.
"""

    list_txt = """
    <L>ist all the files in the archive. <D>irectory lists files in a directory in disk, while <L>ist produces a list of files in the archive.
"""

    add1_txt = """
    -- <A>dd provides a list of files that you can <A>dd to the archive.
"""
    add2_txt = """
    -- Enter a "." to get a list of files from the same directory holding the zip file, or enter a path to another directory. Files in the same directory as the zip file will be added to the root folder in the archive.
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

    remove_txt = """
    <R>emoves a file or a folder from the archive. You can only remove one file or folder at a time. This operation cannot be reversed! Removing a folder removes all sub-folders, as well. "katz" will confirm before removing any files or folders.
"""

    test_txt = """
    <T>est the integrity of the archive. Special NOTE: If you archive a corrupted file, testing will not identify the fact that it is corrupted!
"""

    while True:
        # print("\n".join([fold(txt) for txt in txt.splitlines()]))
        # print(dsh*45)
        print('\n', dsh*52, '\n', slsh*20, ' HELP MENU ',
              slsh*21, '\n', dsh*52, sep='')
        print('<O>pen file  <N>ew file  <D>irectory  <L>ist\n<A>dd        <E>xtract   <R>emove     <T>est\n<Q>uit HELP\n')
        choice = input(
            'Show help on which item: ').strip().upper()
        if choice not in 'ONDLAERTQ':
            print('\nEnter one of O, N, D, L, A, E, R, T, Q.')
            continue

        if choice == 'O':
            print('\nOpen File')
            print(fold(open1_txt, '          '))

        elif choice == 'N':
            print('\nNew File')
            print(fold(new_txt))

        elif choice == 'D':
            print('\nDirectory')
            print(fold(directory_txt))
            print(fold(directory1_txt, '          '))
            print(fold(directory2_txt, '          '))
            print(fold(directory3_txt))

        elif choice == 'L':
            print('\nList Files')
            print(fold(list_txt))

        elif choice == 'A':
            print('\nAdd Files')
            print(fold(add1_txt, '          '))
            print(fold(add2_txt, '          '))
            print(fold(add3_txt, '          '))
            print(fold(add4_txt, '          '))

        elif choice == 'E':
            print('\nExtract Files')
            print(fold(extract1_txt, '          '))
            print(fold(extract2_txt, '          '))
            print(fold(extract3_txt, '          '))
            print(fold(extract4_txt, '          '))
            print(fold(extract5_txt, '          '))
            print(fold(extract6_txt))
            print(fold(extract7_txt, '          '))

        elif choice == 'R':
            print('\nRemove File')
            print(fold(remove_txt))

        elif choice == 'T':
            print('\nTest Archive')
            print(fold(test_txt))

        elif choice == 'Q' or choice == '':
            print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')
            break

    return


def get_revision_number():
    """
    Returns the revision number, which is the number of days since the initial coding of "katz" began on November 12, 2019.
    """
    start_date = datetime(2019, 11, 12)
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
    full_path, file_name = '', ''

    # generate the main menu until the user presses "Q"
    while True:

        # print the program header
        print('one')
        version_num = "1.0"
        revision_number = get_revision_number()
        print("\nkatz ", version_num, '.', revision_number,
              " - a command-line archiving utility", sep='')

        # reset user-entered file names/paths
        # full_path, file_name = '', ''

        while True:
            choice = input(
                '\n<O>pen file    <N>ew file    <D>irectory\n<A>bout        <H>elp        <Q>uit\n\nChoice: ').strip().upper()
            if choice in 'ONDAHQ':
                break
            else:
                print('\nEnter only "O", "N", "D", "A", "H", or "Q".')
                continue

        if choice == 'O':
            open_file, new_file = True, False
            sub_menu(open_file, new_file)

        elif choice == 'N':
            open_file, new_file = False, True
            sub_menu(open_file, new_file)

        elif choice == 'D':
            full_path = dir_files()

        elif choice == 'A':
            about()

        elif choice == 'H':
            help()

        elif choice == 'Q':
            break

    # change back to original user directory
    # os.chdir(_user_directory_)


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
    msg = '...' + full_path[-49:] if len(full_path) >= 49 else full_path
    print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

    while True:
        # generate the sub-menu
        print('\n<L>ist     <D>irectory    <A>dd\n<E>xtract  <R>emove       <T>est\n<M>ain menu')
        user_choice = input('\nChoose an action: ').strip().upper()

        if user_choice not in 'LDAERTMQ ':
            print('\n"', user_choice, '" ', 'is an invalid action.', sep='')
            continue

        print('\n', dsh*52, '\n', msg, '\n', dsh*52, sep='')

        # actions to take on choosing a menu item
        if user_choice == 'L':
            full_path, file_name = list_files(full_path, file_name)

        elif user_choice == 'D':
            full_path = dir_files()

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

    # full_path = 'c:\\temp\\one'
    # file_name = 'temp.zip'
    # full_filename = os.path.join(full_path, file_name)
    # r = 'four'
    # list_files(full_path, file_name)
    # with zipfile.ZipFile(full_filename, 'r')as f:
    #     zip_files = f.namelist()

    # for i in zip_files:
    #     print(i)
