import json
import logging

from model.project import Project


class SettingsService:
    def __init__(self):
        logging.info("Loading settings from disk.")
        try:
            with open("paragon.json", "r") as f:
                js = json.load(f)
                self.cached_project = self._read_cached_project_from_json(js)

            logging.info("Successfully loaded settings from disk.")
        except (IOError, KeyError, json.JSONDecodeError):
            logging.exception("Unable to load settings. Using defaults.")
            self.cached_project = None

    def save_settings(self):
        logging.info("Saving settings.")

        settings_dict = {
            "cached_project": self._created_cached_project_entry()
        }

        logging.info("Serialized settings. Writing to disk...")
        try:
            with open("paragon.json", "w") as f:
                json.dump(settings_dict, f)

            logging.info("Successfully wrote settings to disk.")
        except IOError:
            logging.exception("Unable to write settings to disk.")

    def _created_cached_project_entry(self):
        if self.cached_project:
            return self.cached_project.to_dict()
        return None

    @staticmethod
    def _read_cached_project_from_json(js):
        try:
            return Project.from_json(js["cached_project"])
        except (FileNotFoundError, KeyError):
            logging.exception("Could not read cached project.")
            return None
