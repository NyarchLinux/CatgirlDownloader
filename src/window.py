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
import requests
from gi.repository import Gtk, Adw, GdkPixbuf, GLib, Gio, GObject

from .catgirl import CatgirlDownloaderAPI
from .waifu import WaifuDownloaderAPI
from .preferences import UserPreferences


def load_image_with_callback(url, callback, error_callback=None):
    """
    Load an image from URL and call the callback with the pixbuf loader when complete.
    
    Args:
        url (str): The URL of the image to load
        callback (callable): Function to call when image is loaded successfully.
                           Should accept (pixbuf_loader, content_bytes) as argument
        error_callback (callable, optional): Function to call on error.
                                           Should accept (exception) as argument
    """ 
    def _load_image():
        pixbuf_loader = GdkPixbuf.PixbufLoader()
        data = bytearray()
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=1024):
                data.extend(chunk)
                pixbuf_loader.write(chunk)
            
            pixbuf_loader.close()
            
            # Schedule callback on main thread
            GLib.idle_add(callback, pixbuf_loader, bytes(data))
            
        except Exception as e:
            print(f"Exception loading image: {e}")
            if error_callback:
                GLib.idle_add(error_callback, e)
    
    # Run the loading in a separate thread to avoid blocking the UI
    thread = threading.Thread(target=_load_image)
    thread.daemon = True
    thread.start()

class SourceItem(GObject.Object):
    __gtype_name__ = 'SourceItem'

    def __init__(self, id, name, description, api):
        super().__init__()
        self.id = id
        self.name = name
        self.description = description
        self.api = api

