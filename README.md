# katz v2.0 (rev.212)
a command-line archiving utility

Most GUI archiving utilities have many wonderful features that I never use and a plethora of settings that I never change. "katz" eliminates all this hassle and delivers a minimalist archiving utility that will meet the needs of 99% of users. From the command-line!

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
**_katz_** requires only one file: katz.py. Using katz.bat is optional. See below.

If you have python 3.7+ installed, you can download `katz.py` and, assuming python.exe is in your PATH, run:

    `python katz.py`

## **Usage**
- The program interface is based on the Windows command shell, but with only a very small subset of OS commands. In addition, this "shell" includes a set of command useful for manipulating zip files as noted under *Features*. There are no options or preferences.
- See *Recommended setup* below for creating a shortcut.
- python 3 must be in the PATH environment variable.


## **Recommended setup**
If you want to run "katz" from your desktop, here is what you need to do:
1. Put all of the files in this repository in a directory of your choice.
2. Modify katz.bat as noted within the .bat file.
3. Create a shortcut to the .bat file on your desktop.
4. In the properties dialog for the shortcut
   - change "TARGET" to the full path, including the filename, for katz.bat.
   - change "START IN" to any path that you desire, but usually this will be the path for the directory that holds katz.bat

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
