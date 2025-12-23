from gi.repository import GLib
import os
import json

class UserPreferences:
    def __init__(self):
        self._defaults = {
            "nsfw_mode": "Block NSFW",
            "auto_reload_enabled": False,
            "auto_reload_interval": 5,
        }
        self.preferences = dict(self._defaults)
        self.directory = os.path.join(GLib.get_user_config_dir(), "catgirldownloader")
        os.makedirs(self.directory, exist_ok=True)
        self.file = os.path.join(self.directory, "config.json")
        if not os.path.exists(self.file):
            f = open(self.file, "w+")
            f.write(json.dumps(self.preferences))
            f.close()
        try:
            f = open(self.file, 'r')
            self.preferences = json.loads(f.read())
            f.close()
            changed = False
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
                    changed = True
            if changed:
                self.set_preference_batch(self.preferences)
        except Exception as e:
            print(e)

    def reload_preferences(self):
        try:
            f = open(self.file, 'r')
            self.preferences = json.loads(f.read())
            f.close()
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
        except Exception as e:
            print(e)

    def get_preference(self, key):
        self.reload_preferences()
        if key in self.preferences:
            return self.preferences[key]
        else:
            return None
    def set_preference(self, key, value):
        self.preferences[key] = value
        try:
            f = open(self.file, "w+")
            f.write(json.dumps(self.preferences))
            f.close()
        except Exception as e:
            print(e)

    def set_preference_batch(self, prefs: dict):
        self.preferences = prefs
        try:
            f = open(self.file, "w+")
            f.write(json.dumps(self.preferences))
            f.close()
        except Exception as e:
            print(e)
