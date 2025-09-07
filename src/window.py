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

from gi.repository import Gtk, Adw, GdkPixbuf, GLib
from .catgirl import CatgirlDownloaderAPI, E621DownloaderAPI
import threading
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/Avelcius/furrydownloader/../data/ui/window.ui')
class CatgirldownloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CatgirldownloaderWindow'

    refresh_button = Gtk.Template.Child("refresh_button")
    spinner = Gtk.Template.Child("spinner")
    image = Gtk.Template.Child("image")
    save_button = Gtk.Template.Child("savebutton")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = UserPreferences()
        self.current_source = 'e621'
        self.refresh_button.connect("clicked", self.async_reloadimage)
        self.save_button.connect("clicked", self.file_chooser_dialog)
        self.async_reloadimage()
        print(GLib.get_user_config_dir())

    def reloadimage(self, idk=None):
        """Reload current image
        Args:
            idk (none): not useful but need to put it.
        """
        # Start loading
        self.spinner.set_visible(True)
        self.spinner.start()
        # Get image from selected source
        nsfwsetting = bool(self.settings.get_preference("nsfw"))
        self.current_source = 'e621'
        tags = self.settings.get_preference("e621_tags") or ""
        ct = E621DownloaderAPI()
        url = ct.get_neko(nsfwsetting, tags)
        self.info = ct.info
        if url is not None:
            content = ct.get_image(url)
        self.imagecontent = content
        # Display image
        loader = GdkPixbuf.PixbufLoader()
        loader.write_bytes(GLib.Bytes.new(content))
        # Try retrieving image extension and save it for use in file_chooser_dialog later
        image_format = loader.get_format()
        if image_format and image_format.extensions:
            self.image_extension = image_format.extensions[0]
        loader.close()
        self.image.set_from_pixbuf(loader.get_pixbuf())
        # Stop loading and display image
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.image.set_visible(True)

    def async_reloadimage(self, az=None):
        """Call the function to load the image on another thread
        """
        t = threading.Thread(target=self.reloadimage, args=[az])
        t.start()

    def file_chooser_dialog(self, ae=None):
        """Displays the dialog to save the image
        """
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
            prefix = 'e621' if self.current_source == 'e621' else 'nekos.moe'
            self.dialog.set_current_name(f"{prefix}_{image_id}.{file_extension}")
        else:
            # Otherwise just suggest a sensible default filename (normally the extension should always be there, but just in case)
            prefix = 'e621' if self.current_source == 'e621' else 'nekos.moe'
            self.dialog.set_current_name(f"{prefix}_{image_id}")

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
            f = open(filename, "wb+")
            f.write(self.imagecontent)
            f.close()
        dialog.destroy()
