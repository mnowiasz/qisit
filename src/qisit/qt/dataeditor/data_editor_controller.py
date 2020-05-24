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
import typing
from enum import IntEnum

from babel.numbers import format_decimal

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

    # The Indices for the stacked item widget
    class StackedItems(IntEnum):
        EMPTY = 0
        ITEM_DESCRIPTION = 1
        ITEM_ICON = 2
        ITEM_UNIT = 3


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

        self._selected_index = None

        self._unit_conversion_model = conversion_table_model.ConversionTableModel(self._session)
        self._unit_conversion_model.changed.connect(self.set_modified)
        self.unitConversionTableView.setModel(self._unit_conversion_model)
        self.init_ui()

    def _load_ui_states(self):
        """
        Loads the previously saved UI stated

        Returns:

        """

        settings = QtCore.QSettings()
        settings.beginGroup("DataEditor/window")
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("state"):
            self.restoreState(settings.value("state"))
        settings.endGroup()

        settings.beginGroup("DataEditor/splitter")
        if settings.contains("state"):
            self.splitter.restoreState(settings.value("state"))
        if settings.contains("geometry"):
            self.splitter.restoreGeometry(settings.value("geometry"))
        settings.endGroup()

    def _save_ui_states(self):
        """
        Saves the UI states (splitter, window...)

        Returns:

        """
        settings = QtCore.QSettings()

        settings.beginGroup("DataEditor/window")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        settings.endGroup()

        settings.beginGroup("DataEditor/splitter")
        settings.setValue("geometry", self.splitter.saveGeometry())
        settings.setValue("state", self.splitter.saveState())
        settings.endGroup()

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

        self.nameLineEdit.textEdited.connect(self.stackedwidget_edited)
        self.descriptionTextEdit.textChanged.connect(self.stackedwidget_edited)
        self.factorLineEdit.textEdited.connect(self.stackedwidget_edited)
        self.typeComboBox.currentIndexChanged.connect(self.stackedwidget_edited)

        self._load_ui_states()

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
        self._save_ui_states()
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
        self.switch_stacked_widget(selected.indexes())


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

    def stackedwidget_edited(self):
        """"
        Data has been edited in one of the widgets
        """

        self.okButton.setEnabled(True)
        self.cancelButton.setEnabled(True)

    def switch_stacked_widget(self, selected_indexes: typing.List[QtCore.QModelIndex]):
        """
        Switch the stacked widget accordingly

        Args:
            selected_indexes: The selected indexs

        Returns:

        """

        self.okButton.setEnabled(False)
        self.cancelButton.setEnabled(False)

        if len(selected_indexes) == 1 and selected_indexes[0].flags() & QtCore.Qt.ItemIsEditable:
            self.descriptionTextEdit.blockSignals(True)
            self.unitDescriptionTextEdit.blockSignals(True)
            selected_index = selected_indexes[0]
            self._selected_index = selected_index
            model = self._item_model
            column = selected_index.internalId()
            item = None
            if column == model.Columns.REFERENCED:
                # Ingredient list items
                item = model.get_item(selected_index.row(), column)
            else:
                item = model.get_item(selected_index.row(), column)[0]

            self.nameLineEdit.setReadOnly(False)
            self.nameLineEdit.setText(item.name)
            if model.root_row in (model.RootItems.CATEGORIES, model.RootItems.INGREDIENTGROUPS) or column == model.Columns.REFERENCED:
                self.stackedWidget.setCurrentIndex(self.StackedItems.EMPTY)
                self.nameLineEdit.setText(item.name)
            elif model.root_row in (model.RootItems.AUTHOR, model.RootItems.CUISINE, model.RootItems.YIELD_UNITS):
                self.stackedWidget.setCurrentIndex(self.StackedItems.ITEM_DESCRIPTION)
                if item.description is not None:
                    self.descriptionTextEdit.setText(item.description)
                else:
                    self.descriptionTextEdit.clear()
            elif model.root_row == model.RootItems.INGREDIENTS:
                self.stackedWidget.setCurrentIndex((self.StackedItems.ITEM_ICON))
                if item.icon:
                    pass
            elif model.root_row == model.RootItems.INGREDIENTUNITS:
                self.stackedWidget.setCurrentIndex(self.StackedItems.ITEM_UNIT)
                self.typeComboBox.setCurrentIndex(item.type_)
                if item.factor is not None:
                    self.factorLineEdit.setText(format_decimal(item.factor))
                    self.baseUnitLabel.setText(data.IngredientUnit.base_units[item.type_].unit_string())
                else:
                    self.factorLineEdit.clear()
            self.descriptionTextEdit.blockSignals(False)
            self.unitDescriptionTextEdit.blockSignals(False)
        else:
            self.stackedWidget.setCurrentIndex(self.StackedItems.EMPTY)
            self.nameLineEdit.setReadOnly(True)
            self.nameLineEdit.clear()
            self._selected_index = None


    def unitbutton_clicked(self, button_id: int):
        self._unit_conversion_model.load_model(button_id)