#  Copyright (c) 2020 by Mark Nowiasz
#
#  This file is part of Qisit (https://github.com/mnowiasz/qisit)
#
#  Qisit is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Qisit is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with qisit.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from sqlalchemy import create_engine, exc, func, orm
import typing
from qisit import translate
from qisit.core import db
from qisit.core.db import data
from qisit.core.util import nullify
from qisit.qt.dataeditor.ui import data_editor
from qisit.qt.dataeditor import data_editor_model

class DataEditorController(data_editor.Ui_dataEditor, Qt.QMainWindow):

    # ToDo: Deduplicate code (taken from recipe_window_controller
    class _Decorators(object):
        @classmethod
        def change(cls, method):
            """
            A wrapper for methods that change the recipe data in some way. The wrapper makes sure that - if necessary -
            a new nested transaction will be started and that the "changed" flag will be set

            Args:
                method ():

            Returns:
                wrapped method
            """

            def wrapped(self, *args, **kwargs):
                if not self._transaction_started:
                    self._session.begin_nested()
                    self._transaction_started = True
                self.modified = True
                method(self, *args, **kwargs)

            return wrapped

    dataCommited = QtCore.pyqtSignal(set)
    """ Emitted (including a list/set of affected Recipe IDs) when the data has been committed """

    recipeDoubleClicked = QtCore.pyqtSignal(data.Recipe)
    """ Emitted when the user double clicked on a recipe"""

    def __init__(self, session : orm.Session):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()
        self._session = session
        self._transaction_started = False

        self.setupUi(self)
        self._model = data_editor_model.DataEditorModel(self._session)
        self._model.changed.connect(self.set_modified)
        self.dataColumnView.setModel(self._model)
        self.init_ui()

    @property
    def modified(self) -> bool:
        return self.isWindowModified()

    @modified.setter
    def modified(self, modified: bool):
        self.setWindowModified(modified)
        self.actionSave.setEnabled(modified)
        self.actionRevert.setEnabled(modified)

    def actionRevert_triggered(self, checked: bool = False):
        self.revert_data()

    def actionSave_triggered(self, checked: bool = False):
        self.save_data()

    def init_ui(self):
        self.setWindowTitle(f"{self.windowTitle()} [*]")
        self.setWindowIcon(QtGui.QIcon(":/logos/qisit_128x128.png"))
        self.actionSave.triggered.connect(self.actionSave_triggered)
        self.actionRevert.triggered.connect(self.actionRevert_triggered)
        self.dataColumnView.doubleClicked.connect(self.dataColumnView_doubleclicked)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Window has been closed by the user

        Args:
            event ():

        Returns:

        """
        # TODO: Ask
        if self._transaction_started:
            self._session.rollback()
        self.modified = False
        event.accept()

    def dataColumnView_doubleclicked(self, index: QtCore.QModelIndex):
        column = index.internalId()
        row = index.row()
        recipe = None
        if column == self._model.Columns.RECIPES:
            recipe = self._model.get_item(row, column)
        elif column == self._model.Columns.REFERENCED:
            root_row = self._model.root_row()
            if root_row not in (self._model.RootItems.INGREDIENTS, self._model.RootItems.INGREDIENTUNITS):
                recipe = self._model.get_item(row, column)
        if recipe is not None:
           self.recipeDoubleClicked.emit(recipe)

    def revert_data(self):
        """
        Reverts the recipe to the data stored in the database

        Returns:

        """

        if self._transaction_started:
            self._session.rollback()
        self._transaction_started = False
        self._model.reset()
        self.dataColumnView.reset()
        self.modified = False

    def save_data(self):
        """
        Save the (modified) data into the current session

        Returns:

        """

        if not self._transaction_started:
            raise ValueError("No transaction started")

        self._session.commit()
        self.modified = False
        self._transaction_started = False
        self.dataCommited.emit(self._model.affected_recipe_ids)
        self._model.affected_recipe_ids.clear()


    @_Decorators.change
    def set_modified(self):
        """ Nothing to do here, the decorator does it work """
        pass



