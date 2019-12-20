# `katz v2.0`
a command-line archiving utility

Most GUI archiving utilities have many wonderful features that I never use and a plethora of settings that I never change. `katz` eliminates all this hassle and delivers a minimalist archiving utility that will meet the needs of 99% of users. From the command-line!

#

## **Features**

1. list all files within the archive
2. add file(s), optionally including subfolders, from any directory on disk
3. extract all or selected file(s) from the archive
4. remove file(s) or folders from the archive
5. test the integrity of the archive
6. perform shell commands including dir, cls, and cd

Files are compressed by default.

## **Installation**
**`katz`** requires only one file: `katz.py`.

If you have python 3 installed, you can download `katz.py` and, assuming python.exe is in your PATH, run:

`python katz.py`

## **Usage**
- The program interface is fashioned after the Windows command shell (terminal), but valid commands include only those useful for manipulating zip files as noted under *Features*.
- See *Recommended setup* below for creating a shortcut.


## **Configuration**
- Configuration is limited to setting a default startup directory.


## **Recommended setup**
If you want to run `katz` from your desktop, here is what you need to do:
- Put all of the files in this repository in a directory of your choice.
- Navigate to that directory, and from within a terminal (Windows shell)...
- Start `katz` using...

`python katz.py`
- At the command prompt, enter 's' or 'setup'.
- Create the following setting:
    - startup_directory=[path of your choice]


## **Required python modules:**
- datetime
- glob
- os
- pathlib
- shutil
- string
- subprocess
- sys
- textwrap
- zipfile

All modules are included in the python standard library.
