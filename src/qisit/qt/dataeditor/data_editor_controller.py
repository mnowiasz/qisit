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
from qisit.core.util import nullify

from babel.numbers import format_decimal, parse_decimal, NumberFormatError

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
        NAME_ONLY = 0
        ITEM_WITH_DESCRIPTION = 1
        INGREDIENTS = 2
        INGREDIENT_UNIT = 3


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
        self._ingredient_icon = None

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
        self.typeComboBox.currentIndexChanged.connect(self.typeComboBox_currentIndexChanged)

        self.okButton.clicked.connect(self.okButton_clicked)
        self.cancelButton.clicked.connect(self.cancelButton_clicked)

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

    def cancelButton_clicked(self):
        if self._selected_index:
            self.load_stackedwidget([self._selected_index, ])

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
        self.load_stackedwidget(selected.indexes())

    def load_stackedwidget(self, selected_indexes: typing.List[QtCore.QModelIndex]):
        """
        Switch the stacked widget accordingly and load the data

        Args:
            selected_indexes: The selected indexs

        Returns:

        """

        self.okButton.setEnabled(False)
        self.cancelButton.setEnabled(False)

        if len(selected_indexes) == 1 and selected_indexes[0].flags() & QtCore.Qt.ItemIsEditable:

            # Those widget would emit a signal when being loaded with data (setPlainText)

            blocked_widgets = (self.descriptionTextEdit, self.unitDescriptionTextEdit, self.typeComboBox)
            for widget in blocked_widgets:
                widget.blockSignals(True)

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

            # Common to all items
            self.nameLineEdit.setReadOnly(False)
            self.nameLineEdit.setText(item.name)

            if model.root_row == model.RootItems.INGREDIENTS and column != model.Columns.REFERENCED:
                self.stackedWidget.setCurrentIndex(self.StackedItems.INGREDIENTS)
                if item.icon:
                    # ToDo: Display/Load icon
                    pass
            else:
                self._ingredient_icon = None
                # Only the names (=title) of these entries are editable
                if model.root_row in (model.RootItems.CATEGORIES, model.RootItems.INGREDIENTGROUPS) \
                        or column == model.Columns.REFERENCED:
                    self.stackedWidget.setCurrentIndex(self.StackedItems.NAME_ONLY)
                elif model.root_row in (model.RootItems.AUTHOR, model.RootItems.CUISINE, model.RootItems.YIELD_UNITS):
                    self.stackedWidget.setCurrentIndex(self.StackedItems.ITEM_WITH_DESCRIPTION)
                    if item.description is not None:
                        self.descriptionTextEdit.setPlainText(item.description)
                    else:
                        self.descriptionTextEdit.clear()
                elif model.root_row == model.RootItems.INGREDIENTUNITS:
                    self.stackedWidget.setCurrentIndex(self.StackedItems.INGREDIENT_UNIT)
                    self.typeComboBox.setCurrentIndex(item.type_)
                    if item.factor is not None:
                        self.factorLineEdit.setText(format_decimal(item.factor))
                        self.baseUnitLabel.setText(data.IngredientUnit.base_units[item.type_].unit_string())
                    else:
                        self.factorLineEdit.clear()
                        self.baseUnitLabel.clear()
                    if item.description is not None:
                        self.unitDescriptionTextEdit.setPlainText(item.description)
                    else:
                        self.unitDescriptionTextEdit.clear()

            # Everything set, unblock the signals
            for widget in blocked_widgets:
                widget.blockSignals(False)

        else:
            self.stackedWidget.setCurrentIndex(self.StackedItems.NAME_ONLY)
            self.nameLineEdit.setReadOnly(True)
            self.nameLineEdit.clear()
            self._selected_index = None


    def okButton_clicked(self):
        """
        OK button has been clicked - save the values

        Returns:

        """

        if self._selected_index is None:
            # Huh?
            return

        # ToDo: Merge with load_stackedwidget
        column = self._selected_index.internalId()
        model = self._item_model
        stackedwidget_index = self.stackedWidget.currentIndex()

        item = None
        if column == model.Columns.REFERENCED:
            # Ingredient list items
            item = model.get_item(self._selected_index.row(), column)
        else:
            item = model.get_item(self._selected_index.row(), column)[0]

        new_name = nullify(self.nameLineEdit.text())
        self.set_modified()
        if new_name is None:
            self.nameLineEdit.setText(item.name)
        else:
            # This will take care of saving the value
            model.setData(self._selected_index, new_name, QtCore.Qt.EditRole)

        # Items with descriptions - Author, Cuisine, Yield Units
        if stackedwidget_index == self.StackedItems.ITEM_WITH_DESCRIPTION:
            new_description = nullify(self.descriptionTextEdit.toPlainText())
            item.description = new_description

        elif stackedwidget_index == self.StackedItems.INGREDIENT_UNIT:
            new_type = self.typeComboBox.currentIndex()
            if new_type >= 0:
                # new_type == -1 should never happen - it would mean no type has been selected which should be
                # impossible. However, better play it safe :-)
                item.type_ = new_type
                new_factor = nullify(self.factorLineEdit.text())
                # Depending on the typem the factor (whatever the user entered) should either be None or have a value

                if new_type != data.IngredientUnit.UnitType.UNSPECIFIC:
                    # Unit Type GROUP isn't visible for the user
                    if new_factor is None:
                        new_factor = 1.0
                    else:
                        try:
                            new_factor = parse_decimal(new_factor)
                        except NumberFormatError:
                            # The user entered garbage. TODO: Tell mit that :-)
                            new_factor = item.factor
                else:
                    # Unspecific -> no Factor
                    new_factor = None

                if new_factor is not None:
                    self.factorLineEdit.setText(str(new_factor))
                else:
                    self.factorLineEdit.clear()
                item.factor = new_factor

        elif stackedwidget_index == self.StackedItems.INGREDIENTS:
            pass

        self.okButton.setEnabled(False)
        self.cancelButton.setEnabled(False)


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
        self._selected_index = None
        self.load_stackedwidget([])

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


    def typeComboBox_currentIndexChanged(self, index: int):
        self.stackedwidget_edited()
        if index == data.IngredientUnit.UnitType.UNSPECIFIC:
            self.baseUnitLabel.clear()
        else:
            self.baseUnitLabel.setText(data.IngredientUnit.base_units[index].unit_string())

    def unitbutton_clicked(self, button_id: int):
        self._unit_conversion_model.load_model(button_id)
