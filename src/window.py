# window.py
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

import threading
from gi.repository import Gtk, Adw, GdkPixbuf, GLib

from .catgirl import CatgirlDownloaderAPI
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/nyarchlinux/catgirldownloader/../data/ui/window.ui')
class CatgirldownloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CatgirldownloaderWindow'

    refresh_button = Gtk.Template.Child("refresh_button")
    spinner = Gtk.Template.Child("spinner")
    image = Gtk.Template.Child("image")
    save_button = Gtk.Template.Child("savebutton")
    auto_reload_switch = Gtk.Template.Child("auto_reload_switch")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = UserPreferences()

        self.info = None
        self.imagecontent = None
        self.image_extension = None

        self._is_loading = False
        self._auto_reload_timeout_id = None
        self._auto_reload_interval = self._get_auto_reload_interval()

        enabled = self._get_auto_reload_enabled()
        self.auto_reload_switch.set_active(enabled)
        self.auto_reload_switch.connect("notify::active", self.on_auto_reload_toggle)

        self.refresh_button.connect("clicked", self.async_reloadimage)
        self.save_button.connect("clicked", self.file_chooser_dialog)
        self.async_reloadimage()

    def _get_auto_reload_enabled(self) -> bool:
        enabled = self.settings.get_preference("auto_reload_enabled")
        if isinstance(enabled, bool):
            return enabled
        if isinstance(enabled, str):
            return enabled.lower() in ("1", "true", "yes", "on")
        return False

    def _get_auto_reload_interval(self) -> int:
        seconds = self.settings.get_preference("auto_reload_interval")
        try:
            seconds = int(seconds) if seconds is not None else 30
        except Exception:
            seconds = 30
        if seconds < 1:
            seconds = 1
        return seconds

    def set_auto_reload_interval(self, seconds: int):
        try:
            seconds = int(seconds)
        except Exception:
            seconds = 30
        if seconds < 1:
            seconds = 1
        self._auto_reload_interval = seconds
        self.settings.set_preference("auto_reload_interval", seconds)
        if self.auto_reload_switch.get_active() and not self._is_loading:
            self._schedule_next_auto_reload()

    def on_auto_reload_toggle(self, switch, _):
        active = bool(switch.get_active())
        self.settings.set_preference("auto_reload_enabled", active)
        if not active:
            self._cancel_auto_reload()
            return
        if not self._is_loading:
            self._schedule_next_auto_reload()

    def _cancel_auto_reload(self):
        if self._auto_reload_timeout_id is not None:
            GLib.source_remove(self._auto_reload_timeout_id)
            self._auto_reload_timeout_id = None

    def _schedule_next_auto_reload(self):
        if not self.auto_reload_switch.get_active():
            return
        self._cancel_auto_reload()

        seconds = int(self._auto_reload_interval) if self._auto_reload_interval else 30
        if seconds < 1:
            seconds = 1

        self._auto_reload_timeout_id = GLib.timeout_add_seconds(
            seconds,
            self._on_auto_reload_timeout,
        )

    def _on_auto_reload_timeout(self):
        self._auto_reload_timeout_id = None
        if not self.auto_reload_switch.get_active():
            return False
        self.async_reloadimage()
        return False

    def async_reloadimage(self, az=None):
        """Call the function to load the image on another thread
        """
        if self._is_loading:
            return
        self._is_loading = True
        self._cancel_auto_reload()
        self.spinner.set_visible(True)
        self.spinner.start()

        t = threading.Thread(target=self._download_image_thread, args=[az], daemon=True)
        t.start()

    def _download_image_thread(self, _=None):
        info = None
        content = None
        try:
            ct = CatgirlDownloaderAPI()
            nsfw_mode_setting = self.settings.get_preference("nsfw_mode")
            url = ct.get_image_url(nsfw_mode_setting) if nsfw_mode_setting is not None else ct.get_image_url()
            info = getattr(ct, "info", None)
            if url is not None:
                content = ct.get_image(url)
        except Exception as e:
            print(e)
        GLib.idle_add(self._apply_download_result, info, content)

    def _apply_download_result(self, info, content):
        try:
            if content:
                self.info = info
                self.imagecontent = content

                loader = GdkPixbuf.PixbufLoader()
                loader.write_bytes(GLib.Bytes.new(content))

                image_format = loader.get_format()
                if image_format and image_format.extensions:
                    self.image_extension = image_format.extensions[0]
                loader.close()

                self.image.set_pixbuf(loader.get_pixbuf())
                self.image.set_visible(True)
        except Exception as e:
            print(e)
        finally:
            self.spinner.stop()
            self.spinner.set_visible(False)
            self._is_loading = False
            if self.auto_reload_switch.get_active():
                self._schedule_next_auto_reload()
        return False

    def file_chooser_dialog(self, ae=None):
        """Displays the dialog to save the image
        """
        if not self.info or "images" not in self.info or not self.info["images"]:
            return
        self.dialog = Gtk.FileChooserDialog(title="Save, file", parent=self,
                                            action=Gtk.FileChooserAction.SAVE)

        image_id = self.info["images"][0]["id"]
        if self.image_extension:
            # If we know the extension, add a filter for it
            file_extension = self.image_extension
            image_filter = Gtk.FileFilter()
            image_filter.set_name(f"{file_extension.upper()} files")
            image_filter.add_pattern(f"*.{file_extension}")
            self.dialog.add_filter(image_filter)
            # And suggest a sensible default filename
            # using this format ensures the image source can easily be found from its name
            self.dialog.set_current_name(f"nekos.moe_{image_id}.{file_extension}")
        else:
            # Otherwise just suggest a sensible default filename (normally the extension should always be there, but just in case)
            self.dialog.set_current_name(f"nekos.moe_{image_id}")

        # Buttons
        self.dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        self.dialog.add_button('Save', Gtk.ResponseType.OK)
        self.dialog.connect('response', self.responsehandler)
        self.dialog.show()

    def responsehandler(self, dialog, response_id):
        """Save image and destroy file chooser"""
        if response_id == Gtk.ResponseType.OK:
            file = dialog.get_file()
            filename = file.get_path()
            if self.imagecontent:
                f = open(filename, "wb+")
                f.write(self.imagecontent)
                f.close()
        dialog.destroy()
