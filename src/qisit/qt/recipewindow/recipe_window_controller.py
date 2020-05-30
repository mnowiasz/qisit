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

import math
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from babel.dates import format_timedelta
from sqlalchemy import func, orm

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify, zero_to_none
from qisit.qt import misc
from qisit.qt.misc.ingredient_completer import IngredientCompleter
from qisit.qt.misc.lstrip_validator import LStripValidator
from qisit.qt.recipewindow.combobox_model import DBComboBoxModel, UnitComboBoxModel
from qisit.qt.recipewindow.delegate import AmountDelegate, EditorDelegate
from qisit.qt.recipewindow.image_table_model import ImageTableModel
from qisit.qt.recipewindow.ingredient_treeview_model import IngredientTreeViewModel
from qisit.qt.recipewindow.ui import recipe


class RecipeWindow(recipe.Ui_RecipeWindow, QtWidgets.QMainWindow):
    """ The controller for a RecipeWindow"""

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

    # TODO: Propagate this to all other open recipe windows
    recipeChanged = QtCore.pyqtSignal(data.Recipe)
    """ Emitted after the recipe has been saved so the recipe list (and categories, cuisine, and so on) can reload  """

    def __init__(self, session: orm.Session, recipe: data.Recipe, new_recipe: bool = False):
        """
        Init.

        Args:
            session (): The database session
            recipe (): The recipe
            new_recipe (): The recipe in question is new. This is important when closing the window.

        """
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()
        self._recipe = recipe
        self._session = session
        self._translate = translate
        self.__editable = False
        self.__new_recipe = new_recipe
        self.__force_closed = False

        # Bold font used in the ingredient tree
        self._bold_font = QtGui.QFont()
        self._bold_font.setBold(True)

        # Used to determine  if there's already a (nested) transaction going on or if a new one should be started
        self._transaction_started = False

        # Comboboxes
        self._author_combobox_model = DBComboBoxModel(self._session, data.Author)
        self._cuisine_combobox_model = DBComboBoxModel(self._session, data.Cuisine)
        self._yield_combobox_model = DBComboBoxModel(self._session, data.YieldUnitName)
        self._unit_combobox_model = UnitComboBoxModel(self._session)
        self._unit_combobox_model.unitsToBeChanged.connect(self.set_modified)

        self._lstrip_validator = LStripValidator()
        self._category_button_menu = QtWidgets.QMenu()

        self._image_table_model = ImageTableModel(session=self._session, recipe=self._recipe)
        self._ingredient_treeview_model = IngredientTreeViewModel(self._recipe)

        self.setupUi(self)

        self._amount_delegate = AmountDelegate()
        self._ingredient_completer = IngredientCompleter(self._session)
        self._ingredient_delegate = EditorDelegate(self._ingredient_completer)
        self._image_description_delegate = EditorDelegate()
        self._text_edits = (self.descriptionPlainTextEdit, self.instructionsPlainTextEdit, self.notesPlainTextEdit)

        self.init_ui()
        self.load_data()
        self.editable = self.__new_recipe

    def _clear_new_ingredient(self):
        """
        Clears the new ingredient input fields

        Returns:

        """
        self.newIngredientLineEdit.clear()
        self.newIngredientAmountEditor.amountLineEdit.clear()
        self.newIngredientAmountEditor.unitComboBox.setCurrentIndex(0)
        self.isGroupCheckBox.setChecked(False)

    def _enable_comboboxes(self, enabled: bool = True):
        """
        Activates/Deactivates the ComboBoxes

        Args:
            enabled (): self explanatory

        Returns:

        """
        for combobox in (self.yieldsComboBox, self.authorComboBox, self.cuisineComboBox):
            combobox.setEnabled(enabled)

    def _enable_misc_elements(self, enabled: bool = True):
        """
        Enable/disable misc elements

        Args:
            enabled (): self explanatory

        Returns:

        """

        for element in (self.actionAdd_Image_s, self.addImagesButton, self.catgoriesButton, self.neverCookedCheckBox):
            element.setEnabled(enabled)

        # If the yield is 0, there's no point in converting the ingredients to a higher value.
        self.convertYieldsCheckBox.setEnabled(enabled and self._recipe.yields > 0.0)

        if self._recipe.last_cooked:
            self.lastCookedDateEdit.setEnabled(enabled)
        else:
            self.lastCookedDateEdit.setEnabled(False)

        self.newIngredientAmountEditor.seteditable(enabled)

    def _enable_spinboxes(self, editable: bool = False):
        """
        Makes the SpinBoxes editable or not

        Args:
            editable (): self explanatory

        Returns:

        """
        for spinbox in (self.yieldsDoubleSpinBox, self.ratingSpinBox):
            spinbox.setReadOnly(not editable)

    def _restore_image_columns(self):
        """
        Restore the image columns after the model has been reset or the first image has been added

        Returns:

        """
        settings = QtCore.QSettings()

        settings.beginGroup("RecipeWindow/imageTableView/horizontalHeader")
        if settings.contains("geometry"):
            self.imageTableView.horizontalHeader().restoreGeometry(settings.value("geometry"))
        if settings.contains("state"):
            self.imageTableView.horizontalHeader().restoreState(settings.value("state"))

    def _restore_ingredient_columns(self):
        """
        Restores the the image tree columns. Done after each model reset and - similar - after the
        first ingredient has been added to the tree

        Returns:

        """

        settings = QtCore.QSettings()
        settings.beginGroup("RecipeWindow/ingredientTreeView/header")

        if settings.contains("geometry"):
            self.ingredientTreeView.header().restoreGeometry(settings.value("geometry"))
        if settings.contains("state"):
            self.ingredientTreeView.header().restoreState(settings.value("state"))
        settings.endGroup()

        # To be safe
        for column in (IngredientTreeViewModel.IngredientColumns.POSITION,
                       IngredientTreeViewModel.IngredientColumns.INGREDIENTLISTROW):
            self.ingredientTreeView.setColumnHidden(column, True)

    def _load_image_group(self):
        """ Set up the image group """

        self._image_table_model.load_model()
        number_of_images = len(self._recipe.imagelist)

        # No images - nothing to do
        if number_of_images == 0:
            self._set_image_label(None)
        else:
            the_image = self._recipe.imagelist[0]
            self._set_image_label(the_image.image)
            self.imageLabel.setStatusTip(the_image.description)

    def _load_markdown_textedits(self):
        """
        Sync the markdown TextViews to the plain text TextViews content

        Returns:

        """
        for plain_edit, markdown_edit in ((self.descriptionPlainTextEdit, self.descriptionMarkDownTextEdit),
                                          (self.instructionsPlainTextEdit, self.instructionsMarkdownTextEdit),
                                          (self.notesPlainTextEdit, self.notesMarkdownTextEdit)):
            markdown_edit.setMarkdown(plain_edit.toPlainText())

    def _load_ui_states(self):
        """
        Loads the saved states from the settings

        Returns:

        """

        settings = QtCore.QSettings()
        for widget in (self, self.mainSplitter, self.imageSplitter, self.textViewSplitter):
            settings.beginGroup(f"RecipeWindow/{widget.objectName()}")
            if settings.contains("geometry"):
                widget.restoreGeometry(settings.value("geometry"))
            if settings.contains("state"):
                widget.restoreState(settings.value("state"))
            settings.endGroup()

        settings.beginGroup("RecipeWindow")
        if settings.contains("imageTableView/horizontalHeader/geometry"):
            self.imageTableView.horizontalHeader().restoreGeometry(
                settings.value("imageTableView/horizontalHeader/geometry"))
        if settings.contains("imageTableView/horizontalHeader/state"):
            self.imageTableView.horizontalHeader().restoreState(settings.value("imageTableView/horizontalHeader/state"))
        if settings.contains("mainTabWidget/currentindex"):
            self.mainTabWidget.setCurrentIndex(int(settings.value("mainTabWidget/currentindex")))
        settings.endGroup()

    def _save_ui_states(self):
        """
        Saves the states/geometry of the widgets for later loading

        Returns:

        """
        settings = QtCore.QSettings()
        for widget in (self, self.mainSplitter, self.imageSplitter, self.textViewSplitter):
            settings.beginGroup(f"RecipeWindow/{widget.objectName()}")
            settings.setValue("geometry", widget.saveGeometry())
            settings.setValue("state", widget.saveState())
            settings.endGroup()

        settings.beginGroup("RecipeWindow")

        # Otherwise the data of an empty table would be saved
        if self._image_table_model.rowCount() > 0:
            settings.setValue("imageTableView/horizontalHeader/geometry",
                              self.imageTableView.horizontalHeader().saveGeometry())
            settings.setValue("imageTableView/horizontalHeader/state",
                              self.imageTableView.horizontalHeader().saveState())
        # Same thing
        if self._ingredient_treeview_model.rowCount() > 0:
            settings.setValue("ingredientTreeView/geometry", self.ingredientTreeView.saveGeometry())
            settings.setValue("ingredientTreeView/header/geometry", self.ingredientTreeView.header().saveGeometry())
            settings.setValue("ingredientTreeView/header/state", self.ingredientTreeView.header().saveState())
        settings.setValue("mainTabWidget/currentindex", self.mainTabWidget.currentIndex())
        settings.endGroup()

    def _set_category_button_menu(self):
        """
        Sets the category's button menu

        Returns:

        """

        categories = self._session.query(data.Category).order_by(func.lower(data.Category.name)).all()
        menu = self._category_button_menu

        menu.clear()
        # The top action is adding a new category. After that all existing categories will be added to the menu
        menu.addAction(self.actionNew_Category)
        menu.addSeparator()
        for category in categories:
            category_action = QtWidgets.QAction(parent=self.catgoriesButton)
            category_action.setText(str(category))
            category_action.setCheckable(True)
            category_action.setEnabled(True)
            category_action.triggered.connect(lambda enabled, cat=category: self.actionCategory_triggered(cat, enabled))
            if category in self._recipe.categories:
                category_action.setChecked(True)
            menu.addAction(category_action)

    def _set_category_line_edit(self):
        if len(self._recipe.categories) > 0:
            self.categoriesLineEdit.setText(", ".join([category.name for category in self._recipe.categories]))
        else:
            self.categoriesLineEdit.setText(None)

    def _set_cooking_timeeditors(self):
        """
        Fills the time editor with the recipe's values

        Returns:

        """

        for time_value, timeeditor in ((self._recipe.preparation_time, self.preparationTimeEditor),
                                       (self._recipe.cooking_time, self.cookingTimeEditor),
                                       (self._recipe.total_time, self.totalTimeEditor)):
            if time_value is None:
                time_value = 0
            timeeditor.value = time_value

        self._set_cooking_timelineedits()

    def _set_cooking_timelineedits(self):
        """
        Formats the times in the time LineEdits accoring to it's brother timeeditors

        Returns:

        """

        for timelineedit, timeeditor in ((self.preparationTimeLineEdit, self.preparationTimeEditor),
                                         (self.cookingTimeLineEdit, self.cookingTimeEditor),
                                         (self.totalTimeLineEdit, self.totalTimeEditor)):
            timevalue = timeeditor.value
            timestring = None

            if timevalue > 0:
                timestring = format_timedelta(timevalue, threshold=2)

            timelineedit.setText(timestring)

    def _set_image_label(self, image: bytes = None):
        """
        Sets the image label.

        Args:
            image (): The image (bytes, JPEG) or None

        Returns:

        """
        if image is None:
            self.imageLabel.setPixmap(QtGui.QPixmap(":/icons/image-32.png"))
            self.imageLabel.setStatusTip(None)
        else:
            pixmap = QtGui.QPixmap()
            if pixmap.loadFromData(image):
                self.imageLabel.setPixmap(pixmap)
                self.imageLabel.setText(None)

    def _set_recipe_title(self):
        """
        Sets the recipe title. Also sets the window title

        Returns:

        """
        self.setWindowTitle(f"{self._recipe.title} [*]")
        self.recipeTitleLineEdit.setText(self._recipe.title)

    def _set_windowicon(self):
        """
        The window icon. It's either the first image in recipe's image list or qisit's own

        Returns:

        """

        if len(self._recipe.imagelist) > 0:
            the_image = self._recipe.imagelist[data.RecipeImage.main_image_pos]
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(the_image.thumbnail)
            self.setWindowIcon(QtGui.QIcon(pixmap))
        else:
            self.setWindowIcon(QtGui.QIcon(":/logos/qisit_128x128.png"))

    def _switch_textedits(self, editable: bool = False):
        """
        Switches the widgets between edit (plain text) and view (markdow) mode

        Args:
            editable ():

        Returns:

        """
        stacked_index = 1
        if editable:
            stacked_index = 0

        for stacked_widget in (self.descriptionStackedWidget, self.instructionsStackedWidget, self.notesStackedWidget):
            stacked_widget.setCurrentIndex(stacked_index)

        # Take the changed markdown (in source form) from the plaintext widgets when not editable - there's no
        # reason to change the text every time the plaintext TextView are modified, because the markdown TextEdits
        # are not visible at this moment anyway. They become visible when in read-only mode.
        if not editable:
            self._load_markdown_textedits()

    def _switch_timeedits(self, editable: bool = False):
        """
        Switch the widgets between LineEdits (display) and TimeEditor (edit)

        Args:
            editable ():

        Returns:

        """

        stacked_index = 0
        if editable:
            stacked_index = 1

        for stacked_widget in (self.preparationStackedWidget, self.cookingStackedWidget, self.totalTimeStackedWidget):
            stacked_widget.setCurrentIndex(stacked_index)

        # The values could have changed
        self._set_cooking_timelineedits()

    def _update_add_ingredients_checkboxes(self):
        """
        Sets the checkboxes depending on the user's selection and the checkboxes itself

        Returns:

        """

        # First have a look if the checkboxes should be enabled at all. When the user has chosen to scale the
        # amounts there's no point in letting him/her edit the amounts (or add a new one). This would be quite
        # confusing, otherwise
        enabled = not self.amounts_scaled and self.editable
        self.optionalCheckbox.setEnabled(enabled)
        self.isGroupCheckBox.setEnabled(enabled)
        self.alternativeCheckBox.setEnabled(enabled)

        if not enabled:
            return

        # if they should be enabled, selectively disable them again
        alternative_enabled = False
        alternative_text = self._ingredient_treeview_model.alternative_or
        is_group_enabled = False

        rows = 0
        for index in self.ingredientTreeView.selectedIndexes():
            if index.column() == IngredientTreeViewModel.IngredientColumns.INGREDIENT:
                rows += 1

        if rows == 1:
            # Exactly one row has been selected

            index = self.ingredientTreeView.selectedIndexes()[0]
            depth = self._ingredient_treeview_model.depth(index)
            parent = index.parent()
            if depth in (IngredientTreeViewModel.IngredientLevels.ROOT,
                         IngredientTreeViewModel.IngredientLevels.INGREDIENT) and not parent.isValid():
                # Root level. It's the right level to add new groups
                is_group_enabled = True

            if depth in (IngredientTreeViewModel.IngredientLevels.INGREDIENT,
                         IngredientTreeViewModel.IngredientLevels.ALTERNATIVE):
                # Ingredient level (alternative = or) or alternative level (alternative = and). Possible to
                # Add an alternative ingredient
                alternative_enabled = True
            if depth in (IngredientTreeViewModel.IngredientLevels.ALTERNATIVE,
                         IngredientTreeViewModel.IngredientLevels.ALTERNATIVEGROUP):
                alternative_text = self._ingredient_treeview_model.alternative_and
            if depth == IngredientTreeViewModel.IngredientLevels.ALTERNATIVEGROUP:
                self.alternativeCheckBox.setChecked(True)
        elif rows == 0:
            # Neither ingredient nor groups have been added
            is_group_enabled = True

        # Groups must not be "optional" - makes no sense and they span the first column -  so there's mo optional
        # checkbox to click anyway
        is_group_enabled = is_group_enabled and not self.optionalCheckbox.isChecked()

        # When group is selected alternative doesn't make sense
        alternative_enabled = alternative_enabled and not self.isGroupCheckBox.isChecked()

        if not is_group_enabled:
            self.isGroupCheckBox.setChecked(False)

        self.isGroupCheckBox.setEnabled(is_group_enabled)
        self.alternativeCheckBox.setEnabled(alternative_enabled)
        self.alternativeCheckBox.setText(alternative_text)

        if self.isGroupCheckBox.isChecked():
            self.optionalCheckbox.setChecked(False)
            self.optionalCheckbox.setEnabled(False)
            self.alternativeCheckBox.setChecked(False)
        else:
            self.optionalCheckbox.setEnabled(True)

    def _update_delete_images(self):
        """
        Activate/deactivate the delete button and the delete action.

        Returns:

        """

        # Only when the recipe is editable (and at least one image has been selected)
        enabled = self.editable and len(self.imageTableView.selectedIndexes()) > 0
        self.actionDelete_Image_s.setEnabled(enabled)
        self.deleteImagesButton.setEnabled(enabled)

    def _update_ingredient_widgets(self):
        """
        Depending on the state (editable/not editable) and the selection, change the state of the buttons

        Returns:

        """

        # Delete Button/action
        delete_enabled = len(self.ingredientTreeView.selectedIndexes()) > 0 and self.editable
        self.deleteIngredientsButton.setEnabled(delete_enabled)
        self.actionDelete_Ingredients.setEnabled(delete_enabled)

        # New ingredient group
        enabled = not self.amounts_scaled and self.editable
        self.addNewIngredientButton.setEnabled(enabled)
        self.newIngredientAmountEditor.setEnabled(enabled)
        self.newIngredientLineEdit.setEnabled(enabled)
        self._update_add_ingredients_checkboxes()

    @property
    def amounts_scaled(self) -> bool:
        """
        Are the amounts scaled, i.e. the user chose to calculate the amounts to a different value of yields

        Returns: true, if scaled.

        """

        return not math.isclose(self._ingredient_treeview_model.factor, 1.0)

    @property
    def editable(self) -> bool:
        return self.__editable

    @editable.setter
    def editable(self, editable: bool):
        """
        Sets the widgets, top level items and so on editable (or not)

        Args:
            editable (): editable or not

        Returns:

        """

        self.__editable = editable

        self.actionEdit.setChecked(editable)
        self._enable_comboboxes(editable)
        self._enable_misc_elements(editable)
        self._enable_spinboxes(editable)
        self._switch_textedits(editable)
        self._switch_timeedits(editable)

        self.imageTableView.setDragEnabled(editable)
        self.imageTableView.setAcceptDrops(editable)
        self._image_table_model.editable = editable
        self._update_delete_images()

        self.ingredientTreeView.setDragEnabled(editable)
        self.ingredientTreeView.setAcceptDrops(editable)
        self._ingredient_treeview_model.editable = editable
        self._update_ingredient_widgets()

        self.recipeTitleLineEdit.setReadOnly(not editable)
        self.urlLineEdit.setReadOnly(not editable)

    @property
    def max_image_size(self) -> (int, int):
        """
        The maximum size of an image defined by the user

        Returns:
            (width, height)
        """

        settings = QtCore.QSettings()

        settings.beginGroup("preferences/images")
        max_width = settings.value("max_width", 320)
        max_height = settings.value("max_height", 200)

        return max_width, max_height

    @property
    def modified(self) -> bool:
        return self.isWindowModified()

    @modified.setter
    def modified(self, modified: bool):
        self.setWindowModified(modified)
        self.actionSave.setEnabled(modified)
        self.actionRevert.setEnabled(modified)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:

        # TODO: Ask
        if self.modified:
            # TODO: Ask!
            if self._transaction_started:
                self._session.rollback()
        if self.__new_recipe:
            # This is ugly.. first a new recipe and than delete it. This will make holes in the id, but OTOH it's
            # no real issue - it takes lots of recipes and adding/deleting them to reach  id's limit :-)
            self._session.delete(self._recipe)
            self._session.commit()
            self.recipeChanged.emit()
        self._save_ui_states()
        event.accept()

    def forced_close(self):
        """ Force the window to close without any saving or interaction """
        self.__force_closed = True
        self.close()

    def init_ui(self):

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # -------------------- Common signals for Author, Yields and Cuisine's ComboBoxes --------------------
        for combobox in (self.authorComboBox, self.cuisineComboBox, self.yieldsComboBox):
            combobox.currentIndexChanged[int].connect(
                lambda index, widget=combobox: self.recipe_comboboxes_currentIndexChanged(index, combobox=widget))
            combobox.currentTextChanged.connect(lambda text: self.set_modified())

        # -------------------- Actions --------------------
        for action, slot in ((self.actionAdd_Image_s, self.actionAdd_Image_s_triggered),
                             (self.actionDelete_Image_s, self.actionDelete_Image_s_triggered),
                             (self.actionDelete_Ingredients, self.actionDelete_Ingredients_triggered),
                             (self.actionEdit, self.actionEdit_toggled),
                             (self.actionNew_Category, self.actionNew_Category_triggered),
                             (self.actionRevert, self.actionRevert_triggered),
                             (self.actionSave, self.actionSave_triggered)):
            action.triggered.connect(slot)

        # -------------------- Author /Cuisine --------------------
        for model, combobox in (
                (self._author_combobox_model, self.authorComboBox),
                (self._cuisine_combobox_model, self.cuisineComboBox)):
            model.rowsAboutToBeInserted.connect(lambda parent, start, end: self.set_modified())
            combobox.setModel(model)
            combobox.setValidator(self._lstrip_validator)

        # --------------------- Calculate amount for ----------------------
        self.calculateAmountButton.clicked.connect(self.calculateAmountButton_clicked)
        self.calculateAmountDoubleSpinBox.valueChanged.connect(self.calculateAmountDoubleSpinBox_valueChanged)

        # -------------------- Category group  --------------------
        self.catgoriesButton.setMenu(self._category_button_menu)
        self._category_button_menu.setEnabled(True)

        # -------------------- Image group  --------------------
        max_width, max_height = self.max_image_size
        self.imageLabel.setMaximumSize(max_width, max_height)

        self.addImagesButton.clicked.connect(self.actionAdd_Image_s_triggered)
        self.deleteImagesButton.clicked.connect(self.actionDelete_Image_s_triggered)

        self._image_description_delegate.beginEditing.connect(self.set_modified)
        self._image_table_model.beginReordering.connect(self.set_modified)

        self.imageTableView.setModel(self._image_table_model)
        self.imageTableView.setItemDelegateForColumn(ImageTableModel.ImageTableColumns.DESCRIPTION,
                                                     self._image_description_delegate)
        self.imageTableView.doubleClicked.connect(self.imageTableView_doubleClicked)
        self.imageTableView.selectionModel().selectionChanged.connect(self.imageTableView_selectionChanged)
        self.imageTableView.addAction(self.actionAdd_Image_s)
        self.imageTableView.addAction(self.actionDelete_Image_s)
        self.imageTableView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # -------------------- Ingredient Group --------------------
        # TODO: Better context menu (set amount to...)
        # Ingredient Tree
        self._amount_delegate.illegalValue.connect(self.amountEditor_illegalValue)
        self._amount_delegate.set_combox_model(self._unit_combobox_model)

        treeview = self.ingredientTreeView
        treeviewmodel = self._ingredient_treeview_model

        self._ingredient_delegate.beginEditing.connect(self.set_modified)
        treeviewmodel.firstColumnSpanned.connect(self.ingredient_treeview_model_firstColumnSpanned)
        treeviewmodel.dataToBeChanged.connect(self.set_modified)

        treeview.setModel(treeviewmodel)
        treeview.setItemDelegateForColumn(treeviewmodel.IngredientColumns.AMOUNT, self._amount_delegate)
        treeview.setItemDelegateForColumn(treeviewmodel.IngredientColumns.INGREDIENT, self._ingredient_delegate)
        treeview.selectionModel().selectionChanged.connect(self.ingredientTreeView_selectionChanged)
        treeview.addAction(self.actionDelete_Ingredients)
        treeview.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # New ingredient group
        self.alternativeCheckBox.setText(self._ingredient_treeview_model.alternative_or)
        self.newIngredientAmountEditor.unitComboBox.setModel(self._unit_combobox_model)
        self.newIngredientLineEdit.setValidator(self._lstrip_validator)
        self.newIngredientLineEdit.setCompleter(self._ingredient_completer)
        for checkbox in (self.isGroupCheckBox, self.optionalCheckbox, self.alternativeCheckBox):
            checkbox.clicked.connect(self.addNewIngredientCheckboxes_clicked)

        # Add and Delete buttons
        self.actionDelete_Ingredients.triggered.connect(self.actionDelete_Ingredients_triggered)
        self.addNewIngredientButton.clicked.connect(self.addNewIngredientButton_clicked)
        self.deleteIngredientsButton.clicked.connect(self.actionDelete_Ingredients_triggered)

        # -------------------- Last Cooked group --------------------
        self.lastCookedDateEdit.dateChanged.connect(self.lastCookedDateEdit_dateChanged)
        self.neverCookedCheckBox.clicked.connect(self.neverCookedCheckBox_clicked)

        # -------------------- Rating group  --------------------
        self.ratingSpinBox.valueChanged.connect(self.ratingSpinBox_valueChanged)

        # -------------------- TextEdits (second tab) --------------------
        for the_text_edit in self._text_edits:
            the_text_edit.textChanged.connect(self.set_modified)

        # -------------------- Title --------------------
        self.recipeTitleLineEdit.setValidator(self._lstrip_validator)
        self.recipeTitleLineEdit.textEdited.connect(lambda text: self.set_modified())

        # -------------------- Time widgets --------------------
        for time_widget in (self.preparationTimeEditor, self.cookingTimeEditor, self.totalTimeEditor):
            time_widget.valueChanged.connect(lambda value: self.set_modified())

        # -------------------- URL group --------------------
        self.urlButton.clicked.connect(self.urlButton_clicked)
        self.urlLineEdit.setValidator(self._lstrip_validator)
        self.urlLineEdit.textEdited.connect(self.urlLineEdit_textEdited)

        # -------------------- Yields group  --------------------
        self._yield_combobox_model.rowsAboutToBeInserted.connect(lambda parent, start, end: self.set_modified())
        self.yieldsComboBox.setModel(self._yield_combobox_model)
        self.yieldsComboBox.setValidator(self._lstrip_validator)

        self.yieldsDoubleSpinBox.valueChanged.connect(self.yieldsDoubleSpinBox_valueChanged)
        self._load_ui_states()

    def load_data(self):
        """
        Loads the recipe's data (either initially or after a revert)

        Returns:

        """
        # Widgets that emit a unwanted signal when the value is set by the program (and not by the user)
        blocked_widgets = (self.ratingSpinBox, self.lastCookedDateEdit, self.yieldsComboBox, self.authorComboBox,
                           self.cuisineComboBox, self.yieldsDoubleSpinBox, self.calculateAmountDoubleSpinBox,
                           self.preparationTimeEditor, self.cookingTimeEditor, self.totalTimeEditor) + self._text_edits

        for widget in blocked_widgets:
            widget.blockSignals(True)

        self._unit_combobox_model.reload_model()

        # -------------------- Author, Cuisine,   --------------------
        for model, item, combobox in ((self._author_combobox_model, self._recipe.author, self.authorComboBox),
                                      (self._cuisine_combobox_model, self._recipe.cuisine, self.cuisineComboBox)):

            model.reload_model()
            index = -1
            if item:
                index = model.index_of_item(item)
                if index is None:
                    index = -1
            combobox.setCurrentIndex(index)

        # -------------------- Categories --------------------
        self._set_category_button_menu()
        self._set_category_line_edit()

        # -------------------- Cooking times --------------------
        self._set_cooking_timeeditors()

        # -------------------- Image group --------------------
        self._load_image_group()
        self._set_windowicon()
        self._restore_image_columns()

        # -------------------- Ingredients --------------------
        self._clear_new_ingredient()
        self._ingredient_treeview_model.load_model()

        # This has to be done each time the TreeViewModel reloads - it's not enough to do it once in init_ui()
        self._restore_ingredient_columns()
        self.ingredientTreeView.expandAll()

        # -------------------- Last cooked ---------------------
        self.lastCookedDateEdit.setDisplayFormat(QtCore.QLocale.system().dateFormat(QtCore.QLocale.ShortFormat))
        if self._recipe.last_cooked:
            self.lastCookedDateEdit.setDate(self._recipe.last_cooked)
            self.neverCookedCheckBox.setChecked(False)
        else:
            self.lastCookedDateEdit.setDate(datetime.now())
            self.neverCookedCheckBox.setChecked(True)

        # -------------------- Rating --------------------
        if self._recipe.rating:
            self.ratingSpinBox.setValue(self._recipe.rating)
        else:
            self.ratingSpinBox.setValue(-1)

        # -------------------- TextEdits (second tab) --------------------
        self.descriptionPlainTextEdit.setPlainText(self._recipe.description)
        self.instructionsPlainTextEdit.setPlainText(self._recipe.instructions)
        self.notesPlainTextEdit.setPlainText(self._recipe.notes)

        # -------------------- Title --------------------
        self._set_recipe_title()

        # -------------------- URL --------------------
        if self._recipe.url:
            self.urlLineEdit.setText(self._recipe.url)
            self.urlLineEdit.setCursorPosition(0)
            self.urlButton.setEnabled(True)
        else:
            self.urlLineEdit.setText(None)
            self.urlButton.setEnabled(False)

        # -------------------- Yields / Calculate Amount ---------------------
        self._yield_combobox_model.reload_model()
        self.convertYieldsCheckBox.setChecked(False)

        if not math.isclose(self._recipe.yields, 0.0):
            self.yieldsDoubleSpinBox.setValue(self._recipe.yields)
            self.calculateAmountDoubleSpinBox.setValue(self._recipe.yields)
            self.calculateAmountDoubleSpinBox.setEnabled(True)

            index = self._yield_combobox_model.index_of_item(self._recipe.yield_unit_name)
            if index is None:
                # Should not happen
                index = -1
            self.yieldsComboBox.setCurrentIndex(index)
            if self._recipe.yield_unit_name:
                self.calculateAmountDoubleSpinBox.setSuffix(" " + str(self._recipe.yield_unit_name))
        else:
            # Yields == 0.0. No point in calculating an amount for >0.0
            self.yieldsDoubleSpinBox.setValue(0.0)
            self.yieldsComboBox.setCurrentIndex(-1)
            self.calculateAmountDoubleSpinBox.setValue(0.0)
            self.calculateAmountDoubleSpinBox.setEnabled(False)

        for widget in blocked_widgets:
            widget.blockSignals(False)

    def revert_data(self):
        """
        Reverts the recipe to the data stored in the database

        Returns:

        """

        if self._transaction_started:
            self._session.rollback()
        self.modified = False
        self._transaction_started = False
        self._session.refresh(self._recipe)

        # The user might have added some units which are no longer available after the rollback
        data.IngredientUnit.update_unit_dict(self._session)
        self._ingredient_completer.reload_model()
        self.load_data()
        if not self.editable:
            self._load_markdown_textedits()

    def save_data(self):
        """
        Save the (modified) data into the current session

        Returns:

        """

        if not self._transaction_started:
            raise ValueError("No transaction started")
        self._recipe.last_modified = datetime.now()

        # The user might have entered something in the three ComboBoxes without pressing enter
        for combobox in (self.authorComboBox, self.cuisineComboBox, self.yieldsComboBox):
            comboboxtext = nullify(combobox.currentText())
            if combobox.findText(comboboxtext) == -1:
                # The text isn't in combobox's model. And addItem automatically will create a new db item
                combobox.addItem(comboboxtext)
                # This will cause a signal which in turn will set the recipe's value
                combobox.setCurrentIndex(combobox.findText(comboboxtext))

        self._recipe.preparation_time = zero_to_none(self.preparationTimeEditor.value)
        self._recipe.cooking_time = zero_to_none(self.cookingTimeEditor.value)
        self._recipe.total_time = zero_to_none(self.totalTimeEditor.value)

        if self.recipeTitleLineEdit.isModified():
            self._recipe.title = self.recipeTitleLineEdit.text()
            self._set_recipe_title()
        if self.urlLineEdit.isModified():
            self._recipe.url = self.urlLineEdit.text()
        if self.descriptionPlainTextEdit.document().isModified():
            self._recipe.description = self.descriptionPlainTextEdit.toPlainText()
        if self.instructionsPlainTextEdit.document().isModified():
            self._recipe.instructions = self.instructionsPlainTextEdit.toPlainText()
        if self.notesPlainTextEdit.document().isModified():
            self._recipe.notes = self.notesPlainTextEdit.toPlainText()
        self._ingredient_treeview_model.save_tree(self._session)
        self._image_table_model.reorder_imagelist()
        self._set_windowicon()
        self._session.commit()

        # When saved the new recipe will lose its "new recipe" state
        self.__new_recipe = False
        self.modified = False
        self._transaction_started = False
        self.recipeChanged.emit(self._recipe)

    @_Decorators.change
    def set_image(self, image: Qt.QImage):
        """
        Scales and sets the image (thumbnail, image)

        Args:
            image (): The image

        Returns:

        """

        max_width, max_height = self.max_image_size

        settings = QtCore.QSettings()
        settings.beginGroup("preferences/images")
        thumb_height = settings.value("thumb_height", 40)
        jpeg_quality = settings.value("jpeg_quality", 80)
        settings.endGroup()

        # 1. Scale the images
        scaled_image = image.scaled(max_width, max_height, QtCore.Qt.KeepAspectRatio)
        scaled_thumb = image.scaledToHeight(thumb_height)

        # 2. Export the images to jpeg byte format
        image_buffer = QtCore.QBuffer()
        image_buffer.open(QtCore.QIODevice.ReadWrite)
        scaled_image.save(image_buffer, "JPG", jpeg_quality)

        image = image_buffer.data()

        # Unfortunately the buffer cannot be reused, therefore it has to be recreated
        image_buffer.close()

        # Same procedure for the thumbnail
        image_buffer = QtCore.QBuffer()
        image_buffer.open(QtCore.QIODevice.ReadWrite)
        scaled_thumb.save(image_buffer, "JPG", jpeg_quality)
        thumbnail = image_buffer.data()
        image_buffer.close()

        # 3. Save the images
        position = 0

        if len(self._recipe.imagelist) > 0:
            last_position = self._recipe.imagelist[len(self._recipe.imagelist) - 1].position
            position = last_position + 1

        new_image = data.RecipeImage(recipe=self._recipe, position=position, image=image, thumbnail=thumbnail)
        self._recipe.imagelist.append(new_image)
        new_row = self._image_table_model.setup_row(new_image)
        new_row[self._image_table_model.ImageTableColumns.IMAGE].setData(position, QtCore.Qt.UserRole)
        self._image_table_model.appendRow(new_row)

    @_Decorators.change
    def set_modified(self):
        """ Nothing to do here, the decorator does it work """
        pass

    def actionAdd_Image_s_triggered(self, enabled: bool = False):
        """ Open a file requester, add the images """

        _translate = self._translate
        # TODO: settings / last directory

        options = Qt.QFileDialog.Options()

        filenames, filter_ = Qt.QFileDialog.getOpenFileNames(self, _translate("RecipeWindow", "Select new Image"),
                                                             filter=misc.image_filter, options=options)
        if filenames:
            # Workaround similar to ingredient tree: When the first image has been added to the image list
            # The image table will behave oddly - 2 more columns and so on. This is a workaround
            was_empty = self._image_table_model.rowCount() == 0
            for the_filename in filenames:
                image_reader = Qt.QImageReader(the_filename)
                image = image_reader.read()
                if image.isNull():
                    Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Error loading file"),
                                            _translate("RecipeWindow", "Unable to read {}: {}")
                                            .format(the_filename, image_reader.errorString()))
                else:
                    # modified will be handled by the method below
                    self.set_image(image)
            if was_empty:
                self._restore_image_columns()

    @_Decorators.change
    def actionCategory_triggered(self, category: data.Category, enabled: bool):
        """
        Add - or remove - a category from recipe's category list

        Args:
            category (): The category
            enabled (): the checkbox - enabled = add, disabled = remove

        Returns:

        """

        if enabled:
            self._recipe.categories.append(category)
        else:
            self._recipe.categories.remove(category)
        self._set_category_line_edit()

    @_Decorators.change
    def actionDelete_Image_s_triggered(self, checked: bool = False):
        """
        Deletes the selected iamges

        Args:
            checked (): Not used

        Returns:

        """
        for the_index in self.imageTableView.selectedIndexes():
            if the_index.column() == ImageTableModel.ImageTableColumns.IMAGE:
                row = the_index.row()

                # Find the correct images. Since each remove changes the list it's not possible to use the index
                # operator
                the_image = None
                for image in self._recipe.imagelist:
                    if image.position == row:
                        the_image = image
                        break
                if the_image:
                    self._recipe.imagelist.remove(the_image)

        # Free the deleted positions
        self._session.merge(self._recipe)

        # Renumber the remaining images
        position = 0
        for image in self._recipe.imagelist:
            image.position = position
            self._session.merge(self._recipe)
            position += 1
        self._load_image_group()

    @_Decorators.change
    def actionDelete_Ingredients_triggered(self, checked: bool = False):
        """
        Delete the selected ingredient(s)

        Args:
            checked (): Ignored

        Returns:

        """

        if self.editable:
            treeviewmodel = self._ingredient_treeview_model
            ids_for_deletion = []
            for index in self.ingredientTreeView.selectedIndexes():
                if index.column() == treeviewmodel.IngredientColumns.INGREDIENT:
                    ingredient_list_index = index.siblingAtColumn(treeviewmodel.IngredientColumns.INGREDIENTLISTROW)
                    ids_for_deletion.append(int(ingredient_list_index.data(QtCore.Qt.DisplayRole)))
            if len(ids_for_deletion) > 0:
                treeviewmodel.delete_ids(self._session, ids_for_deletion)

    def actionEdit_toggled(self, enabled: bool):
        self.editable = enabled

    def actionNew_Category_triggered(self, checked: bool = False):
        """
        Add a new category

        Args:
            checked (): not used

        Returns:

        """
        _translate = self._translate
        new_category_name, ok = Qt.QInputDialog.getText(self, _translate("RecipeWindow", "Add New Category"),
                                                        _translate("RecipeWindow", "New Category"))
        if ok:
            self.set_modified()
            new_category_name = nullify(new_category_name)
            if new_category_name:
                new_category = data.Category.get_or_add_category(self._session, new_category_name)
                # The user might have entered an existing category
                if new_category not in self._recipe.categories:
                    self._recipe.categories.append(new_category)
                    self._set_category_button_menu()
                    self._set_category_line_edit()

    def actionRevert_triggered(self, checked: bool = False):
        self.revert_data()

    def actionSave_triggered(self, checked: bool = False):
        self.save_data()

    def addNewIngredientButton_clicked(self, checked: bool = False):
        """
        Add a new ingredient

        Args:
            checked (): ignored

        Returns:

        """

        _translate = self._translate
        treeviewmodel = self._ingredient_treeview_model
        newingredient_name = nullify(self.newIngredientLineEdit.text())

        if newingredient_name is None:
            Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Empty Ingredient"),
                                    _translate("RecipeWindow", "Please enter a value for ingredient"))
            return

        # A group or an ingredient has to be handled differently
        if self.isGroupCheckBox.isChecked():
            # A new group
            new_group_position = data.IngredientListEntry.get_position_for_new_group(self._session, self._recipe)

            # Should never happen in - more than 99 groups are highly unlikely
            if new_group_position < 0:
                Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Maximum Groups reachet"),
                                        _translate("RecipeWindow",
                                                   "You've reached the maximum of groups on this level"))
                return

            self.set_modified()

            # The user might have changed the tree - reordering ingredients and so on, so the model and the db
            # might be out of sync
            treeviewmodel.save_tree(self._session)

            new_group_ingredient = data.Ingredient.get_or_add_ingredient(session_=self._session,
                                                                         name=newingredient_name, is_group=True)
            new_group_entry = data.IngredientListEntry(recipe=self._recipe, unit=data.IngredientUnit.unit_group,
                                                       ingredient=new_group_ingredient, position=new_group_position,
                                                       name=None)
            self._session.add(new_group_entry)
            self._session.merge(new_group_entry)
            model_was_empty = treeviewmodel.rowCount() == 0
            treeviewmodel.add_new_group(new_group_entry)

            # The very first append to a model will unhide all columns. This is a workaround to counter it.
            if model_was_empty:
                self._restore_ingredient_columns()
        else:
            # A real ingredient
            newingredient_unit = self.newIngredientAmountEditor.unit()
            (newingredient_amount, newingredient_rangeamount), amount_ok = self.newIngredientAmountEditor.amount()
            newingredient_optional = self.optionalCheckbox.isChecked()

            if not amount_ok:
                Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Illegal amount"),
                                        _translate("RecipeWindow", "Unable to recognize value for amount: {}").format(
                                            self.newIngredientAmountEditor.amountLineEdit.text()))
                return

            # Try to find the "generic" ingredient for the ingredient. Assumption:
            # In "Tomatoes, red, chopped" the generic ingredient "Tomatoes". Of course, this is not reliable - for
            # example the user might enter "Red tomatoes, chopped". In that case "tomatoes" probably would be right,
            # but consider: "Green pepper" vs "Red pepper". Same kind of ingredient, but taste and nutrition value
            # are different. Therefore it's best to use such a crude assumption and let the user sort it out later -
            # there just isn't a foolproof way (especially if you consider different languages) to do it.
            generic_ingredient_name = newingredient_name.split(",", 1)[0]

            self.set_modified()

            # The user might have changed the tree - reordering ingredients and so on, so the model and the db
            # might be out of sync
            treeviewmodel.save_tree(self._session)

            rows = 0
            item_position = None
            parent_item = None
            parent_position = None

            # Find out which parent the new ingredient to attach

            # There can be only one selection - when multiple items are selected it's not clear where to append the
            # new ingredient. At the the item closest to the bottom? Or the last selected one?
            for the_index in self.ingredientTreeView.selectedIndexes():
                # Only count the position items for the rows
                if the_index.column() == treeviewmodel.IngredientColumns.INGREDIENT:
                    rows += 1
                    item_position = int(the_index.data(QtCore.Qt.UserRole))

            if rows != 1:
                # Too much selection -> append at root level
                parent_position = None
                parent_item = None
            else:
                position_item = treeviewmodel.findItems(str(item_position), QtCore.Qt.MatchRecursive,
                                                        treeviewmodel.IngredientColumns.POSITION)[0]
                ingredient_index = position_item.index().sibling(position_item.row(),
                                                                 treeviewmodel.IngredientColumns.INGREDIENT)
                ingredient_item = treeviewmodel.itemFromIndex(ingredient_index)

                # Depending on the state of checkbox, either append it on the item (or/and) or to it's parent
                # When the checkbox is checked AND disabled: the last level (and) has been reached. It's not possible
                # To use the item as a parent
                if self.alternativeCheckBox.isChecked() and self.alternativeCheckBox.isEnabled():
                    parent_item = ingredient_item
                    parent_position = item_position
                else:
                    # Either deselected or at the last level. In either cases the parent will be the item's parent
                    parent_item = ingredient_item.parent()

                    if parent_item is None:
                        # ingredient_item is a root-level item

                        # Group?
                        if data.IngredientListEntry.is_group(item_position):
                            parent_position = item_position
                            parent_item = ingredient_item
                        else:
                            # No, a root-level item.
                            parent_position = None
                    else:
                        parent_position = int(parent_item.data(QtCore.Qt.UserRole))

            position = data.IngredientListEntry.get_position_for_ingredient(self._session, self._recipe,
                                                                            parent_position)

            # Should never happen in normal circumstances - more than 99 ingredients on a level is highly unlikely
            if position < 0:
                Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Maximum ingredients"),
                                        _translate("RecipeWindow",
                                                   "You've reached the maximum of ingredients on this level"))

            generic_ingredient = data.Ingredient.get_or_add_ingredient(self._session, name=generic_ingredient_name)
            new_entry = data.IngredientListEntry(recipe=self._recipe, unit=newingredient_unit,
                                                 ingredient=generic_ingredient, position=position,
                                                 amount=newingredient_amount, range_amount=newingredient_rangeamount,
                                                 name=newingredient_name, optional=newingredient_optional)
            self._session.add(new_entry)
            self._session.merge(new_entry)
            new_row = treeviewmodel.setup_row(new_entry)

            if parent_item is None:
                model_was_empty = treeviewmodel.rowCount() == 0
                treeviewmodel.appendRow(new_row)

                # The very first append to a model will unhide all columns. This is a workaround to counter it.
                if model_was_empty:
                    self._restore_ingredient_columns()
            else:
                parent_item.appendRow(new_row)

        self._session.merge(self._recipe)
        self._session.refresh(self._recipe)
        treeviewmodel.set_ingredient_list_row()

        self._clear_new_ingredient()
        self.newIngredientAmountEditor.amountLineEdit.setFocus()

    def addNewIngredientCheckboxes_clicked(self, checked: bool):
        """
        Depending on the state of the three "Add new ingredient" checkboxes enabled/disable/unchecked the other
        ones.

        Args:
            checked ():

        Returns:

        """
        self._update_add_ingredients_checkboxes()

    def amountEditor_illegalValue(self, text: str):
        """
        The user has entered a incorrect value into the amount LineEdit

        Args:
            text (): The illegal test

        Returns:

        """
        _translate = self._translate
        Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Illegal Value"),
                                _translate("RecipeWindow", "Illegal value for amount: {}")
                                .format(text))

    def calculateAmountButton_clicked(self, checked: bool):
        """
        Resets the calculated amounts the recipes yield

        Args:
            checked ():

        Returns:

        """
        if not checked:
            # This is the only possible action
            self.calculateAmountDoubleSpinBox.setValue(self.yieldsDoubleSpinBox.value())

    def calculateAmountDoubleSpinBox_valueChanged(self, value: float):
        """
        The calculate amount spinbox has been changed

        Args:
            value ():

        Returns:

        """
        yields = self.yieldsDoubleSpinBox.value()
        if yields == 0 or value == 0:
            return
        else:
            factor = value / yields
            factor_one = math.isclose(factor, 1.0)
            self.calculateAmountButton.setChecked(not factor_one)
            self.calculateAmountButton.setEnabled(not factor_one)
            self._ingredient_treeview_model.scale_amounts(factor)
            self._update_ingredient_widgets()

    def imageTableView_doubleClicked(self, index: QtCore.QModelIndex):
        """
        User has double clicked on an image

        Args:
            index ():

        Returns:

        """

        # On double click display the image in full size. Therefore only the image column is relevant
        if index.column() == ImageTableModel.ImageTableColumns.IMAGE:
            imagelist_row = int(index.data(QtCore.Qt.UserRole))
            the_image = self._recipe.imagelist[imagelist_row]
            self._set_image_label(the_image.image)
            self.imageLabel.setStatusTip(the_image.description)

    def imageTableView_selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        """
        Enabled/disable the delete button/action
        Args:
            selected (): Ignored
            deselected (): Ignored

        Returns:

        """
        self._update_delete_images()

    def ingredient_treeview_model_firstColumnSpanned(self, row: int, parent: QtCore.QModelIndex):
        """
        The row should be spanned across all columns

        Args:
            row (): The row
            parent (): The parent

        Returns:

        """
        # The model has detected a group. Since the model cannot set the flag itself it sends a signal
        # to the controller
        self.ingredientTreeView.setFirstColumnSpanned(row, parent, True)

    def ingredientTreeView_itemDoubleClicked(self, item: QtWidgets.QTreeWidgetItem, column: int):
        """
        The user has double clicked on ingredient

        Args:
            item (): The item
            column (): The column

        Returns:

        """
        # Selectively make the items editable (or not)
        if self.editable and column != IngredientTreeViewModel.IngredientColumns.ALTERNATIVE:
            flags = item.flags()
            flags |= QtCore.Qt.ItemIsEditable
            item.setFlags(flags)

    def ingredientTreeView_selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        self._update_ingredient_widgets()

    @_Decorators.change
    def lastCookedDateEdit_dateChanged(self, date: QtCore.QDate):
        """
        "Last Cooked" changed

        Args:
            date ():

        Returns:

        """
        self._recipe.last_cooked = self.lastCookedDateEdit.date().toPyDate()

    @_Decorators.change
    def neverCookedCheckBox_clicked(self, checked: bool):
        """
        "Never cooked" selected (or not)

        Args:
            checked ():

        Returns:

        """
        if checked:
            self.lastCookedDateEdit.setEnabled(False)
            self._recipe.last_cooked = None
        else:
            self.lastCookedDateEdit.setEnabled(True)
            self._recipe.last_cooked = self.lastCookedDateEdit.date().toPyDate()

    @_Decorators.change
    def ratingSpinBox_valueChanged(self, value: int):
        """
        Updates the recipe's rating

        Args:
            value ():

        Returns:

        """

        # Special value (unrated)
        if value == -1:
            self._recipe.rating = None
        else:
            self._recipe.rating = value

    @_Decorators.change
    def recipe_comboboxes_currentIndexChanged(self, index: int, combobox: QtWidgets.QComboBox):
        """
        One of the recipe's ComboBoxes (Yield unit, Author, Cuisine) has been changed

        Args:
            index ():
            combobox ():

        Returns:

        """

        # To prevent the combobox from displaying "- None -" (or something similar), this is
        # a hack: whenever the "none" index has been selected, the selection will change to the
        # "unselected" value of the combobox
        if index == DBComboBoxModel.none_index:
            # Prevent from emitting the signal - there's no need
            combobox.blockSignals(True)
            combobox.setCurrentIndex(-1)
            combobox.blockSignals(False)

        item = combobox.model().item_at(index)

        # When the yield's ComboBox changed the calculate's ComboBox prefix should change, too
        if combobox == self.yieldsComboBox:
            self._recipe.yield_unit_name = item
            if item:
                self.calculateAmountDoubleSpinBox.setSuffix(" " + str(item))
        elif combobox == self.authorComboBox:
            self._recipe.author = item
        elif combobox == self.cuisineComboBox:
            self._recipe.cuisine = item
        else:
            raise (ValueError("Unknown combobox"))

    @_Decorators.change
    def timeLineEdit_returnPressed(self, time_line_edit: QtWidgets.QLineEdit):
        """
        The text of a time's value LineEdit  has been changed

        Args:
            time_line_edit ():

        Returns:

        """

        time_value = 0
        days, hours, minutes = time_line_edit.text().split(":")

        # Deliberately no check if the user enters something like 90 hours 80 minutes.
        if nullify(days):
            time_value += int(days) * 24 * 60
        if nullify(hours):
            time_value += int(hours) * 60
        if nullify(minutes):
            time_value += int(minutes)

        # Timedelta is in seconds
        time_value *= 60

        # The user has (unset) the specific time value
        if time_value == 0:
            time_value = None

        if time_line_edit == self.preparationTimeLineEdit:
            self._recipe.preparation_time = time_value
        elif time_line_edit == self.cookingTimeLineEdit:
            self._recipe.cooking_time = time_value
        elif time_line_edit == self.totalTimeLineEdit:
            self._recipe.total_time = time_value

    def urlButton_clicked(self):
        """
        Opens the URL in the url LineEdit externally

        Returns:

        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.urlLineEdit.text()))

    @_Decorators.change
    def urlLineEdit_textEdited(self, text):
        self.urlButton.setEnabled(nullify(text) is not None)

    @_Decorators.change
    def yieldsDoubleSpinBox_valueChanged(self, value: float):
        """
        The value of yields' double spinbox has been changed

        Args:
            value (): The changed value

        Returns:
        """

        if math.isclose(value, 0.0):
            self.convertYieldsCheckBox.setChecked(False)
            self.convertYieldsCheckBox.setEnabled(False)
            self.calculateAmountDoubleSpinBox.setEnabled(False)
        else:
            self.convertYieldsCheckBox.setEnabled(True)
            self.calculateAmountDoubleSpinBox.setEnabled(True)

            # Let's see if the ingredients should be scaled
            if self.convertYieldsCheckBox.isChecked():
                # Yes
                factor = value / self._recipe.yields

                for ingredient in self._recipe.ingredientlist:
                    if ingredient.amount:
                        ingredient.amount *= factor
                        if ingredient.range_amount:
                            ingredient.range_amount *= factor

            self._recipe.yields = value
            self.calculateAmountDoubleSpinBox.setValue(value)
