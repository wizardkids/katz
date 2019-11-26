# katz
a command-line archiving utility

Most GUI archiving utilities have many wonderful features that I never use and a plethora of settings that I never change. "katz" eliminates all this hassle and delivers a minimalist archiving utility that will meet the needs of 99% of users. From the command-line!

## **Features**

1. list all files, including files in subfolders, within the archive
2. add one, many, or all files, optionally including subfolders
3. extract one, many, or all files from the archive, including subfolders
4. remove one file at a time from the archive
5. test the integrity of the archive

Files are compressed by default.

## **Usage**
- The program is menu driven, with only essential capabilities as noted under *Features*. There are no options or preferences.
- python 3 must be in the PATH environment variable.

## **Recommended setup**
If you want to run "katz" from your desktop, here is what you need to do:
1. Put all of the files in this repository in a directory of your choice.
2. Modify katz.bat as noted within the .bat file.
3. Create a shortcut on your desktop.
4. In the properties dialog for the shortcut
   - change "TARGET" to the full path, including the filename, for katz.bat.
   - change "START IN" to the path for the directory that holds katz.bat