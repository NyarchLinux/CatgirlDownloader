# main.py
#
# Copyright 2023 SilverOS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import CatgirldownloaderWindow
from .preferenceswindow import PreferencesWindow

class CatgirldownloaderApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='moe.nyarchlinux.catgirldownloader',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action('quit', lambda action, _: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('show-art-about', self.on_art_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('reload', self.on_reload, ['<primary>r'])

    def on_reload(self, widget, _):
        self.window.async_reloadimage()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = CatgirldownloaderWindow(application=self)
        win.set_title("Catgirl Downloader")
        self.window = win
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Catgirl Downloader',
                                application_icon='moe.nyarchlinux.catgirldownloader',
                                developer_name='Nyarch Linux developers team',
                                version='0.2.6',
                                developers=['SilverOS'],
                                copyright='© 2024 SilverOS')
        about.present()

    def on_art_about_action(self, widget, _):
        """Callback for the app.about action."""
        if hasattr(self.window, "info"):
            info = self.window.info["images"][0]
            about = Adw.AboutWindow(transient_for=self.props.active_window,
                                    artists=[info['artist']],
                                    website="https://nekos.moe/post/" + info['id'])
            about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        window = PreferencesWindow(self.window)
        window.set_transient_for(self.window)
        window.set_modal(True)
        window.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = CatgirldownloaderApplication()
    return app.run(sys.argv)
