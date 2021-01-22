"""
katz.py
version: 1.0
Richard E. Rawson
2021-01-15

Program Description:
GUI rendition of previously written katz.py

change log:

1.0 -- initial version

"""

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Line, Color, Rectangle
from kivy.graphics.vertex_instructions import Ellipse
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import os
from pathlib import Path
from pprint import pprint
import shutil
from zipfile import ZipFile

kivy.require('1.11.1')

# feature ============================================================

# TODO -- Need to be able to changed "default_directory" to the directory of the current zip file that is open.

# TODO -- Add function to set the default directory via "Options" and save that folder in a config file. Add another function/command to read the config file at startup.

# TODO -- remove_tmp() and on_stop() don't seem to ALWAYS remove the temporary directory.

# TODO -- Currently, you can only add files; change addFiles() so it will add folders with files.

# TODO -- Instead of printing messages on the white screen (like "File extracted."), display messages in the status bar. You will have to add a second Label.

# TODO -- After opening a file, I extracted it; them clicked "Remove" which told me there was no zip file open.

# TODO -- Rearrange functions and document everything.

# feature ============================================================


class ListFiles(FloatLayout):
    listFiles = ObjectProperty(None)
    show_files = ObjectProperty(None)
    cancel = ObjectProperty(None)

class OpenDialog(FloatLayout):
    openFile = ObjectProperty(None)
    cancel = ObjectProperty(None)

class AddDialog(FloatLayout):
    addFiles = ObjectProperty(None)
    cancel = ObjectProperty(None)

