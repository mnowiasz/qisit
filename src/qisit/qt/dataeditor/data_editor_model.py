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

    class FirstColumnRows(IntEnum):
        """ Symbolic row names """
        AUTHOR = 0
        CATEGORIES = 1
        CUISINE = 2
        INGREDIENTS = 3
        INGREDIENTGROUPS = 4
        YIELD_UNITS = 5
    ROOTCOLUMN = 0
    ITEMCOLUMN = 1

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

        # The list of items displayed in the second columm
        self._item_list = []

        # For whatever reason rowCount() is called multiple times (at least four). This is to prevent unnecessary
        # loading
        self._item_parent_row = None


        self._bold_font = QtGui.QFont()
        self._bold_font.setBold(True)


    def __setup_first_column(self):
        _translate = translate
        # Table, Item, Icon
        self._first_column = {
            self.FirstColumnRows.AUTHOR: (data.Author, _translate("DataEditor", "Author"), ":/icons/quill.png"),
            self.FirstColumnRows.CATEGORIES: (data.Category, _translate("DataEditor", "Categories"), ":/icons/bread.png"),
            self.FirstColumnRows.CUISINE: (data.Cuisine, _translate("DataEditor", "Cuisine"), ":/icons/cutleries.png"),
            self.FirstColumnRows.INGREDIENTS: (data.Ingredient, _translate("DataEditor", "Ingredients"), None),
            self.FirstColumnRows.INGREDIENTGROUPS: (data.Ingredient, _translate("DataEditor", "Ingredient Groups"), None),
            self.FirstColumnRows.YIELD_UNITS: (data.YieldUnitName, _translate("DataEditor", "Yield units"), ":/icons/plates.png"),
        }

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """ There's only one column regardless of the depth of the tree """
        return 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        column = index.internalId()
        row = index.row()

        if column == self.ROOTCOLUMN:
            count = 0
            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.UserRole):
                query =  self._session.query(self._first_column[row][0])
                if row in (self.FirstColumnRows.INGREDIENTS, self.FirstColumnRows.INGREDIENTGROUPS):
                    group = row == self.FirstColumnRows.INGREDIENTGROUPS
                    # is False/is True wouldn't work here
                    query = query.filter(data.Ingredient.is_group == group)
                count = query.count()
            if role == QtCore.Qt.DisplayRole:
                text = f"{self._first_column[row][1]} ({count})"
                return QtCore.QVariant(text)
            if role == QtCore.Qt.DecorationRole and self._first_column[row][2] is not None:
                return QtCore.QVariant(QtGui.QIcon(self._first_column[row][2]))
            #if role == QtCore.Qt.FontRole:
            #    return QtCore.QVariant(self._bold_font)
            if role == QtCore.Qt.UserRole:
                return QtCore.QVariant(count)
            return QtCore.QVariant()


        if column == self.ITEMCOLUMN:
            item = self._item_list[row]
            count = item.count
            if self._item_parent_row == self.FirstColumnRows.INGREDIENTS:
                pass
            else:
                pass
                #count = len(item.recipes)
            if role == QtCore.Qt.UserRole:
                return count
            if role == QtCore.Qt.DisplayRole:
                title = f"{item.name} ({count})"
                return QtCore.QVariant(title)
        return None


    def Qflags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        return not parent.isValid() or parent.data(QtCore.Qt.UserRole) > 0


    def index(self, row: int, column: int, parent: QtCore.QModelIndex = ...) -> QtCore.QModelIndex:
        if not parent.isValid():
            # The very first column, the root column
            self._parent_row[self.ROOTCOLUMN] = row
            return self.createIndex(row, 0, self.ROOTCOLUMN)
        else:
            # The "display" column, *not* the model column
            parent_column = parent.internalId()
            self._parent_row[parent_column] = parent.row()
            return self.createIndex(row, 0, parent_column+1)

    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:

        # Again - the "display" column, *not* the model column (which is always 0)
        child_column = child.internalId()
        if child_column == self.ROOTCOLUMN:
            # The items on the root level have no parent
            return QtCore.QModelIndex()
        return self.createIndex(self._parent_row[child_column - 1], 0, child_column - 1)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:

        if parent.row()== -1:
            return self.FirstColumnRows.YIELD_UNITS + 1
        column = parent.internalId()+1

        # Lazy load the columns
        if column == self.ITEMCOLUMN:
            parent_row = parent.row()

            # Depending on the previous content or the repeated calls of rowCount(), either load the content or
            # do nothing
            if parent_row != self._item_parent_row:
                self._item_parent_row = parent_row
                self._item_list.clear()
                the_table = self._first_column[parent_row][0]

                # Construct the query
                query = None
                if parent_row in (self.FirstColumnRows.INGREDIENTS, self.FirstColumnRows.INGREDIENTGROUPS):
                    group = parent_row == self.FirstColumnRows.INGREDIENTGROUPS
                    query = self._session.query(the_table.name, the_table.id, func.count(data.IngredientListEntry.id).label("count")).join(data.IngredientListEntry, isouter=True).filter(data.Ingredient.is_group == group)
                else:
                    query = self._session.query(the_table.name, the_table.id, func.count(data.Recipe.id).label("count"))

                # Categories need an additional join
                if parent_row == self.FirstColumnRows.CATEGORIES:
                    query = query.join(data.CategoryList, data.Category.id == data.CategoryList.category_id, isouter=True)
                if parent_row in (self.FirstColumnRows.AUTHOR, self.FirstColumnRows.CATEGORIES, self.FirstColumnRows.CUISINE, self.FirstColumnRows.YIELD_UNITS):
                    query = query.join(data.Recipe, isouter=True)

                if parent_row not in (self.FirstColumnRows.INGREDIENTS, ) and False:
                    self._item_list = self._session.query(the_table.name, the_table.id, func.count(the_table.id).label("count"))\
                        .join(data.Recipe, isouter=True)\
                        .group_by(the_table.id).\
                        order_by(func.lower(the_table.name)).all()
                self._item_list =  query.group_by(the_table.id).order_by(func.lower(the_table.name)).all()
            return len(self._item_list)

        return 0