@Gtk.Template(resource_path='/moe/nyarchlinux/catgirldownloader/../data/ui/window.ui')
class CatgirldownloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CatgirldownloaderWindow'

    refresh_button = Gtk.Template.Child("refresh_button")
    spinner = Gtk.Template.Child("spinner")
    image = Gtk.Template.Child("image")
    save_button = Gtk.Template.Child("savebutton")
    auto_reload_switch = Gtk.Template.Child("auto_reload_switch")
    source_selector = Gtk.Template.Child("source_selector")

    AVAILABLE_SOURCES = {
        "catgirl": {
            "name": "Catgirl",
            "description": "Generate images from nekos.moe.",
            "class": CatgirlDownloaderAPI
        },
        "waifu": {
            "name": "Waifu",
            "description": "Generate images from waifu.im.",
            "class": WaifuDownloaderAPI
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = UserPreferences()

        self.downloaders = {}
        self.source_store = Gio.ListStore(item_type=SourceItem)
        
        saved_source = self.settings.get_preference("source")
        default_index = 0
        found_source = False

        for i, (key, value) in enumerate(self.AVAILABLE_SOURCES.items()):
            api = value["class"]()
            self.downloaders[key] = api
            item = SourceItem(key, value["name"], value.get("description", ""), api)
            self.source_store.append(item)
            if key == saved_source:
                default_index = i
                found_source = True
        
        if not found_source and self.source_store.get_n_items() > 0:
            default_index = 0

        self.source_selector.set_model(self.source_store)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_source_item)
        factory.connect("bind", self.bind_source_item)
        self.source_selector.set_factory(factory)
        
        # Configure list factory for the dropdown list to use the complex layout
        self.source_selector.set_list_factory(factory)
        
        # Configure a simple factory for the selected item display (button content)
        # We just want the name of the source here
        button_factory = Gtk.SignalListItemFactory()
        button_factory.connect("setup", self.setup_source_button_item)
        button_factory.connect("bind", self.bind_source_button_item)
        self.source_selector.set_factory(button_factory)
        
        self.source_selector.set_selected(default_index)
        self.source_selector.connect("notify::selected-item", self.on_source_changed)

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

    def setup_source_button_item(self, factory, list_item):
        label = Gtk.Label(halign=Gtk.Align.START)
        list_item.set_child(label)

    def bind_source_button_item(self, factory, list_item):
        label = list_item.get_child()
        item = list_item.get_item()
        if item:
            label.set_label(item.name)

    def setup_source_item(self, factory, list_item):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_size_request(300, -1)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        avatar = Adw.Avatar(size=32)
        box.append(avatar)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_hexpand(True)
        
        title_label = Gtk.Label(halign=Gtk.Align.START)
        title_label.add_css_class("heading")
        vbox.append(title_label)
        
        desc_label = Gtk.Label(halign=Gtk.Align.START)
        desc_label.add_css_class("caption")
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(30)
        vbox.append(desc_label)
        
        box.append(vbox)

        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.add_css_class("circular")
        settings_btn.set_valign(Gtk.Align.CENTER)
        box.append(settings_btn)

        list_item.set_child(box)

    def bind_source_item(self, factory, list_item):
        box = list_item.get_child()
        item = list_item.get_item()
        
        avatar = box.get_first_child()
        avatar.set_text(item.name)
        
        vbox = avatar.get_next_sibling()
        title_label = vbox.get_first_child()
        title_label.set_label(item.name)
        
        desc_label = title_label.get_next_sibling()
        desc_label.set_label(item.description)
        
        settings_btn = vbox.get_next_sibling()
        
        if hasattr(settings_btn, "_handler_id"):
             settings_btn.disconnect(settings_btn._handler_id)
        
        def on_settings_clicked(btn):
            item.api.open_settings_window(self)
            
        settings_btn._handler_id = settings_btn.connect("clicked", on_settings_clicked)

    def on_source_changed(self, dropdown, _pspec):
        item = dropdown.get_selected_item()
        if item:
            self.settings.set_preference("source", item.id)
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

        source_id = None
        item = self.source_selector.get_selected_item()
        if item:
            source_id = item.id

        if not source_id:
            # Fallback if no selection
            if self.source_store.get_n_items() > 0:
                source_id = self.source_store.get_item(0).id
        
        # Should not happen if store populated, but handle safely
        if not source_id and self.downloaders:
             source_id = next(iter(self.downloaders))

        t = threading.Thread(target=self._fetch_url_thread, args=[source_id], daemon=True)
        t.start()

    def _fetch_url_thread(self, source_id=None):
        try:
            if not source_id:
                source_id = next(iter(self.downloaders))

            ct = self.downloaders.get(source_id)
            if not ct:
                ct = self.downloaders[next(iter(self.downloaders))]
                
            nsfw_mode_setting = self.settings.get_preference("nsfw_mode")
            url = ct.get_image_url(nsfw_mode_setting) if nsfw_mode_setting is not None else ct.get_image_url()
            info = getattr(ct, "info", None)
            
            if url:
                load_image_with_callback(
                    url, 
                    lambda loader, data: self._on_image_loaded(loader, data, info), 
                    self._on_image_error
                )
            else:
                 GLib.idle_add(self._on_image_error, Exception("Could not retrieve image URL"))
        except Exception as e:
            print(f"Error fetching URL: {e}")
            GLib.idle_add(self._on_image_error, e)

    def _on_image_loaded(self, loader, content, info):
        try:
            self.info = info
            self.imagecontent = content
            
            # Loader is already closed and should have pixbuf
            self.image.set_pixbuf(loader.get_pixbuf())
            
            image_format = loader.get_format()
            if image_format and image_format.extensions:
                self.image_extension = image_format.extensions[0]
                
            self.image.set_visible(True)
        except Exception as e:
            print(f"Error displaying image: {e}")
        finally:
            self._finish_loading()
            
    def _on_image_error(self, error):
        print(f"Image loading error: {error}")
        self._finish_loading()

    def _finish_loading(self):
        self.spinner.stop()
        self.spinner.set_visible(False)
        self._is_loading = False
        if self.auto_reload_switch.get_active():
            self._schedule_next_auto_reload()

    def file_chooser_dialog(self, ae=None):
        """Displays the dialog to save the image
        """
        if not self.info:
            return
        self.dialog = Gtk.FileChooserDialog(title="Save file", parent=self,
                                            action=Gtk.FileChooserAction.SAVE)

        source_id = None
        item = self.source_selector.get_selected_item()
        if item:
            source_id = item.id
        
        if not source_id:
             if self.source_store.get_n_items() > 0:
                 source_id = self.source_store.get_item(0).id
             elif self.downloaders:
                 source_id = next(iter(self.downloaders))

        downloader = self.downloaders.get(source_id)
        
        current_name = "image"
        if downloader:
             current_name = downloader.get_filename_suggestion(self.image_extension, self.info)

        if self.image_extension:
            # If we know the extension, add a filter for it
            file_extension = self.image_extension
            image_filter = Gtk.FileFilter()
            image_filter.set_name(f"{file_extension.upper()} files")
            image_filter.add_pattern(f"*.{file_extension}")
            self.dialog.add_filter(image_filter)
        
        self.dialog.set_current_name(current_name)

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
