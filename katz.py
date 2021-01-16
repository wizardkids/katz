"""
katz.py

Richard E. Rawson
2021-01-15

Program Description:

"""

import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Line, Color, Rectangle
from kivy.graphics.vertex_instructions import Ellipse
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.popup import Popup

from pprint import pprint

kivy.require('1.11.1')


class TemplateWindow(FloatLayout):
    """

    """

    def __init__(self, **kwargs):
        super(TemplateWindow, self).__init__(**kwargs)



class TemplateApp(App):
    def build(self):

        # Set the title that displays in the window title bar.
        self.title = ""

        # Default size the window at program launch. This can be changed by the user, dragging a window corner.
        Window.size = (586, 660)

        return TemplateWindow()


if __name__ == '__main__':
    my_app = TemplateApp()
    my_app.run()