class NewFileDialog(FloatLayout):
    newFile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class KatzWindow(FloatLayout):
    """

    """

    def __init__(self, **kwargs):
        super(KatzWindow, self).__init__(**kwargs)

        savefile = ObjectProperty(None)
        text_input = ObjectProperty(None)
        self.text_input = text_input

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_open(self):
        content = OpenDialog(openFile=self.openFile, cancel=self.dismiss_popup)
        self._popup = Popup(title="Open file",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def show_add(self):
        content = AddDialog(addFiles=self.addFiles, cancel=self.dismiss_popup)
        self._popup = Popup(title="Add files",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def show_save(self):
        content = NewFileDialog(newFile=self.newFile, cancel=self.dismiss_popup)
        self._popup = Popup(title="New zip file",
                            content=content,
                            title_color=(1, 1, 1, 1),
                            title_size=28,
                            background='',
                            background_color=(0/255, 128/255, 128/255, 1),
                            size_hint=(0.75, 0.75)
                        )

        self._popup.open()

    def newFile(self, path, filename):

        # Try...except in case user enters a filename that is invalid for the OS.
        try:
            if filename[-4:] == '.zip':
                with ZipFile(os.path.join(path, filename), 'w') as file:
                    pass

                # Open the newly created file...
                # openFile is expecting zip_file as an item in a list:
                filename = [os.path.join(path, filename)]
                self.openFile(path, filename)
            else:
                msg = 'Can only create zip file with ".zip" extension.'
                self.show_msg(msg)
        except:
            msg = 'Filename that is invalid\nfor this operating system.'
            self.show_msg(msg)

        self._popup.dismiss()


    def cancel_listFiles(self):
        os.chdir(self.current_directory)
        try:
            shutil.rmtree(self.tmp_directory)
        except:
            pass
        self._popup.dismiss()

    def show_files(self):

        # A zip file must be opened first. If not, then there is no path,
        # and an exception will be raised.
        try:
            self.tmp_directory = self.path +  '\\_tmp_zip_'

            try:
                os.mkdir(self.tmp_directory)
            except:
                pass
            self.current_directory = os.getcwd()
            os.chdir(self.tmp_directory)
            lf = ListFiles()
            lf.ids.file_chooser.path = self.tmp_directory

            with ZipFile(self.zip_filename, 'r') as f:
                f.extractall(path=self.tmp_directory)

            content = ListFiles(listFiles=self.listFiles, cancel=self.dismiss_popup)
            # content = ListFiles(listFiles=self.listFiles, cancel=self.cancel_listFiles)
            self._popup = Popup(title="Archive contents",
                                title_color=(0, 0, 0, 1),
                                title_size=28,
                                background='',
                                background_color=(1, 1, 1, 1),
                                content=content,
                                size_hint=(1, (600 - 90)/600),
                                pos_hint={'x': 0, 'y':0}
                            )

            self._popup.open()

        except:
            self.show_msg('Open a zip file first.\nThen list its contents.')
            return


    def listFiles(self, selected_path, selected_files):

        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

        self.selected_files = selected_files
        path = os.path.dirname(self.zip_filename)
        path = path + '\\_tmp_zip_\\'
        print('path:', path)
        for ndx, file in enumerate(self.selected_files):
            file = file.replace(path, '')
            self.selected_files[ndx] = file

        self._popup.dismiss()
        print(self.selected_files)
        print('self.zip_filename:', self.zip_filename)


    def removeFiles(self):

        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

        # User must select one or more files to remove before continuing.
        try:
            print(self.selected_files)
        except:
            msg = 'You must open a zip file and select files\nbefore attempting to remove files.'
            self.show_msg(msg)
            return

        current_directory = os.getcwd()

        # Recreate the zip file from the files in the "current_directory"

        # 1. Add all the files in the "current directory", respecting relative paths,
        #    skipping the files that are listed in "selected_files".
        with ZipFile(os.path.basename(self.zip_filename), 'w') as this_zip:
            for root, dirs, files in os.walk(".", topdown=False):
                for name in files:
                    file_name = os.path.join(root, name)
                    file_name = file_name[2:]
                    if file_name not in self.selected_files:
                        this_zip.write(os.path.join(root, name))
                    else:
                        os.remove(file_name)

        # 2. Move the newly created zip file to the location of the original zip file.
        default_directory = os.path.dirname(self.zip_filename)
        new_zip_file = os.path.join(current_directory, os.path.basename(self.zip_filename))
        shutil.move(new_zip_file, self.zip_filename)
        os.chdir(default_directory)

        #3. Alert user of the files that were removed:
        msg = "Files removed:\n"
        msg += ', '.join(self.selected_files)
        if len(msg) > 30:
            msg += '...'
        if not self.selected_files:
            msg = 'No files selected. No files removed.'
        self.show_msg(msg, width=450, height=250)


    def openFile(self, path, filename):
        """
        Open the archive "filename". The current directory will be changed to "path." "filename" will be checked for .zip extension.
        """


        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

        # filename argument is a list. In this case, it is a list with only one item: the zip filename. An exception is raised if no filename was selected.
        try:
            self.zip_filename = filename[0]
            self.default_path = path
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
            if self.zip_filename[-4:] != '.zip': pass

            # Check to be sure the .zip file selected is actually a zip file.
            zfile = ZipFile(self.zip_filename)
        except:
            self.show_msg("Selected file is not a zip file.")
            self.dismiss_popup()
            return

        # Get the path by itself.
        self.path = os.path.dirname(self.zip_filename)

        # Change the working directory to directory containing the zip file
        self.current_directory = self.path
        os.chdir(self.current_directory)

        # Show filename in status bar:
        self.ids.open_filename.text = self.zip_filename

        self.dismiss_popup()


    def addFiles(self, path, filename):
        """
        Add a single file to the archive. The file will be placed in the archive relative to the location of the zip file itself. Updating a file that already exists is not supported. Remove the file first, and then add the newer version back.

        Example:
            zip file: c:\foo\bar.zip
            add file: c:\foo\foobar\blah.txt

            This file will be added to the folder "foobar" in the archive.
        """

        """
        To prevent duplicate files, get a list of all the files in the zip file already. Replace '/' with '\' so we can compare filenames accurately.
        """

        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

        zfile = ZipFile(self.zip_filename)
        these_files = zfile.namelist()
        for ndx, file in enumerate(these_files):
            file = file.replace('/', '\\')
            these_files[ndx] = file

        # Prevent user from adding files to an archive when one isn't open.
        try:
            if self.zip_filename: pass
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # Add the selected files to the archive, respecting relative paths.
        cnt_files = 0
        with ZipFile(self.zip_filename, 'a') as this_zip:
            for file in filename:
                """
                  absolute path to the zip file: c:\foo
                absolute path to the added file: c:\foo\foobar\newfile.txt

                relative_path: foobar
                add_this_file: foobar\newfile.txt
                """
                relative_path = os.path.relpath(os.path.dirname(file), os.path.dirname(self.zip_filename))
                add_this_file = os.path.join(relative_path, os.path.basename(file))
                if add_this_file not in these_files:
                    print('add_this_file:', add_this_file)
                    this_zip.write(add_this_file)
                    cnt_files += 1

        # If no files were added (because the file(s) already exist in the zip file), alert the user.
        if len(filename) > 0 and cnt_files == 0:
            msg = "No files were added.\nYou may have selected duplicate files."
            msg += "\n\nTo update a file, remove it first,\nthen add it."
            self.show_msg(msg, 400, 300)

        self.dismiss_popup()


    def extract(self):
        """
        Extract all files from an archive. Destination of unzipped files is not configurable at this time.
        """
        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

        # Prevent user from extracting from an archive when one isn't open.
        try:
            if self.zip_filename:
                self.ids.info.text = 'Files extracted.'
        except:
            self.show_msg("No zip file is open.\nOpen a zip file, first.")
            return

        # Extract all the files in the zipfile to a subfolder of the same name as the zipfile.
        with ZipFile(self.zip_filename, 'r') as f:
            print('\nExtracting...')
            extract_location = str(Path(self.path, self.zip_filename[:-4]))
            f.extractall(path=extract_location)


    def testFiles(self):
        """
        Test the integrity of the archive. Does not test archived files to determine if they are corrupted. If you archive a corrupted file, testing will not identify the fact that it is corrupted! Presumably, it was archived perfectly well as a corrupted file!
        """

        # Clear any messages off the large screen.
        Clock.schedule_once(self.clear_screen, 0)

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


    def show_msg(self, msg, width=400, height=200):
        """
        Utility function that simply shows a popup displaying "msg".

        Args:
            msg (str): Any string that is passed in, usually an error message.
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


    def remove_tmp(self):
        # Remove temporary directory '\\_tmp_zip_\\' if it exists.
        current_path = os.getcwd()
        if current_path[-9:] == '_tmp_zip_':
            os.chdir(Path(self.default_path))
            shutil.rmtree(Path(current_path))
        elif os.path.isdir(Path(self.default_path + '\\_tmp_zip_\\')):
            shutil.rmtree(Path(self.default_path + '\\_tmp_zip_\\'))
        else:
            pass


    def on_size(self, *args):
        self.ids.newbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.openbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.listbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.addbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.extractbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.removebutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.testbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.optionsbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))
        self.ids.exitbutton.font_size = max(Window.width * (20 / 800), Window.height * (20 / 600))


    def clear_screen(self, dt):
        self.ids.info.text = ''
        print('Clearing the screen')


class Popups(FloatLayout):
    pass

class KatzApp(App):
    def build(self):

        # Set the title that displays in the window title bar.
        self.title = "Katz - for zip files"

        # Here is where you can set a default path for openFile()
        self.default_path = "c:\\temp"

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
        if current_path[-9:] == '_tmp_zip_':
            os.chdir(Path(self.default_path))
            shutil.rmtree(Path(current_path))
        elif os.path.isdir(Path(self.default_path + '\\_tmp_zip_\\')):
            shutil.rmtree(Path(self.default_path + '\\_tmp_zip_\\'))
        else:
            pass


if __name__ == '__main__':
    my_app = KatzApp()
    my_app.run()
