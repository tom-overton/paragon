import logging
from typing import cast
from PySide2 import QtCore
from PySide2.QtCore import QSortFilterProxyModel
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QFileDialog
from model.module import Module, TableModule
from model.open_files_model import OpenFilesModel
from services.driver import Driver
from ui.autogen.ui_main_window import Ui_MainWindow
from ui.object_editor import ObjectEditor
from ui.simple_editor import SimpleEditor


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, close_handler, driver: Driver):
        super().__init__()
        self.setupUi(self)
        self.driver = driver
        self.open_editors = {}
        self.close_handler = close_handler
        self.setWindowTitle("Paragon")
        self.setWindowIcon(QIcon("paragon.ico"))

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.driver.module_model)
        self.module_list_view.setModel(self.proxy_model)
        self.editors_list_view.setModel(self.driver.services_model)

        self.open_file_model = OpenFilesModel()
        self.file_list_view.setModel(self.open_file_model)

        self.search_field.textChanged.connect(self.proxy_model.setFilterRegExp)
        self.module_list_view.activated.connect(self._on_module_activated)
        self.editors_list_view.activated.connect(self._on_editor_activated)
        self.file_list_view.selectionModel().currentRowChanged.connect(self._on_file_list_selection_change)
        self.close_button.clicked.connect(self._on_close_file_pressed)
        self.action_save.triggered.connect(self.save)
        self.action_close.triggered.connect(self.close)
        self.action_quit.triggered.connect(self.quit_application)

        logging.info("Opened main window.")

    def save(self):
        self.driver.save()

    def close(self):
        self.hide()
        self.close_handler()

    @staticmethod
    def quit_application():
        exit(0)

    def _on_file_list_selection_change(self, index):
        self.close_button.setEnabled(self.open_file_model.can_close(index.row()))

    def _on_close_file_pressed(self):
        self.open_file_model.close(self.file_list_view.currentIndex().row())

    def _on_module_activated(self, index):
        logging.info("Module " + str(index.row()) + " activated.")

        # First, see if the module is already open.
        module: Module = self.proxy_model.data(index, QtCore.Qt.UserRole)
        if module in self.open_editors:
            logging.info(module.name + " is cached. Reopening editor...")
            self.driver.set_module_used(module)
            self.open_editors[module].show()
            return

        # Next, handle common modules.
        if not module.unique:
            logging.info(module.name + " is a common module. Prompting for a file...")
            target_file = QFileDialog.getOpenFileName(self)
            if not target_file[0]:
                logging.info("No file selected - operation aborted.")
                return
            logging.info("File selected. Opening common module...")
            module = self.driver.handle_open_for_common_module(module, target_file[0])

            # Hack to keep the display for the open file model consistent.
            self.open_file_model.beginResetModel()
            self.open_file_model.endResetModel()

        if module.type == "table":
            logging.info("Opening " + module.name + " as a TableModule.")
            editor = SimpleEditor(self.driver, cast(TableModule, module))
        elif module.type == "object":
            logging.info("Opening " + module.name + " as an ObjectModule.")
            editor = ObjectEditor(self.driver, module)
        else:
            logging.error("Attempted to open an unsupported module type.")
            raise NotImplementedError

        self.driver.set_module_used(module)
        self.open_editors[module] = editor
        editor.show()

    def _on_editor_activated(self, index):
        model = self.driver.services_model
        service = model.data(index, QtCore.Qt.UserRole)
        service.editor.show()
