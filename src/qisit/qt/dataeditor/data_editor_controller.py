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

import typing
from enum import IntEnum

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from babel.numbers import format_decimal, parse_decimal, NumberFormatError
from sqlalchemy import orm

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify
from qisit.qt.dataeditor import data_editor_model, conversion_table_model, recipe_list_model
from qisit.qt.dataeditor.ui import data_editor


class DataEditorController(data_editor.Ui_dataEditor, Qt.QMainWindow):
    # ToDo: Deduplicate code (taken from recipe_window_controller

    class _Decorators(object):
        @classmethod
        def change(cls, method):
            """
            A wrapper for methods that change the data in some way. The wrapper makes sure that - if necessary -
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

    # The indexes for the stacked item widget
    class StackedItems(IntEnum):
        NAME_ONLY = 0
        ITEM_WITH_DESCRIPTION = 1
        INGREDIENTS = 2
        INGREDIENT_UNIT = 3

    dataCommited = QtCore.pyqtSignal(set)
    """ Emitted (including a list/set of affected Recipe IDs) when the data has been committed """

    recipeDoubleClicked = QtCore.pyqtSignal(data.Recipe)
    """ Emitted when the user double clicked on a recipe so the RecipeListController may open/show the recipe """

    def __init__(self, session: orm.Session):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()
        self._session = session
        self._settings = QtCore.QSettings()

        self._transaction_started = False

        self.setupUi(self)
        self._item_model = data_editor_model.DataEditorModel(self._session)
        self._item_model.changed.connect(self.set_modified)
        self.dataColumnView.setModel(self._item_model)

        self._unit_conversion_model = conversion_table_model.ConversionTableModel(self._session)
        self._unit_conversion_model.changed.connect(self.set_modified)
        self.unitConversionTableView.setModel(self._unit_conversion_model)

        self._selected_index = None

        # Temporarily stores the icon (if any) the user has loaded
        self._ingredient_icon = None

        self.recipeListLayout = QtWidgets.QVBoxLayout()
        self.recipeListView = QtWidgets.QListView()
        self._recipe_list_model = recipe_list_model.RecipeListModel()
        self.init_ui()

    def _load_ui_states(self):
        """
        Loads the previously saved UI stated

        Returns:

        """

        settings = self._settings
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
        settings = self._settings

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
        #self.dataColumnView.doubleClicked.connect(self.dataColumnView_doubleclicked)
        self.dataColumnView.selectionModel().selectionChanged.connect(self.dataColumnView_selectionChanged)
        self.dataColumnView.updatePreviewWidget.connect(self.dataColumnView_updatePreviewWidget)

        # Setup the button group so the id reflect the unit types
        self.unitButtonGroup.setId(self.massRadioButton, data.IngredientUnit.UnitType.MASS)
        self.unitButtonGroup.setId(self.volumeRadioButton, data.IngredientUnit.UnitType.VOLUME)
        self.unitButtonGroup.setId(self.quantityRadioButton, data.IngredientUnit.UnitType.QUANTITY)
        self.unitButtonGroup.buttonClicked[int].connect(self.unitbutton_clicked)

        self.nameLineEdit.textEdited.connect(self.stackedwidget_edited)
        self.descriptionTextEdit.textChanged.connect(self.stackedwidget_edited)
        self.factorLineEdit.textEdited.connect(self.stackedwidget_edited)
        self.typeComboBox.currentIndexChanged.connect(self.typeComboBox_currentIndexChanged)

        self.loadIconButton.clicked.connect(self.loadIconButton_clicked)
        self.deleteIconButton.clicked.connect(self.deleteIconButton_clicked)

        self.okButton.clicked.connect(self.okButton_clicked)
        self.cancelButton.clicked.connect(self.cancelButton_clicked)

        self.recipeListView.setModel(self._recipe_list_model)
        self.recipeListView.setWordWrap(True)
        self.recipeListView.doubleClicked.connect(self.recipeListView_doubleclicked)

        self.dataColumnView.setPreviewWidget(self.recipeListView)

        self._load_ui_states()

        selected_id = self.unitButtonGroup.checkedId()
        if selected_id is None:
            # Shouldn't happen
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
        """
        Deletes the item in question

        Args:
            checked (): ignored

        Returns:

        """

        for index in self.dataColumnView.selectedIndexes():
            # Better play it safe
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

    def dataColumnView_selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        """
        The selection has been changed. Used to enable/disable the delete action and to load the stacked widget

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

    def dataColumnView_updatePreviewWidget(self, index: QtCore.QModelIndex):
        item = None
        recipe_list = None
        column = index.internalId()
        model = self._item_model
        data = model.get_item(index.row(), index.internalId())
        if column == model.Columns.INGREDIENTLIST_ENTRIES:
            item = data
            recipe_list = [item.recipe, ]
        else:
            item = data[0]
            recipe_list = [recipe for recipe in item.recipes]


        self._recipe_list_model.set_recipe_list(recipe_list)

    def deleteIconButton_clicked(self):
        self._ingredient_icon = None
        self.iconLabel.clear()
        self.deleteIconButton.setEnabled(False)
        self.stackedwidget_edited()

    def loadIconButton_clicked(self):
        """
        The load icon button has been clicked
        Returns:

        """

        _translate = translate

        # TODO: Merge with RecipeWindow/deduplicate
        image_filter = _translate("DataEditor", "Imagefiles ({})").format(" ".join(
            ["*.{}".format(supported_format.data().decode()) for supported_format in
             Qt.QImageReader.supportedImageFormats()]))
        options = Qt.QFileDialog.Options()

        filename, filter_ = Qt.QFileDialog.getOpenFileName(self, _translate("DataEditor", "Select an Icon"),
                                                           filter=image_filter, options=options)
        if not filename:
            return

        image_reader = Qt.QImageReader(filename)
        image = image_reader.read()
        if image.isNull():
            Qt.QMessageBox.critical(self, _translate("DataEditor", "Error loading file"),
                                    _translate("DataEditor", "Unable to read {}: {}")
                                    .format(filename, image_reader.errorString()))
            return

        settings = self._settings
        icon_height = settings.value("preferences/icons/height", 16)

        # 1. Scale the images (if necessary)
        if image.height() > icon_height:
            icon_image = image.scaled(icon_height, icon_height, QtCore.Qt.KeepAspectRatio)
        else:
            icon_image = image

        # 2. Export the images to PNG byte format
        image_buffer = QtCore.QBuffer()
        image_buffer.open(QtCore.QIODevice.ReadWrite)
        icon_image.save(image_buffer, "PNG")

        self.iconLabel.setPixmap(Qt.QPixmap(icon_image))
        self._ingredient_icon = image_buffer.data()
        image_buffer.close()

        self.deleteIconButton.setEnabled(True)
        self.stackedwidget_edited()

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

            # Those widget would emit a signal when being loaded with data
            blocked_widgets = (self.descriptionTextEdit, self.unitDescriptionTextEdit, self.typeComboBox)
            for widget in blocked_widgets:
                widget.blockSignals(True)

            selected_index = selected_indexes[0]
            self._selected_index = selected_index
            model = self._item_model
            column = selected_index.internalId()

            the_item = None
            if column == model.Columns.INGREDIENTLIST_ENTRIES:
                # Ingredient list items
                the_item = model.get_item(selected_index.row(), column)
            else:
                the_item = model.get_item(selected_index.row(), column)[0]

            # Common to all items
            self.nameLineEdit.setReadOnly(False)
            self.nameLineEdit.setText(the_item.name)

            if model.root_row == model.RootItems.INGREDIENTS and column != model.Columns.INGREDIENTLIST_ENTRIES:
                self.stackedWidget.setCurrentIndex(self.StackedItems.INGREDIENTS)
                if the_item.icon:
                    icon_pixmap = Qt.QPixmap()
                    if icon_pixmap.loadFromData(the_item.icon):
                        self.iconLabel.setPixmap(icon_pixmap)
                        self.deleteIconButton.setEnabled(True)
                else:
                    self.iconLabel.clear()
                    self.deleteIconButton.setEnabled(False)
            else:
                self._ingredient_icon = None

                # Only the names (=title) of these entries are editable
                if model.root_row in (model.RootItems.CATEGORIES, model.RootItems.INGREDIENTGROUPS) \
                        or column == model.Columns.INGREDIENTLIST_ENTRIES:
                    self.stackedWidget.setCurrentIndex(self.StackedItems.NAME_ONLY)
                elif model.root_row in (model.RootItems.AUTHOR, model.RootItems.CUISINE, model.RootItems.YIELD_UNITS):
                    # These three are very similar and share a description
                    self.stackedWidget.setCurrentIndex(self.StackedItems.ITEM_WITH_DESCRIPTION)
                    if the_item.description is not None:
                        self.descriptionTextEdit.setPlainText(the_item.description)
                    else:
                        self.descriptionTextEdit.clear()
                elif model.root_row == model.RootItems.INGREDIENTUNITS:
                    self.stackedWidget.setCurrentIndex(self.StackedItems.INGREDIENT_UNIT)
                    self.typeComboBox.setCurrentIndex(the_item.type_)
                    if the_item.factor is not None:
                        self.factorLineEdit.setText(format_decimal(the_item.factor))
                        self.baseUnitLabel.setText(data.IngredientUnit.base_units[the_item.type_].unit_string())
                    else:
                        self.factorLineEdit.clear()
                        self.baseUnitLabel.clear()
                    if the_item.description is not None:
                        self.unitDescriptionTextEdit.setPlainText(the_item.description)
                    else:
                        self.unitDescriptionTextEdit.clear()

            # Everything set, unblock the signals
            for widget in blocked_widgets:
                widget.blockSignals(False)

        else:
            # Multiple selections
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

        the_item = None
        if column == model.Columns.INGREDIENTLIST_ENTRIES:
            # Ingredient list items
            the_item = model.get_item(self._selected_index.row(), column)
        else:
            the_item = model.get_item(self._selected_index.row(), column)[0]

        new_name = nullify(self.nameLineEdit.text())
        self.set_modified()
        if new_name is None:
            self.nameLineEdit.setText(the_item.name)
        else:
            # This will take care of saving the value
            model.setData(self._selected_index, new_name, QtCore.Qt.EditRole)

            # Trimmed name
            self.nameLineEdit.setText(new_name)

        # Items with descriptions - Author, Cuisine, Yield Units
        if stackedwidget_index == self.StackedItems.ITEM_WITH_DESCRIPTION:
            new_description = nullify(self.descriptionTextEdit.toPlainText())
            the_item.description = new_description

        elif stackedwidget_index == self.StackedItems.INGREDIENT_UNIT:
            new_type = self.typeComboBox.currentIndex()
            if new_type >= 0:
                # new_type == -1 should never happen - it would mean no type has been selected which should be
                # impossible. However, better play it safe :-)
                the_item.type_ = new_type
                new_factor = nullify(self.factorLineEdit.text())

                # Depending on the type of  the factor (whatever the user entered) should either be None or have a
                # value. Unit Type GROUP isn't visible for the user so don't bother to check
                if new_type != data.IngredientUnit.UnitType.UNSPECIFIC:
                    if new_factor is None:
                        new_factor = 1.0
                    else:
                        try:
                            new_factor = parse_decimal(new_factor)
                        except NumberFormatError:
                            # The user entered garbage. TODO: Tell him that :-)
                            new_factor = the_item.factor
                else:
                    # Unspecific -> no Factor
                    new_factor = None

                if new_factor is not None:
                    self.factorLineEdit.setText(str(new_factor))
                else:
                    self.factorLineEdit.clear()
                the_item.factor = new_factor

        elif stackedwidget_index == self.StackedItems.INGREDIENTS:
            the_item.icon = self._ingredient_icon
            model.affected_recipe_ids = model.affected_recipe_ids.union([recipe.id for recipe in the_item.recipes])

        self.okButton.setEnabled(False)
        self.cancelButton.setEnabled(False)

    def recipe_changed(self, recipe: data.Recipe):
        self._session.expire_all()

    def recipeListView_doubleclicked(self, index: QtCore.QModelIndex):
        recipe = self._recipe_list_model.get_item(index.row())
        self.recipeDoubleClicked.emit(recipe)

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
