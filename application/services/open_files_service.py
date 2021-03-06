import logging
from typing import Dict
from model.message_archive import MessageArchive


class OpenFile:
    def __init__(self, file):
        self.file = file
        self.dirty = False


class OpenFilesService:
    def __init__(self, filesystem):
        self.open_files: Dict[str: OpenFile] = {}
        self.open_message_archives: Dict[MessageArchive] = {}
        self.filesystem = filesystem

    def close_archive(self, archive):
        target_key = None
        for (key, value) in self.open_files.items():
            if value.file == archive:
                target_key = key
                break
        if target_key:
            del self.open_files[target_key]

    def set_archive_in_use(self, archive):
        for entry in self.open_files.values():
            if entry.file is archive:
                entry.dirty = True
                break

    def is_archive_in_use(self, archive) -> bool:
        for entry in self.open_files.values():
            if entry.file is archive:
                return entry.dirty
        return False

    def to_valid_path_in_filesystem(self, file_path: str):
        source_path = self.filesystem.get_source_path()
        dest_path = self.filesystem.get_dest_path()
        if file_path.startswith(dest_path):
            return file_path[len(dest_path):]
        if file_path.startswith(source_path):
            return file_path[len(source_path):]
        return None

    def open(self, path_in_rom):
        logging.info("Opening " + path_in_rom)
        if path_in_rom in self.open_files:
            logging.info("Found " + path_in_rom + " in cache.")
            return self.open_files[path_in_rom].file

        logging.info(path_in_rom + " was not in the cache. Reading from filesystem...")
        archive = self.filesystem.open_bin("/" + path_in_rom)

        logging.info("Successfully read " + path_in_rom + " from filesystem.")
        self.open_files[path_in_rom] = OpenFile(archive)
        return archive

    def open_message_archive(self, path_in_rom):
        if path_in_rom in self.open_message_archives:
            return self.open_message_archives[path_in_rom]

        archive = self.filesystem.open_localized_bin("/" + path_in_rom)
        message_archive = MessageArchive()
        message_archive.read(archive)
        self.open_message_archives[path_in_rom] = message_archive
        return message_archive

    def save(self):
        logging.info("Saving open files to filesystem.")
        self._save_open_files()
        self._save_open_message_archive()
        logging.info("Save complete.")

    def _save_open_files(self):
        for (path, open_file) in self.open_files.items():
            if open_file.dirty:
                logging.info("Saving " + path + " to filesystem.")
                self._try_save_archive(open_file.file, path)
            else:
                logging.info("Skipping " + path + " because it is not dirty.")

    def _save_open_message_archive(self):
        for (path, message_archive) in self.open_message_archives.items():
            if message_archive.dirty:
                logging.info("Saving " + path + " to filesystem.")
                archive = message_archive.to_bin()
                self._try_save_archive(archive, path, True)
            else:
                logging.info("Skipping " + path + " because it is not dirty.")

    def _try_save_archive(self, archive, path, localized=False):
        try:
            if localized:
                self.filesystem.write_localized_bin("/" + path, archive)
            else:
                self.filesystem.write_bin("/" + path, archive)
        except:
            logging.exception("Failed to save file " + path)

    def clear(self):
        self.open_files.clear()
