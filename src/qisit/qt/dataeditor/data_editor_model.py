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

from PyQt5 import QtCore, QtGui
from sqlalchemy import orm, func

from qisit import translate
from qisit.core.db import data


class DataEditorModel(QtCore.QAbstractItemModel):
    class RootItems(IntEnum):
        """ Symbolic row names """
        AUTHOR = 0
        CATEGORIES = 1
        CUISINE = 2
        INGREDIENTS = 3
        INGREDIENTGROUPS = 4
        YIELD_UNITS = 5

    class Columns(IntEnum):
        """ Symoblic column names """

        ROOT = 0
        ITEMS = 1
        REFERENCED = 2
        RECIPES = 3  # Only for ingredients, otherwise REFERENCED is the last column

    class FirstColumnData(IntEnum):
        """ Symbolic names for self:_first_column """
        TABLE = 0
        NAME = 1
        ICON = 2

    def __init__(self, session: orm.Session):

        super().__init__()
        self._session = session

        # This needs some explanation. index() need to save information about it's parent so parent() can extract these
        # to create a valid index. Unfortunately it's not possible to save information into index's.internalPointer() -
        # Python's garbage collector causes havoc in this case, deleting the object stored into internalPointer(). So
        # apart from saving the information in the model (i.e. in a structure like a list, dictionary or tree) - which
        # is overkill in this case - this is used to store *which row* has been selected as a parent in the given
        # column.
        self._parent_row = {}

        # Table, Text, Icon.
        self._first_column = {}
        self.__setup_first_column()

        # The list of items displayed in the column
        self._item_lists = {column: [] for column in self.Columns}

        # For whatever reason rowCount() is called multiple times (at least four). This is to prevent unnecessary
        # loading
        self._item_parent_rows = [None for column in self.Columns]

    def __setup_first_column(self):
        _translate = translate
        # Table, Item, Icon
        self._first_column = {
            self.RootItems.AUTHOR: (data.Author, _translate("DataEditor", "Author"), ":/icons/quill.png"),
            self.RootItems.CATEGORIES: (
                data.Category, _translate("DataEditor", "Categories"), ":/icons/bread.png"),
            self.RootItems.CUISINE: (data.Cuisine, _translate("DataEditor", "Cuisine"), ":/icons/cutleries.png"),
            self.RootItems.INGREDIENTS: (
            data.Ingredient, _translate("DataEditor", "Ingredients"), ":/icons/mushroom.png"),
            self.RootItems.INGREDIENTGROUPS: (
                data.Ingredient, _translate("DataEditor", "Ingredient Groups"), ":/icons/edit-bold.png"),
            self.RootItems.YIELD_UNITS: (
                data.YieldUnitName, _translate("DataEditor", "Yield units"), ":/icons/plates.png"),
        }

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """ There's only one column regardless of the depth of the tree """
        return 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        column = index.internalId()
        row = index.row()
        count = 0
        if column == self.Columns.ROOT:
            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.UserRole):
                # Construct a query, i.e. which table to query
                query = self._session.query(self._first_column[row][self.FirstColumnData.TABLE])

                # Ingredients and ingredientsgroups only differ whether to display ingredients groups
                # (and no ingredients) or only ingredients (and not groups)
                if row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTGROUPS):
                    group = (row == self.RootItems.INGREDIENTGROUPS)
                    # is False/is True wouldn't work here
                    query = query.filter(data.Ingredient.is_group == group)
                count = query.count()

                if role == QtCore.Qt.DisplayRole:
                    text = f"{self._first_column[row][self.FirstColumnData.NAME]} ({count})"
                    return QtCore.QVariant(text)
                if role == QtCore.Qt.UserRole:
                    return QtCore.QVariant(count)
            if role == QtCore.Qt.DecorationRole and self._first_column[row][self.FirstColumnData.ICON] is not None:
                return QtCore.QVariant(QtGui.QIcon(self._first_column[row][self.FirstColumnData.ICON]))
            return QtCore.QVariant()

        if column == self.Columns.ITEMS:
            item = self._item_lists[column][row]
            count = item[1]
            if role == QtCore.Qt.UserRole:
                return QtCore.QVariant(count)
            if role == QtCore.Qt.DisplayRole:
                title = f"{item[0].name} ({count})"
                return QtCore.QVariant(title)
        elif column == self.Columns.REFERENCED:
            item = self._item_lists[column][row]
            if role == QtCore.Qt.UserRole:
                if self._parent_row[self.Columns.ROOT] == self.RootItems.INGREDIENTS:
                    # Ingredients have a four column
                    return 1
                else:
                    return 0

            if role == QtCore.Qt.DisplayRole:
                # Different items have different leaves: Author, Cusine, ... have the recipes' belonging to them
                # displayed in it's leaf ("referenced") column. Ingredients on the other hand have got
                # Ingredientlist entries displayed there. Recipes have got a title, all other tables a name (this was
                # probably an oversight, if a recipe would have a name instead of a title, the code underneath would be
                # unnecessary). But too much bother to change the database now.
                if self._parent_row[self.Columns.ROOT] == self.RootItems.INGREDIENTS:
                    return QtCore.QVariant(item.name)
                else:
                    return QtCore.QVariant(item.title)
        elif column == self.Columns.RECIPES:
            if role == QtCore.Qt.DisplayRole:
                recipe = self._item_lists[column][row]
                return QtCore.QVariant(recipe.title)
            if role == QtCore.Qt.UserRole:
                return 0
        return QtCore.QVariant(None)

    def OFFflags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        # Currently disabled, hence the OFF
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        # Number of children is stored in the item's user role
        return not parent.isValid() or parent.data(QtCore.Qt.UserRole) > 0

    def index(self, row: int, column: int, parent: QtCore.QModelIndex = ...) -> QtCore.QModelIndex:
        if not parent.isValid():
            # The very first column, the root column. There's only one (model) column, hence the 0
            return self.createIndex(row, 0, self.Columns.ROOT)
        else:
            # The "display" column, *not* the model column
            parent_column = parent.internalId()
            self._parent_row[parent_column] = parent.row()
            return self.createIndex(row, 0, parent_column + 1)

    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:

        # Again - the "display" column, *not* the model column (which is always 0)
        child_column = child.internalId()
        if child_column == self.Columns.ROOT:
            # The items on the root level have no parent
            return QtCore.QModelIndex()
        return self.createIndex(self._parent_row[child_column - 1], 0, child_column - 1)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if parent.row() == -1:
            return self.RootItems.YIELD_UNITS + 1

        column = parent.internalId() + 1

        # Lazily load the columns. Note: Usually this is done using fetchMore() / canFetchMore. However, since
        # counting the rows and fetching the data at the same time is more efficient than first counting the rows
        # and then fetching the data (duplicating the same joins) this is done here
        parent_row = parent.row()

        # Depending on the previous content or the repeated calls of rowCount(), either load the content or
        # do nothing

        if parent_row != self._item_parent_rows[column]:

            # Reset all further columns, otherwise odd things might happen: if the next column has the same parent_row
            # as before, it wouldn't be reloaded creating odd effects
            for the_column in range(column + 1, self.Columns.RECIPES + 1):
                self._item_parent_rows[the_column] = None
            self._item_parent_rows[column] = parent_row

            if column == self.Columns.ITEMS:
                the_table = self._first_column[parent_row][self.FirstColumnData.TABLE]

                # Construct the query
                query = None
                if parent_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTGROUPS):
                    group = (parent_row == self.RootItems.INGREDIENTGROUPS)
                    query = self._session.query(the_table, func.count(data.IngredientListEntry.id).label("count")) \
                        .join(data.IngredientListEntry, isouter=True).filter(data.Ingredient.is_group == group)
                else:
                    query = self._session.query(the_table, func.count(data.Recipe.id).label("count"))

                    # Categories need an additional join
                    if parent_row == self.RootItems.CATEGORIES:
                        query = query.join(data.CategoryList, data.Category.id == data.CategoryList.category_id,
                                           isouter=True)
                    query = query.join(data.Recipe, isouter=True)

                self._item_lists[column] = query.group_by(the_table.id).order_by(func.lower(the_table.name)).all()

            elif column == self.Columns.REFERENCED:
                item = self._item_lists[self.Columns.ITEMS][parent_row][0]

                # Copy the lists. Otherwise - when cleared - they would be erased from the
                # database itself: items/recipes are sqlalchemy lists, very convenient - but changes
                # there will cause database changes, too, so clearing() such a list will cause the references
                # to be deleted for real.
                if self._parent_row[self.Columns.ROOT] == self.RootItems.INGREDIENTS:
                    self._item_lists[column] = [ingredient for ingredient in item.items]
                else:
                    self._item_lists[column] = [recipe for recipe in item.recipes]
            elif column == self.Columns.RECIPES:
                recipe = self._item_lists[self.Columns.REFERENCED][parent_row].recipe
                self._item_lists[column] = [recipe, ]
            else:
                return 0

        return len(self._item_lists[column])
