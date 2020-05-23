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
from sqlalchemy import orm

from qisit.core.db import data
from qisit.qt.dataeditor import data_editor_model, conversion_table_model
from qisit.qt.dataeditor.ui import data_editor


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

    def __init__(self, session: orm.Session):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()
        self._session = session
        self._transaction_started = False

        self.setupUi(self)
        self._item_model = data_editor_model.DataEditorModel(self._session)
        self._item_model.changed.connect(self.set_modified)
        self.dataColumnView.setModel(self._item_model)

        self._unit_conversion_model = conversion_table_model.ConversionTableModel(self._session)
        self._unit_conversion_model.changed.connect(self.set_modified)
        self.unitConversionTableView.setModel(self._unit_conversion_model)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"{self.windowTitle()} [*]")
        self.setWindowIcon(QtGui.QIcon(":/logos/qisit_128x128.png"))
        self.actionDelete.triggered.connect(self.actionDelete_triggered)
        self.actionSave.triggered.connect(self.actionSave_triggered)
        self.actionRevert.triggered.connect(self.actionRevert_triggered)
        self.dataColumnView.addAction(self.actionDelete)
        self.dataColumnView.doubleClicked.connect(self.dataColumnView_doubleclicked)
        self.dataColumnView.selectionModel().selectionChanged.connect(self.dataColumnView_selectionChanged)
        self.unitButtonGroup.setId(self.massRadioButton, data.IngredientUnit.UnitType.MASS)
        self.unitButtonGroup.setId(self.volumeRadioButton, data.IngredientUnit.UnitType.VOLUME)
        self.unitButtonGroup.setId(self.quantityRadioButton, data.IngredientUnit.UnitType.QUANTITY)
        self.unitButtonGroup.buttonClicked[int].connect(self.unitbutton_clicked)

        selected_id = self.unitButtonGroup.checkedId()
        if selected_id == None:
            selected_id = data.IngredientUnit.UnitType.MASS
        self._unit_conversion_model.load_model(selected_id)


    @property
    def modified(self) -> bool:
        return self.isWindowModified()

    @modified.setter
    def modified(self, modified: bool):
        self.setWindowModified(modified)
        self.actionSave.setEnabled(modified)
        self.actionRevert.setEnabled(modified)

    def actionDelete_triggered(self, checked: bool = False):
        for index in self.dataColumnView.selectedIndexes():
            if self._item_model.is_deletable(index):
                self._item_model.delete_item(index)

    def actionRevert_triggered(self, checked: bool = False):
        self.revert_data()

    def actionSave_triggered(self, checked: bool = False):
        self.save_data()

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
        """
        User double clicked on an item
        Args:
            index ():  The item

        Returns:

        """
        column = index.internalId()
        row = index.row()
        recipe = None
        # Find out the index that contain a recipe
        if column == self._item_model.Columns.RECIPES:
            # Like the column says - always recipes
            recipe = self._item_model.get_item(row, column)
        elif column == self._item_model.Columns.REFERENCED:
            if self._item_model.root_row not in (self._item_model.RootItems.INGREDIENTS, self._item_model.RootItems.INGREDIENTUNITS):
                recipe = self._item_model.get_item(row, column)
        if recipe is not None:
            self.recipeDoubleClicked.emit(recipe)

    def dataColumnView_selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        """
        The selection has been changed. Used to enable/disable the delete action

        Args:
            selected (): Selected indexes
            deselected (): Deselected index

        Returns:

        """

        delete_action_enabled = False

        for index in selected.indexes():
            delete_action_enabled |= self._item_model.is_deletable(index)
        self.actionDelete.setEnabled(delete_action_enabled)

    def revert_data(self):
        """
        Reverts the recipe to the data stored in the database

        Returns:

        """

        if self._transaction_started:
            self._session.rollback()
        self._transaction_started = False
        self._item_model.reset()
        self.dataColumnView.reset()
        self._unit_conversion_model.reload_model()
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
        self.dataCommited.emit(self._item_model.affected_recipe_ids)
        self._item_model.affected_recipe_ids.clear()

    @_Decorators.change
    def set_modified(self):
        """ Nothing to do here, the decorator does it work """
        pass

    def unitbutton_clicked(self, button_id: int):
        self._unit_conversion_model.load_model(button_id)