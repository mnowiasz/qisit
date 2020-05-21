""" The recipe's list controller"""

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
from qisit.importer import gourmetdb
from qisit.qt.aboutdialog.aboutdialog_controller import AboutdialogController
from qisit.qt.dataeditor.data_editor_controller import DataEditorController
from qisit.qt.recipelistwindow.recipe_table_model import RecipeTableModel
from qisit.qt.recipelistwindow.ui import recipe_list
from qisit.qt.recipewindow import recipe_window_controller
from .gourmet_import import QTImportGourmet


# TODO: Cleanup (massive)
class RecipeListWindow(recipe_list.Ui_RecipeListWindow, QtWidgets.QMainWindow):
    """ The controller for the recipe list window """

    # Values in the recipe per page combobox
    __COMBOVALUES = (10, 15, 20, 25, 50, 75, 100, 150, 200)

    def __init__(self, session_: orm.Session):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()

        self._settings = QtCore.QSettings()
        self._filter_set = set()
        self._session = session_
        self._about_dialog_controller = None

        self._translate = translate
        recipes_per_page = int(self._settings.value("RecipeListWindow/RecipeTableView/main/recipes_per_page", 15))
        self.table_model = RecipeTableModel(session_, recipes_per_page=recipes_per_page)
        self.setupUi(self)

        self._data_editor = None
        self._filter_menus = {}
        self._recipe_windows = {}

        # Setup filter menus
        _translate = self._translate
        self.menuFilter.clear()

        for menu_entry, filter_table in ((_translate("RecipeWindow", "Author"), data.Author),
                                         (_translate("RecipeWindow", "Category"), data.Category),
                                         (_translate("RecipeWindow", "Cuisine"), data.Cuisine)):
            self._filter_menus[filter_table] = QtWidgets.QMenu(title=menu_entry)
            self._filter_menus[filter_table].setEnabled(True)
            self.menuFilter.addMenu(self._filter_menus[filter_table])

        self._action_filters = {
            data.Category: self.actionfilterCategories,
            data.Cuisine: self.actionfilterCuisine,
            data.Author: self.actionfilterAuthor
        }

        # To prevent the filter from being applied again and again when the user types spaces (or something similar)
        self._current_search_text = None

        _translate = self._translate

        self._setup_combo_list()
        self._update_page_buttons()
        self._update_page_slider()

        self.init_ui()

    def _load_ui_states(self):
        """
        Restores the states of the widgets (splitters, views...)

        Returns:

        """

        self._settings.beginGroup("RecipeListWindow/window")
        if self._settings.contains("geometry"):
            self.restoreGeometry(self._settings.value("geometry"))
        if self._settings.contains("state"):
            self.restoreState(self._settings.value("state"))
        self._settings.endGroup()

        self._settings.beginGroup("RecipeListWindow/RecipeTableView")
        if self._settings.contains("main/geometry"):
            self.recipeTableView.restoreGeometry(self._settings.value("main/geometry"))

        if self._settings.contains("header/state"):
            self.recipeTableView.horizontalHeader().restoreState(self._settings.value("header/state"))
        if self._settings.contains("header/geometry"):
            self.recipeTableView.horizontalHeader().restoreGeometry(self._settings.value("header/geometry"))
        self._settings.endGroup()

    def _recipe_window_closed(self, id_: int):
        """ Called when a recipe window has been closed """

        controller = self._recipe_windows.pop(id_)
        del controller

    def _reload_model(self):
        """
        Update the model (after filters or sorting order have changed) and change/update/enable/disable the UI
        elements  accordingly

        Returns:

        """
        self.table_model.update_model()
        self._update_page_slider()
        self._update_page_buttons()

    def _save_ui_states(self):
        """
        Saves the state of the widgets (splitters, views...)

        Returns:

        """
        settings = QtCore.QSettings()

        settings.beginGroup("RecipeListWindow/window")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        settings.endGroup()

        settings.beginGroup("RecipeListWindow/RecipeTableView")
        settings.setValue("main/geometry", self.recipeTableView.saveGeometry())
        settings.setValue("main/recipes_per_page", str(self.table_model.recipes_per_page))
        settings.setValue("header/state", self.recipeTableView.horizontalHeader().saveState())
        settings.setValue("header/geometry", self.recipeTableView.horizontalHeader().saveGeometry())
        settings.endGroup()

    def _setup_columns_menu(self):
        """
        The columns menu where use can choose which columns to display
        Returns:

        """
        _translate = self._translate
        columns_menu = QtWidgets.QMenu(title=_translate("RecipeWindow", "Columns"), parent=self.menuShow)
        for column in self.table_model.RecipeColumns:
            if column == self.table_model.RecipeColumns.ID:
                # The hidden ID column is always hidden and shouldn't be displayed in a menu
                continue

            column_action = QtWidgets.QAction(columns_menu)
            column_action.setText(self.table_model.column_headers[column][0])
            column_action.setCheckable(True)
            column_action.setEnabled(True)

            # After restoration of the GUI elements some columns might be hidden
            if not self.recipeTableView.isColumnHidden(column):
                column_action.setChecked(True)
            column_action.toggled.connect(
                lambda checked, my_column=column: self.actionColumn_triggered(my_column, checked))
            columns_menu.addAction(column_action)

        columns_menu.setEnabled(True)
        self.menuShow.addMenu(columns_menu)

    def _setup_combo_list(self):
        """
        Setup/update the recipes per page-Combobox

        Returns:

        """
        for value in self.__COMBOVALUES:
            self.recipesPerPagecomboBox.addItem(str(value), value)

        # Set the combo box to the last saved state
        index = self.recipesPerPagecomboBox.findData(self.table_model.recipes_per_page)
        self.recipesPerPagecomboBox.setCurrentIndex(index)

    def _update_filter_menu(self, table: db.Base, parent_action: QtWidgets.QAction):
        """
        Setup / update filter menu for the given table. Assumes that the table has got a property called name and a
        list called recipes. Called at startup and whenever a recipe changes (or after an import)

        Args:
            table (): The database table
            parent_action ():  the parent action

        Returns:

        """
        items = self._session.query(table).order_by(func.lower(table.name)).all()

        if len(items) == 0:
            # Empty database
            parent_action.setEnabled(False)
        else:
            parent_action.setEnabled(True)
            self._filter_menus[table].clear()
            for item in items:
                filter_action = QtWidgets.QAction(parent_action)
                filter_action.setText(f"{item.name} ({len(item.recipes)})")
                filter_action.setCheckable(True)

                # Note: After an item has been deleted but it's id is still in the model's filter it will  remain
                # there after the update. This is no problem, the SQL statement ("IN (...)") will still work.
                # Granted, it's a bit sloppy, but too much hassle finding out which items has been deleted and
                # removing them from the filters.
                filter_action.setChecked(item.id in self.table_model.filters[table])
                filter_action.triggered.connect(
                    lambda checked, my_table=table, my_id=item.id: self.actionFilterMenu_triggered(my_table, my_id,
                                                                                                   checked))
                self._filter_menus[table].addAction(filter_action)

    def _update_page_buttons(self):
        """
        Enable/disable page buttons (first, last, next..)

        Returns:

        """

        is_firstpage = self.table_model.offset == 0
        is_lastpage = self.table_model.offset >= (
                self.table_model.number_of_filtered_recipes - self.table_model.recipes_per_page)

        # First page?
        self.firstPageButton.setEnabled(not is_firstpage)
        self.previousPageButton.setEnabled(not is_firstpage)

        # last page?
        self.lastPageButton.setEnabled(not is_lastpage)
        self.nextPageButton.setEnabled(not is_lastpage)

    def _update_page_slider(self):
        """
        Update the slider after the model has been changed

        Returns:

        """
        number_of_filtered_recipes = self.table_model.number_of_filtered_recipes
        recipes_per_page = self.table_model.recipes_per_page

        maximum = number_of_filtered_recipes - recipes_per_page
        if maximum < 0:
            maximum = 0

        if recipes_per_page > number_of_filtered_recipes:
            # The recipes_per_page exceed the number of filtered recipes, i.e. there are no more pages
            self.recipesSlider.setEnabled(False)
        else:
            self.recipesSlider.setMaximum(maximum)
            self.recipesSlider.setPageStep(recipes_per_page)
            self.recipesSlider.setTickInterval(recipes_per_page)
            self.recipesSlider.setSingleStep(recipes_per_page)
            self.recipesSlider.setEnabled(True)
            self.recipesSlider.setMinimum(0)
            self.recipesSlider.setValue(self.table_model.offset)

    @property
    def modified(self) -> bool:
        return self.isWindowModified()

    @modified.setter
    def modified(self, modified: bool):
        self.setWindowModified(modified)
        self.actionSave.setEnabled(modified)
        self.actionRevert.setEnabled(modified)

    def init_ui(self):
        _translate = self._translate

        self.setWindowTitle(f"{self.windowTitle()} [*]")

        # -------------------- Actions --------------------
        self.actionAbout.triggered.connect(self.actionAbout_triggered)
        self.actionData_editor.triggered.connect(self.actionData_editor_triggered)
        self.actionDelete_Recipe_s.setEnabled(False)
        self.actionDelete_Recipe_s.triggered.connect(self.actionDelete_Recipe_s_triggered)
        self.actionfilterAuthor.setMenu(self._filter_menus[data.Author])
        self.actionfilterAuthor.toggled.connect(
            lambda checked: self.actionToolBarFilterButton_toggled(data.Author, checked))
        self.actionfilterCategories.setMenu(self._filter_menus[data.Category])
        self.actionfilterCategories.toggled.connect(
            lambda checked: self.actionToolBarFilterButton_toggled(data.Category, checked))
        self.actionfilterCuisine.setMenu(self._filter_menus[data.Cuisine])
        self.actionfilterCuisine.toggled.connect(
            lambda checked: self.actionToolBarFilterButton_toggled(data.Cuisine, checked))

        self.actionGourmet_DB.triggered.connect(self.actionGourmnet_DB_triggered)
        self.actionNew_Recipe.triggered.connect(self.actionNew_triggered)
        self.actionQuit.triggered.connect(lambda: self.close())
        self.actionRevert.setEnabled(False)
        self.actionRevert.triggered.connect(self.actionRevert_triggered)
        self.actionSave.setEnabled(False)
        self.actionSave.triggered.connect(self.actionSave_triggered)

        # -------------------- Toolbar --------------------
        self.filter_label = QtWidgets.QLabel(text=_translate("RecipeListWindow", "Filter:"))
        self.toolBar.addWidget(self.filter_label)
        self.toolBar.addAction(self.actionfilterCategories)
        self.toolBar.addAction(self.actionfilterCuisine)
        self.toolBar.addAction(self.actionfilterAuthor)
        self.toolBar.addSeparator()
        self.search_recipe_label = QtWidgets.QLabel(text=_translate("RecipeListWindow", "Search Recipe:"))
        self.toolBar.addWidget(self.search_recipe_label)
        self.search_recipe = QtWidgets.QLineEdit()
        self.search_recipe.setClearButtonEnabled(True)
        self.search_recipe.textChanged.connect(self.search_recipe_textChanged)
        self.toolBar.addWidget(self.search_recipe)

        # -------------------- TableView --------------------
        self.recipeTableView.horizontalHeader().setSectionsMovable(True)
        self.recipeTableView.setColumnHidden(self.table_model.RecipeColumns.ID, True)
        self.recipeTableView.setModel(self.table_model)
        self.recipeTableView.setSortingEnabled(True)

        self.recipeTableView.doubleClicked.connect(self.recipeTableView_doubleclicked)
        self.recipeTableView.selectionModel().selectionChanged.connect(self.recipeTableView_selectionChanged)
        self.recipeTableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.recipeTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.recipeTableView.addAction(self.actionDelete_Recipe_s)
        self.recipeTableView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # -------------------- Buttons --------------------
        self.firstPageButton.clicked.connect(self.firstPageButton_clicked)
        self.lastPageButton.clicked.connect(self.lastPageButton_clicked)
        self.nextPageButton.clicked.connect(self.nextPageButton_clicked)
        self.previousPageButton.clicked.connect(self.previousPageButton_clicked)

        index = self.recipesPerPagecomboBox.findText(str(self.table_model.recipes_per_page))
        self.recipesPerPagecomboBox.setCurrentIndex(index)

        self.recipesPerPagecomboBox.activated.connect(self.recipesPerPagecomboBox_activated)

        self.recipesSlider.valueChanged.connect(self.recipeSlider_valueChanged)

        self.update_filters()
        self.setWindowIcon(QtGui.QIcon(":/logos/qisit_128x128.png"))
        self._load_ui_states()
        self._setup_columns_menu()
        self.show()

    def update_filters(self):
        """
        Updates all the filters, either at init or after something changed

        Returns:

        """

        for table, action in ((data.Author, self.actionfilterAuthor), (data.Category, self.actionfilterCategories),
                              (data.Cuisine, self.actionfilterCuisine)):
            self._update_filter_menu(table, action)

    def actionAbout_triggered(self, checked: bool = False):
        """
        The "about" dialog

        Args:
            checked ():

        Returns:

        """
        if self._about_dialog_controller is None:
            self._about_dialog_controller = AboutdialogController()
        self._about_dialog_controller.show()

    def actionColumn_triggered(self, column: int, checked: bool = False):
        """
        The user enabled/disabled a column

        Args:
            column ():
            checked ():

        Returns:

        """
        self.recipeTableView.setColumnHidden(column, not checked)

    def actionData_editor_triggered(self, checked: bool = False):
        """
        The user selected the data editor

        Args:
            checked ():  Ignored

        Returns:

        """

        if self._data_editor is None:
            self._data_editor = DataEditorController(session = self._session)
            self._data_editor.dataCommited.connect(self.dataeditor_commited)
        self._data_editor.show()

    def actionDelete_Recipe_s_triggered(self, checked: bool = False):
        """
        Delete the selected recipes

        Args:
            checked (): ignored

        Returns:

        """

        rows = set()
        for index in self.recipeTableView.selectedIndexes():
            rows.add(index.row())

        for row in rows:
            recipe = self.table_model.recipe_at_row(row)
            self._session.delete(recipe)

        self.modified = True
        self._reload_model()

    def actionFilterMenu_triggered(self, my_table, my_id: int, checked: bool):
        """
        A filter has been changed (enabled/disabled) by the user

        Args:
            my_table (): The table the filter works on
            my_id (): The item id in the table
            checked (): on/off

        Returns:

        """

        if checked:
            self.table_model.filters[my_table].add(my_id)
            # At least one filter item has been selected. Therefore the filter icon can be unchecked by the user
            # (disabling all entries in this specific filter).
            self._action_filters[my_table].setCheckable(True)
            self._action_filters[my_table].setChecked(True)
        else:
            if my_id in self.table_model.filters[my_table]:
                self.table_model.filters[my_table].remove(my_id)
            # If there are no entries to filter there's no point in the action being checked/checkable.
            if len(self.table_model.filters[my_table]) == 0:
                self._action_filters[my_table].setChecked(False)
                self._action_filters[my_table].setCheckable(False)
        self.table_model.offset = 0
        self._reload_model()

    def actionNew_triggered(self, checked=False):
        """
        New recipe
        Args:
            checked (): ignored

        Returns:

        """
        _translate = self._translate

        title = _translate("RecipeWindow", "New Recipe")

        new_recipe = data.Recipe(title=title)
        self._session.add(new_recipe)
        self._session.commit()
        self.modified = True

        new_recipe_id = new_recipe.id
        recipe_window = None

        # Is there already a window displaying this recipe? (shouldn't be!)
        if new_recipe_id in self._recipe_windows:
            recipe_window = self._recipe_windows[new_recipe_id]
        else:
            recipe_window = recipe_window_controller.RecipeWindow(session=self._session, recipe=new_recipe,
                                                                  new_recipe=True)
            self._recipe_windows[new_recipe_id] = recipe_window
            recipe_window.destroyed.connect(lambda: self._recipe_window_closed(new_recipe_id))
            recipe_window.recipeChanged.connect(self.recipe_commited)

        recipe_window.setEnabled(True)
        recipe_window.show()
        recipe_window.raise_()

    def actionGourmnet_DB_triggered(self, checked=False):
        """
        Import Gourmet's DB

        Args:
            checked ():

        Returns:

        """

        _translate = self._translate

        home_directory = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.HomeLocation)

        # TODO: Depending on the OS?
        directory = f"{home_directory}/.gourmet"

        if not QtCore.QDir(directory).exists():
            directory = home_directory

        database_filter = _translate("RecipeWindow", "Gourmet's database file (recipes.db)")
        options = Qt.QFileDialog.ReadOnly
        filename, _ = Qt.QFileDialog.getOpenFileName(self, caption=_translate("RecipeWindow", "Select Gourmet's DB"),
                                                     directory=directory, filter=database_filter, options=options)
        filename = nullify(filename)
        if filename is not None:
            gourmet_engine = create_engine(f"sqlite:///{filename}", echo=False)

            gourmetdb.GourmetSession.configure(bind=gourmet_engine)
            gourmet_session = gourmetdb.GourmetSession()

            progress_dialog = QtWidgets.QProgressDialog(self)
            progress_dialog.setWindowTitle(_translate("RecipeListWindow", "Importing Gourmet DB"))
            progress_dialog.setCancelButtonText(_translate("RecipeListWindow", "Abort"))
            progress_dialog.setModal(True)
            importer = QTImportGourmet(progress_dialog, gourmet_session, self._session)
            try:
                errors = importer.import_gourmet(check_duplicates=True)
                if errors:
                    for error in errors:
                        print(f"{error}: {errors[error]}")
                self.update_filters()
                self._reload_model()
            except exc.OperationalError as error:
                importer.abort()
                progress_dialog.close()
                Qt.QMessageBox.critical(self, _translate("RecipeWindow", "Error importing Gourmet DB"),
                                        _translate("RecipeWindow", "Error importing Gourmet DB!"))
                # TODO: Log
                print(error)

    def actionRevert_triggered(self, checked: bool = False):
        """
        Revert

        Args:
            checked (): ignored

        Returns:

        """
        if self.modified:
            # In case of revert close all open recipe windows. One of them could be a new Recipe which would
            # be dangling after the database rollback. This is not a perfect solution.
            for recipe_window_controller in self._recipe_windows.values():
                recipe_window_controller.destroyed.disconnect()
                recipe_window_controller.forced_close()
            self._recipe_windows.clear()
            self._session.rollback()
            if self._data_editor:
                self._data_editor.revert_data()
            self.modified = False
            self.update_filters()
            self._reload_model()

    def actionSave_triggered(self, checked=False):
        """
        Save the database

        Args:
            checked ():

        Returns:

        """
        if self.modified:
            self._session.commit()
            self.modified = False

    def actionToolBarFilterButton_toggled(self, table, checked: bool):
        """
        The filter toolbar button has been checked/unchecked by the user.

        Args:
            table (): The table it operates on
            checked (): on/off

        Returns:

        """

        # The action will be checked automatically as soon as the user selects a category to filter. Nothing
        # To do in this case
        if not checked:
            # Disable all active filters and update the model
            for action in self._filter_menus[table].actions():
                action.setChecked(False)
            self.table_model.filters[table].clear()
            self._action_filters[table].setChecked(False)
            self._action_filters[table].setCheckable(False)
            self._reload_model()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Window has been closed by the user

        Args:
            event ():

        Returns:

        """
        # TODO: Ask
        if self._recipe_windows:
            for recipe_window in self._recipe_windows.values():
                recipe_window.destroyed.disconnect()
                recipe_window.close()
        self._session.commit()
        self._save_ui_states()
        event.accept()

    def dataeditor_commited(self, affected_recipe_ids: set):
        self.modified = True
        self.update_filters()
        self._reload_model()

    def firstPageButton_clicked(self):
        """
        First page clicked

        Returns:

        """
        self.table_model.offset = 0
        self._reload_model()

    def lastPageButton_clicked(self):
        """
        Last page clicked

        Returns:

        """
        self.table_model.offset = self.table_model.number_of_filtered_recipes - self.table_model.recipes_per_page
        self._reload_model()

    def nextPageButton_clicked(self):
        """
        Next page clicked

        Returns:

        """
        new_offset = self.table_model.offset + self.table_model.recipes_per_page
        if new_offset > (self.table_model.number_of_filtered_recipes - self.table_model.recipes_per_page):
            self.lastPageButton_clicked()
        else:
            self.table_model.offset = new_offset
            self._reload_model()

    def recipe_commited(self):
        """
        A recipe has been changed and saved

        Returns:

        """
        self.modified = True
        self.update_filters()
        self._reload_model()

    def recipesPerPagecomboBox_activated(self, index: int):
        """
        The user changed the recipes per page

        Args:
            index ():

        Returns:

        """
        entries_per_page = self.recipesPerPagecomboBox.itemData(index)
        self.table_model.recipes_per_page = entries_per_page

        # No need to reload the model if the entries per page exceed the available entries
        if entries_per_page < self.table_model.number_of_filtered_recipes:
            self._reload_model()

    def previousPageButton_clicked(self):
        """
        Previous page

        Returns:

        """
        new_offset = self.table_model.offset - self.table_model.recipes_per_page
        if new_offset < 0:
            self.firstPageButton_clicked()
        else:
            self.table_model.offset = new_offset
            self._reload_model()

    def recipeSlider_valueChanged(self, value: int):
        """
        The recipe slider has been changed

        Args:
            value ():

        Returns:

        """
        self.table_model.offset = value
        self._reload_model()

    def recipeTableView_doubleclicked(self, index: QtCore.QModelIndex):
        """
        Opens a new recipe window (or raises and exiting one)

        Args:
            index ():

        Returns:

        """
        recipe = self.table_model.recipe_at_row(index.row())
        if recipe:
            recipe_id = recipe.id
            recipe_window = None

            # Is there already a window displaying this recipe?
            if recipe_id in self._recipe_windows:
                recipe_window = self._recipe_windows[recipe_id]
            else:
                recipe_window = recipe_window_controller.RecipeWindow(session=self._session, recipe=recipe)
                self._recipe_windows[recipe_id] = recipe_window
                recipe_window.destroyed.connect(lambda: self._recipe_window_closed(recipe_id))
                recipe_window.recipeChanged.connect(self.recipe_commited)

            recipe_window.setEnabled(True)
            recipe_window.show()
            recipe_window.raise_()

    def recipeTableView_selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        """
        Enable/Disable the delete action

        Args:
            selected ():
            deselected ():

        Returns:

        """
        self.actionDelete_Recipe_s.setEnabled(len(self.recipeTableView.selectedIndexes()) > 0)

    def recipeTableView_sortIndicatorChanged(self, index, sort):
        """
        if a column ist not sortable (for example, it makes no sense trying to sort by thumbnails) reject
        the user's input by deactivating the sort indicator. Unfortunately there's no other/canonical way in QT to
        mark a column as "unsortable", so this is a rather ugly hack.

        Args:
            index ():
            sort ():

        Returns:

        """
        self.recipeTableView.horizontalHeader().setSortIndicatorShown(index in RecipeTableModel.sortable_columns)

    def search_recipe_textChanged(self, text: str):
        """
        The user entered some input in the search recipe LineEdit


        Args:
            text ():

        Returns:

        """
        search_text = nullify(text)
        if search_text != self._current_search_text:
            # A real change (not spaces...). If the search field is empty, search_text will be None
            self.table_model.offset = 0
            self._current_search_text = search_text
            self.table_model.search_title = search_text
            self._reload_model()
