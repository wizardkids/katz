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

import os
import shutil
import zipfile

# todo -- in version 2, add support for other formats including tar and gzip


def create_new():
    """
    Create a new zip file.
    """

    # get a valid filename from the user
    file_name, full_path = get_filename()

    # if not file name was entered, return to the menu
    if not file_name:
        return

    try:
        # if file already exists, issue warning
        with zipfile.ZipFile(file_name, 'r') as f:
            msg = '\n' + file_name + ' already exists. Overwrite? '
            overwrite = input(msg).upper()
            if overwrite == 'Y':
                with zipfile.ZipFile(file_name, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                    print('\n', file_name, 'created as new archive.\n')
            else:
                print(file_name, 'not created.\n')

    # if file_name was not found, then we can create it!
    except FileNotFoundError:
        # create a new zip file
        with zipfile.ZipFile(file_name, 'w', compression=zipfile.ZIP_DEFLATED) as f:
            print('\n', file_name, 'created as new archive.\n')
    return file_name, full_path


def open_archive():
    """
    Open an archive and list the files in the archive.
    """
    # get a valid file name from user
    file_name, full_path = get_filename()

    # open the archive and list all the files in it
    try:
        with zipfile.ZipFile(file_name, 'r') as f:
            zip_files = f.namelist()
            for ndx, file in enumerate(zip_files):
                print(ndx+1, '. ', file, sep='')
    except:
        print('File not found.')

    return file_name


def get_filename():
    """
    Get a filename from user and check the entry for validity.
    """
    while True:
        # get a file name from the user
        full_path = input("\nName of archive: ").strip()
        file_name = os.path.basename(full_path)

        # if no file name was entered, return to menu
        if not full_path.strip():
            return file_name, full_path

        # "escape" any backslashes
        # full_path = full_path.replace('\\', '\\\\')

        # check filename for bad characters and bad extension
        prohibited = ['<', '>', '\"', '?', '|', '*']
        if full_path[-4:] != '.zip':
            print('\nFile name is not a zip file.\n')
            continue
        bad_file = False
        for i in full_path:
            if i in prohibited:
                print("\nBad file name: '", i, "' not allowed.", sep='')
                bad_file = True
        if bad_file:
            continue

        break

    # to make thing easier, change the cwd() to the path for this file
    _working_directory_ = os.path.dirname(full_path)
    if _working_directory_:
        os.chdir(_working_directory_)

    return file_name, full_path


def list_files(file_name):
    """
    Generate a numbered list of all the files in the archive.
    """
    with zipfile.ZipFile(file_name, 'r') as f:
        zip_files = f.namelist()
        # get and print the root directory
        current_directory = os.path.dirname(zip_files[0])
        print(current_directory)
        for ndx, file in enumerate(zip_files):
            # when the directory changes, print it (left-justified)
            if current_directory != os.path.dirname(file):
                current_directory = os.path.dirname(file)
                print(current_directory)
            # print files indented 5 spaces
            this_directory, this_file = os.path.split(file)
            print(' '*5, ndx+1, '. ', this_file, sep='')

    return file_name


def add_file(file_name):
    """
    Add one, many, or all files to an existing archive.
    """
    # generate a list of files in the current directory
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    print('\n--------------------------------\n',
          'FILES IN THE CURRENT DIRECTORY\n',
          '--------------------------------', sep='')
    for ndx, file in enumerate(files):
        print(file, sep='')

    while True:
        # get a file name to add
        print('\nUse "all" to add all files to the archive.')
        file_to_add = input('\nFile name to add to archive: ').strip()

        # if no file name was entered, return to menu
        if not file_to_add:
            return
        else:
            break

    if file_to_add.upper() == 'ALL':
        choice = input('Include subdirectories? Y/N ').strip().upper()
        if choice == 'Y':
            # except for the zip file, add all files including subfolders
            tree = os.walk('.')
            for dirpath, dirnames, filenames in tree:
                for file in filenames:
                    if file != file_name:
                        this_file = os.path.relpath(
                            os.path.join(dirpath, file), ".")
                        write_one_file(this_file, file_name)
        else:
            # add all files in top level directory except the zip itself
            for file in files:
                if file != file_name:
                    write_one_file(file, file_name)
    else:
        # adding a single file; make sure file exists
        if not os.path.isfile(file_to_add):
            print('\nFile name is incorrect\nor file does not exist.\n')
        # add one specific file to archive, unless it's the zip itself
        if file != file_name:
            write_one_file(file, file_name)
        else:
            print('\nCannot add the archive to itself.')

    return file_name


def write_one_file(file_to_add, file_name):
    # determine if the file already exists in the archive;
    # an archive cannot have duplicate files
    with zipfile.ZipFile(file_name) as f:
        zip_files = f.namelist()

    if file_to_add in zip_files:
        # print message if file already resides in archive
        print(
            '\n', file_to_add, ' already exists in archive.\nRemove this file before adding a new version.', sep='')
    else:
        # add the compressed file to the archive
        with zipfile.ZipFile(file_name, 'a', compression=zipfile.ZIP_DEFLATED) as f:
            f.write(file_to_add)
    return


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
            '\nEnter a comma-separated combination of:\n  -- the number of the file(s) to extract\n  -- a hyphenated list of sequential numbers\n  -- or enter "all" to extract all files\n')
        choice = input("File number(s) to extract: ")

        # if no choice is made, return to menu
        if not choice.strip():
            return file_name

        # which_files is a list of digits user entered (type:string)
        # if choice="ALL", then generate a list of all file numbers
        if choice.strip().upper() == 'ALL':
            which_files = [str(x) for x in range(1, len(zip_info)+1)]
        else:
            # extract all the file numbers from the user's list:
            selected_files = choice.split(',')
            which_files = []
            for i in selected_files:
                if '-' in i:
                    r = i.split('-')
                    try:
                        n = [str(x) for x in range(int(r[0]), (int(r[1]))+1)]
                        for x in n:
                            which_files.append(x)
                    except:
                        print(
                            '\nInvalid range of numbers was excluded. Did you comma-separate values?')
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
        for ndx, file in enumerate(zip_files):
            if ndx+1 in which_files:
                this_file = zip_files[ndx]
                print(this_file)
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

    # get confirmation from the user about the file to be removed
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
        with zipfile.ZipFile('_temp_zipfile_.zip', 'w', compression=zipfile.ZIP_DEFLATED) as f:
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

    return file_name


