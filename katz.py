"""
katz.py
version: 1.0
Richard E. Rawson
2021-01-15

Program Description:
GUI rendition of previously written katz.py

Versions:
1.0 -- initial version

"""

from ctypes import sizeof
from logging import exception
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Line, Color, Rectangle
from kivy.graphics.vertex_instructions import Ellipse
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import os
from pathlib import Path
from pprint import pprint
import shutil
from zipfile import ZipFile

kivy.require('1.11.1')

# ===== FEATURE REQUESTS AND TODO ITEMS ======================


# ============================================================


class NewFileDialog(FloatLayout):
    newFile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class OpenDialog(FloatLayout):
    openFile = ObjectProperty(None)
    cancel = ObjectProperty(None)

class ListFiles(FloatLayout):
    listFiles = ObjectProperty(None)
    show_files = ObjectProperty(None)
    cancel = ObjectProperty(None)

class AddDialog(FloatLayout):
    addFiles = ObjectProperty(None)
    cancel = ObjectProperty(None)

class RemoveDialog(FloatLayout):
    removeFiles = ObjectProperty(None)
    cancel = ObjectProperty(None)

class KatzWindow(FloatLayout):
    """
    Main application window for the Katz app, housing the menu buttons and popups displaying archive contents, file choosers, etc.
    """

    def __init__(self, **kwargs):
        super(KatzWindow, self).__init__(**kwargs)

        text_input = ObjectProperty(None)
        self.text_input = text_input

        # The startup path (default_path) is read from katz.config in KatzApp() or defaults to the app's home folder.
        kw = KatzApp()
        self.default_path = kw.default_path

    # ========================================================================
    # ==== NEW FILE
    # ========================================================================
    """
    show_save() -- Activated by the "New" button. It displays a popup that contains a file chooser, where the user picks a folder, and a TextInput widget that gets the new filename.

    newFile() --
    """
    def show_save(self):
        content = NewFileDialog(newFile=self.newFile, cancel=self.dismiss_popup)
        self._popup = Popup(title="New zip file",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            separator_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def newFile(self, path, filename):
        """
        Create a new zip file with a name and location determined by the user.

        Args:
            path (str): Path to the file that will be created.
            filename (str): basename (filename.ext) of the file that will be created.

        NOTES:
            -- The filename that the user enters must end with ".zip".
            -- Filenames with characters invalid for the OS are not allowed.
        """


        # Try...except in case:
            # -- the filename does not end in ".zip"
            # -- user enters a filename that is invalid for the OS.
        try:
            if filename[-4:] == '.zip':
                with ZipFile(os.path.join(path, filename), 'w') as file:
                    pass

                # Since we created a new file, open it by passing "filename" to openFile().
                # Since openFile() is expecting a [list], then pass filename as a [list].
                filename = [os.path.join(path, filename)]
                self.openFile(path, filename)
            else:
                msg = 'Can only create zip file with ".zip" extension.'
                self.show_msg(msg)
        except:
            msg = 'Filename that is invalid\nfor this operating system.'
            self.show_msg(msg)

        self._popup.dismiss()


    # =======================================================================
    # ==== OPEN FILE
    # ========================================================================
    """
    show_open() -- Activated by the "Open" button. It displays a popup that contains a file chooser so that the user can select a specific .zip file.

    openFile() -- Besides being invoked by show_open(), this function is also called by newFile(). In both cases the selected/created file is opened.

    NOTE:
        -- "Open"ing a file means:
                1. Check to be sure file ends in .zip and that it is actually a zip archive.
                2. Change the default_path to the path of the zip file that is open.
                3. Display the name of the open file in the status bar.
                4. The subfolder, "_tmp_zip_", is deleted automatically and without warning.
    """

    def show_open(self):
        content = OpenDialog(openFile=self.openFile, cancel=self.dismiss_popup)
        self._popup = Popup(title="Open file",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            separator_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def openFile(self, path, filename):
        """
        Open the archive "filename". The current directory will be changed to "path." "filename" will be checked for .zip extension.

        Args:
            path (str): Path to the file that will be opend.
            filename ([list]): full path (path/filename.ext) of the file that will be opened.
        """

        # The "filename" argument is a [list] with only one item: the zip filename that should be opened. An exception is raised if no filename was selected by show_open().
        try:
            self.zip_filename = filename[0]
            self.default_path = path
            os.chdir(Path(self.default_path))

            # Create the temporary folder (_tmp_zip_) so its name is established at file opening.
            try:
                self.tmp_path = self.default_path +  '\\_tmp_zip_'
                for i in range(50):
                    if not os.path.isdir(self.tmp_path):
                        print('self.tmp_path:', self.tmp_path)
                        break
                    else:
                        self.tmp_path = self.tmp_path + '(' + str(i) + ')'
                        continue
            except:
                pass

            os.chdir(Path(self.default_path))

        except:
            self.show_msg('No file was selected to open.')
            self.dismiss_popup()
            return

        # If this is the second time a file has been opened in this session, remove temporary directory from previous zip file, if it exists.
        self.remove_tmp()

        # Conduct error checks before moving forward.
        try:
            # Check if user-selected file ends in .zip:
            if self.zip_filename[-4:] != '.zip': raise exception

            # Check to be sure the .zip file selected is actually a zip file.
            zfile = ZipFile(self.zip_filename)
        except:
            self.show_msg("Selected file is not a zip file.")
            self.dismiss_popup()
            return

        # Get the default path as a variable.
        self.default_path = os.path.dirname(self.zip_filename)

        # Change the working directory to directory containing the zip file
        os.chdir(self.default_path)

        # Show filename in status bar:
        self.ids.open_filename.text = self.zip_filename

        self.dismiss_popup()


    # ========================================================================
    # ==== LIST FILES (ARCHIVE CONTENTS)
    # ========================================================================
    """
    List the contents of the archive. To do this, we create a sub-directory under the default directory (the directory holding the zip file) that is called "_tmp_zip_". The zip file is extracted to that temporary directory. The file chooser then displays the contents of the temporary directory.

    NOTE:
        If the directory "_tmp_zip_" already exists, it won't be overwritten. The user will be instructed to delete that directory before files can be listed.

    """
    def show_files(self):

        # Prevent user from adding files to an archive when one isn't open.
        try:
            print(self.zip_filename)
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # A try...except block is used just in case there is any problem with naming or creating the temporary directory.
        try:
            # Make the temporary folder, then change the current directory to that folder.
            os.mkdir(self.tmp_path)
            os.chdir(self.tmp_path)

            # Instantiate the ListFiles() class so we can save the temporary directory path name to the path attribut of the file chooser.
            lf = ListFiles()
            lf.ids.file_chooser.path = self.tmp_path

            # Extract the zip file to the temporary directory.
            with ZipFile(self.zip_filename, 'r') as f:
                f.extractall(path=self.tmp_path)

            # Create a popup displaying the folders and files extracted from the archive. The filechooser that is shown uses the path established by the code 5 lines up from here.
            content = ListFiles(listFiles='', cancel=self.cleanup_listFiles)
            self._popup = Popup(title="Archive contents",
                                title_color=(0, 0, 0, 1),
                                title_size=28,
                                background='',
                                background_color=(1, 1, 1, 1),
                                separator_color=(0/255, 128/255, 128/255, 1),
                                content=content,
                                size_hint=(1, (600 - 90)/600),
                                pos_hint={'x': 0, 'y':0}
                            )

            self._popup.open()

        except:
            msg = 'The temporary folder, "_tmp_zip_",\nalready exists. Delete that folder\nbefore proceeding.'
            self.show_msg(msg, 400, 300)
            return

    def cleanup_listFiles(self):
        os.chdir(self.default_path)
        self.remove_tmp()
        self.dismiss_popup()



    # ========================================================================
    # ==== ADD FILES (AND FOLDERS)
    # ========================================================================
    def show_add(self):
        """
        This function is called by the "Add" button in the menu bar. Here, we display a file chooser to allow user to choose files to add to the archive. By default, the default folder when the file chooser opens is the folder containing the open archive.
        """

        # Prevent user from adding files to an archive when one isn't open.
        try:
            print(self.zip_filename)
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        content = AddDialog(addFiles=self.addFiles, cancel=self.dismiss_popup)
        self._popup = Popup(title="Add files",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            separator_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def addFiles(self, path, added_filenames):
        """
        Add files and/or folders to the archive. Files will be placed in the archive relative to the location of the zip file itself. Updating a file that already exists is not supported. Remove the file first, and then add the newer version back.

        Args:
            path (str): Path to the file that will be opened.
            filename ([list]): full path (path/filename.ext) of the file that will be opened.

        NOTE:
            To prevent duplicate files, we get a list of all the files in the zip file already. Replace '/' with '\' so we can compare filenames accurately.
        """

        print('path:', path)
        print('added_filenames:', added_filenames)

        os.chdir(self.default_path)

        # Prevent user from adding files to an archive when one isn't open.
        try:
            if self.zip_filename: pass
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # The user's selected files are in the argument "added_filenames" with absolute paths.
        # In the following for... loop, filenames are converted to relative paths and stored in [selected_files].
        self.selected_files = []
        for item in added_filenames:

            if os.path.isdir(item):
                for root, dirs, files in os.walk(item, topdown=False):
                    for name in files:
                        if root.lower() == item.lower():
                            # print('root, name:', root, ';', name)
                            self.selected_files.append(os.path.join(root, name))
            else:
                if item != 'c:\\':
                    self.selected_files.append(item)

        # Create a string, "msg", containing a list of all the selected file.
        # "msg" is the string that will be displayed by the ScrollView in the white screen.
        msg = 'Added files:\n'
        for ndx, i in enumerate(self.selected_files):
            msg = msg + i + '\n'

        # Create the two buttons that the user will use to confirm or cancel adding files.
        self.showfiles_OK = Button(text='Go!',
                                size_hint=(0.15, 0.08),
                                pos_hint={'x': 0.01, 'y': 0.01}
                            )
        self.showfiles_cancel = Button(text='Forget it',
                                size_hint=(0.15, 0.08),
                                pos_hint={'x': 0.2, 'y': 0.01}
                            )

        self.ids.sv_label.text = msg
        self.ids.white_screen.add_widget(self.showfiles_OK)
        self.ids.white_screen.add_widget(self.showfiles_cancel)

        self.showfiles_OK.bind(on_release=self.add_the_files)
        self.showfiles_cancel.bind(on_release=self.cancel_scroll)

        self.dismiss_popup()

    def add_the_files(self, instance):
        """
        When the user presses the "Go!" button on the white screen, this function is run.

        Add the selected files to the archive, respecting relative paths. If a file is chosen in a folder that is not a subfolder of the archive, the relative path is still used.

        Example of the latter:
                        zip file: c:\\foo\\my_zip.zip
              adding a file from: c:\\bar\\foobar.txt
            the path in zip file: ..\\bar\\foobar.txt
        """

        print('instance:', instance)

        # Create a list of all archive files, so we don't add a file already present.
        zfile = ZipFile(self.zip_filename)
        archive_files = zfile.namelist()
        for ndx, file in enumerate(archive_files):
            file = file.replace('/', '\\')
            archive_files[ndx] = file

        # Iterate through "selected_file" and add each file to the archive, using relative paths.
        cnt_files = 0
        with ZipFile(self.zip_filename, 'a') as this_zip:
            for file in self.selected_files:

                """
                  absolute path to the zip file: c:\\foo\\my_zip.zip
                absolute path to the added file: c:\foo\foobar\newfile.txt
                                  add_this_file: foobar\newfile.txt
                """
                relative_path = os.path.relpath(os.path.dirname(file), os.path.dirname(self.zip_filename))
                add_this_file = os.path.join(relative_path, os.path.basename(file))

                if add_this_file not in archive_files:
                    this_zip.write(add_this_file)
                    cnt_files += 1

        # "Erase" the content being shown on the white screen, including the ScrollView and buttons.
        self.cancel_scroll("")


    # ========================================================================
    # ==== EXTRACT ARCHIVE
    # ========================================================================
    def extract(self):
        """
        Extract all files from an archive into a folder with the same name as the zip file. Destination of unzipped files is not configurable at this time.
        """

        # Prevent user from extracting from an archive when one isn't open.
        try:
            if self.zip_filename: pass
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # Extract all the files in the zipfile to a subfolder of the same name as the zipfile.
        with ZipFile(self.zip_filename, 'r') as f:
            print('\nExtracting...')
            extract_location = str(Path(self.default_path, self.zip_filename[:-4]))
            f.extractall(path=extract_location)

        msg = 'Extracting finished.'
        self.show_msg(msg)


    # ========================================================================
    # ==== REMOVE FILES (AND FOLDERS)
    # ========================================================================
    """
    show_remove() -- Displays a popup with a filechooser showing the files that are presently in the archive file.

    removeFiles() -- Removes files and/or folders from the archive. This cannot be undone.
    """

    def show_remove(self):
        """
        This function is called by the "Remove" button in the menu bar. Here, we display a file chooser to allow user to choose files to remove from the archive.
        """

        # Prevent user from adding files to an archive when one isn't open.
        try:
            print(self.zip_filename)
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        try:
            # Create a temporary folder into which archive files will be extracted.
            # self.tmp_path = self.default_path +  '\\_tmp_zip_'
            os.mkdir(self.tmp_path)

            # Change the current working directory to that temporary folder.
            os.chdir(self.tmp_path)

            # Extract the archive to the temporary folder.
            with ZipFile(self.zip_filename, 'r') as f:
                f.extractall(path=self.tmp_path)

            # Now, the file chooser displayed by self._popup will contain all the files in the archive.
            content = RemoveDialog(removeFiles=self.removeFiles, cancel=self.dismiss_popup)

            self._popup = Popup(title="Remove files",
                                content=content,
                                title_color=(1, 1, 1, 1),
                                title_size=28,
                                background='',
                                background_color=(0/255, 128/255, 128/255, 1),
                                separator_color=(0/255, 128/255, 128/255, 1),
                                size_hint=(0.75, 0.75)
                            )

            self._popup.open()

        except:
            msg = 'The temporary folder, "_tmp_zip_",\nalready exists. Delete that folder\nbefore proceeding.'
            self.show_msg(msg, 400, 300)
            os.chdir(self.default_path)
            self.remove_tmp()
            return

    def removeFiles(self, path, remove_these):
        """
        Remove one or more files and/or folders from an archive.

        Args:
            path (str): Path to the file that will be opened.
            remove_these ([list]): full path (path/filename.ext) to the files/folders to be removed.
        """

        # User must have selected one or more files to remove before continuing.
        try:
            if path == '':
                raise Exception
        except:
            msg = 'No files were selected.\nNo files will be removed.'
            self.show_msg(msg)
            self.dismiss_popup()
            os.chdir(self.default_path)
            self.remove_tmp()
            return

        # "self.remove_these" contains all the files/folders the user wants to remove from the archive.
        self.remove_these = remove_these

        # Change the cwd to the temporary directory: _tmp_zip_
        os.chdir(self.tmp_path)

        # Convert all paths in "remove_these" to relative paths:
        for ndx, f in enumerate(self.remove_these):
            relative_path = os.path.relpath(os.path.dirname(f), self.tmp_path)
            self.remove_these[ndx] = os.path.join(relative_path, os.path.basename(f))
            # If the file is in the root directory of the zip file, delete the '.\\' prefix.
            if self.remove_these[ndx][0:2] == '.\\':
                self.remove_these[ndx] = self.remove_these[ndx][2:]

        # If [remove_these] contains a directory, replace the directory name with all the file names in that directory.
        add_these = []
        for ndx, item in enumerate(self.remove_these):
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item, topdown=False):
                    for name in files:
                        add_these.append(os.path.join(root, name))
                self.remove_these.remove(item)
        self.remove_these.extend(add_these)

        # Create a string that contains path.filename for each file to be removed.
        # This string will be displayed in the ScrollView Label.
        msg = 'Files to be removed:\n'
        for ndx, i in enumerate(self.remove_these):
            msg = msg + i + '\n'

        self.showfiles_OK = Button(text='OK',
                                size_hint=(0.15, 0.08),
                                pos_hint={'x': 0.01, 'y': 0.01}
                            )
        self.showfiles_cancel = Button(text='Cancel',
                                size_hint=(0.15, 0.08),
                                pos_hint={'x': 0.2, 'y': 0.01}
                            )

        self.ids.sv_label.text = msg
        self.ids.white_screen.add_widget(self.showfiles_OK)
        self.ids.white_screen.add_widget(self.showfiles_cancel)

        self.showfiles_OK.bind(on_release=self.remove_the_files)
        self.showfiles_cancel.bind(on_release=self.cancel_scroll)

        self.dismiss_popup()

    def remove_the_files(self, instance):
        """
        When the user presses the "Go!" button on the white screen, files that have been selected by the user will be removed from the temporary folder. The archive is recreated in the temporary folder, but this time without the deleted file(s). The newly recreated archive in the temporary folder has the same name as the original. It is moved to the same folder as the original archive, overwriting the original archive.
        """

        # tmp_path = os.getcwd()
        os.chdir(self.tmp_path)

        # Find each of the files in "remove_these" and delete each one.
        zfile =  os.path.basename(self.zip_filename)
        with ZipFile(zfile, 'w') as this_zip:
            for root, dirs, files in os.walk(".", topdown=False):
                for name in files:
                    file_name = os.path.join(root, name)
                    file_name = file_name[2:]
                    if file_name not in self.remove_these and name != zfile:
                        this_zip.write(file_name)
                    else:
                        if name != zfile:
                            os.remove(file_name)

        # Move the newly created zip file to the location of the original zip file.
        self.default_path = os.path.dirname(self.zip_filename)
        new_zip_file = os.path.join(self.tmp_path, os.path.basename(self.zip_filename))
        shutil.move(new_zip_file, self.zip_filename)
        os.chdir(self.default_path)

        # Alert user if no files were removed.
        if not self.remove_these:
            msg = 'No files selected. No files removed.'
            self.show_msg(msg, width=450, height=250)

        # Finally, remove "tmp_path"
        try:
            shutil.rmtree(self.tmp_path)
        except:
            pass

        self.cancel_scroll("")


    # ========================================================================
    # ==== TEST ARCHIVE
    # ========================================================================
    def testFiles(self):
        """
        Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testing will not identify the fact that it is corrupted! Presumably, it was archived perfectly well as a corrupted file!
        """

        # Prevent user from testing an archive when one isn't open.
        try:
            if self.zip_filename: pass
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # Test integrity of zip file using testzip().
        with ZipFile(self.zip_filename, 'r') as f:
            bad_files = f.testzip()
            num_zip_files = len(f.infolist())

        # Display the results of the testing function.
        if bad_files:
            msg = str(', '.join(bad_files)) + "\nfailed testing."
        else:
            msg = str(num_zip_files) + " files tested.\nAll files passed testing."
        self.show_msg(msg)


    # ========================================================================
    # ==== OPTIONS
    # ========================================================================
    def katz_options(self):
        """
        Provide a means for getting, and saving, a default start-up folder for the user.
        """


        text_label = Label(text='Enter a startup folder:',
                            font_size=20,
                            color=(0, 0, 0, 1),
                            text_size=self.size,
                            pos_hint={'x': 0.2, 'y': 1},
                            halign='left'
                        )

        get_startup = TextInput(
                                background_color=(1, 1, 1, 1),
                                size_hint=(.95, 0.1),
                                pos_hint={'x': 0, 'y': 0.5},
                                focus=False,
                                multiline=False,
                                font_size=20,
                                hint_text='path',
                                hint_text_color=[0.5, 0.5, 0.5, 1.0],       # a light grey
                                cursor_width=4,
                                cursor_color=(179/255, 27/255, 27/255, 1),  # a shade of deep red
                            )

        content = FloatLayout()

        content.add_widget(text_label)
        content.add_widget(get_startup)

        # content = Label(text='Options dialog', font_size=28, color=(0, 0, 0, 1))
        self._popup = Popup(title="Katz options",
                            content=content,
                            title_color=(0/255, 128/255, 128/255, 1),
                            title_size=28,
                            background='',
                            background_color=(1, 1, 1, 1),
                            separator_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        get_startup.bind(on_text_validate=self.set_default_path)

        self._popup.open()

    def set_default_path(self, instance):

        print('setting path...', instance.text)

        self.default_path = instance.text
        kw = KatzApp()
        self.app_folder_name = kw.app_folder_name

        self.current_path = os.getcwd()
        os.chdir(self.app_folder_name)

        with open('katz.config', 'w') as f:
            f.write(self.default_path)

        os.chdir(self.current_path)

        self.dismiss_popup()


    # ========================================================================
    # ==== UTILITY FUNCTIONS
    # ========================================================================

    def cancel_scroll(self, instance):
        """
        In removeFiles() and addFiles(), a ScrollView is displayed in the white screen to show files that the program intends to add or remove. The user is given the option to cancel or confirm the action. Once completed this function clears the ScrollView and related buttons from the white screen.
        """
        self.ids.sv_label.text = ''
        self.ids.white_screen.remove_widget(self.showfiles_OK)
        self.ids.white_screen.remove_widget(self.showfiles_cancel)
        os.chdir(self.default_path)
        try:
            self.remove_tmp()
        except:
            pass

    def dismiss_popup(self):
        """
        Dismisses the popup _popup.
        """
        # self.remove_tmp()
        self._popup.dismiss()

    def on_size(self, *args):
        """
        Activated whenever the window size is changed by the user. Used to alter the size of buttons and font used in the button text.
        """

        self.ids.newbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.openbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.listbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.addbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.extractbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.removebutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.testbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.optionsbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.exitbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))

    def remove_tmp(self):
        """
        This is a "cleanup" function that removes the temporary directory '\\_tmp_zip_\\', if it exists. This function is called by openFile(), cleanup_listFiles(), the "Exit" button, and on_stop().
        """
        os.chdir(self.default_path)
        # tmp_path = os.path.join(self.default_path, '_tmp_zip_')

        try:
            if os.path.isdir(self.tmp_path):
                shutil.rmtree(Path(self.tmp_path))
        except:
            pass

    def show_msg(self, msg, width=400, height=200):
        """
        Utility function that simply shows a popup displaying "msg".

        Args:
            msg (str): Any string that is passed in. (Typically, but not always, used for error messages.)
            width (int): Width of the popup; defaults to 400
            height (int): Height of popup; defaults to 200
        """

        title = 'Message Center'
        self.popup_content = Label(text=msg,
                                color=(0, 0, 0, 1),
                                font_size=20
                                )

        # Create the layout widget to hold the error message and "Dismiss" button.
        self.popup_layout = GridLayout(rows=2, cols=1, padding=10)

        # Define a Close button.
        self.closeButton = Button(text="Dismiss",
                            size_hint=(None, None),
                            height=40,
                            width=80
                            )

        # Add the error message Label and the Close button to the GridLayout.
        self.popup_layout.add_widget(self.popup_content)
        self.popup_layout.add_widget(self.closeButton)

        # Define the popup window, with the popup content.
        popupWindow = Popup(title=title,
                    title_color=(0, 0, 0, 1),
                    title_size=28,
                    background='',
                    background_color=(1, 1, 1, 1),
                    content=self.popup_layout,
                    size_hint=(None,None),
                    size=(width,height)
                    )

        popupWindow.open()

        # Bind an on_press event to the Close button.
        self.closeButton.bind(on_press=popupWindow.dismiss)


class KatzApp(App):

    # Read the startup folder from katz.config in the app folder.
    app_folder_name = os.path.abspath(os.path.dirname(__file__))
    os.chdir(app_folder_name)
    try:
        with open('katz.config', 'r') as f:
            default_path = f.readline()
    except:
        default_path = app_folder_name

    def build(self):

        # Set the title that displays in the window title bar.
        self.title = "Katz - for zip files"

        # Change the startup path to default path read from katz.config, if it exists.
        os.chdir(self.default_path)

        # Default size the window at program launch. This can be changed by the user, dragging a window corner.
        # Window.size = (586, 660)

        return KatzWindow()


    def on_stop(self):
        """
        This function runs when the user clicks the "close" button on the kivy
        """
        print('Running on_stop()...')

        # Remove temporary directory '\\_tmp_zip_\\' if it exists.
        current_path = os.getcwd()
        if current_path[-9:] == '_tmp_zip_' or current_path[-12:-3]== '_tmp_zip_' or current_path[-13:-4] == '_tmp_zip_':
            os.chdir(Path(self.default_path))
            shutil.rmtree(Path(current_path))
        elif os.path.isdir(Path(self.tmp_path)):
            shutil.rmtree(Path(self.tmp_path))
        else:
            pass


if __name__ == '__main__':
    my_app = KatzApp()
    my_app.run()