def test_archive(file_name):
    """
    Test the integrity of the archive.
    """
    # first, test if it is a valid zip file
    if not zipfile.is_zipfile(file_name):
        print('\nNot a valid zip file.')
        return file_name

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


def about():
    dsh, slsh = '=', '/'
    print('\n', dsh*52, '\n', slsh*52, '\n', dsh*52, sep='')

    about1 = '"katz" is named after Phil Katz, the originator of'
    about2 = 'PKWARE, the company that originated the ZIP file'
    about3 = 'format in 1989 that is still in popular use today.'

    print(about1, '\n', about2, '\n', about3, '\n', sep='')

    return


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
        file_name, full_path = '', ''
        while True:
            choice = input(
                '\n<O>pen file    <N>ew file    <A>bout\nQ>uit\n\nChoice: ').upper()
            if choice in 'ONAQ':
                break
            else:
                print('\nEnter only "O", "N", "A", or "Q".')
                continue

        if choice == 'O':
            open_file, new_file = True, False
            sub_menu(open_file, new_file)

        elif choice == 'N':
            open_file, new_file = False, True
            sub_menu(open_file, new_file)

        elif choice == 'A':
            about()

        elif choice == 'Q':
            break

        # change back to original user directory
        os.chdir(_user_directory_)


def sub_menu(open_file, new_file):
    """
    Menu of actions on the file that the user has opened or created.
    """
    if open_file:
        file_name, full_path = get_filename()
        # if the file does not exist upon <open>, render warning and return
        if not os.path.isfile(full_path):
            print('\nFile not found.')
            return
    else:
        file_name, full_path = create_new()

    # go back to the main menu if no file name is entered
    if not file_name:
        return

    # use the following to delimit output from sequential commands
    if len(full_path) >= 49:
        fp = '...' + full_path[-49:]
    else:
        fp = full_path

    dsh, slsh = '=', '/'
    print('\n', dsh*52, '\n', fp, '\n', dsh*52, sep='')

    file_name = list_files(file_name)

    while True:
        # generate the sub-menu
        print('\n<L>ist    <A>dd   <E>xtract\n<R>emove  <T>est  <M>ain menu')
        user_choice = input('\nChoose an action: ').strip().upper()

        if user_choice not in 'LAERTM':
            print('\n"', user_choice, '" ', 'is an invalid action.', sep='')
            continue

        print('\n', dsh*52, '\n', fp, '\n', dsh*52, sep='')

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
