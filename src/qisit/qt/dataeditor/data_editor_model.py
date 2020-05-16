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
from sqlalchemy import orm

from qisit import translate


class DataEditorModel(QtCore.QAbstractItemModel):

    class FirstColumnRows(IntEnum):
        """ Symbolic row names """
        AUTHOR = 0
        CATEGORIES = 1
        CUISINE = 2
        INGREDIENTS = 3
        YIELD_UNITS = 4
    ROOTCOLUMN = 0

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
        self._first_column = {}
        self.__setup_first_column()
        self._bold_font = QtGui.QFont()
        self._bold_font.setBold(True)


    def __setup_first_column(self):
        _translate = translate
        # Item, Icon
        self._first_column = {
            self.FirstColumnRows.AUTHOR: (_translate("DataEditor", "Author"), ":/icons/quill.png"),
            self.FirstColumnRows.CATEGORIES: (_translate("DataEditor", "Categories"), ":/icons/bread.png"),
            self.FirstColumnRows.INGREDIENTS: (_translate("DataEditor", "Ingredients"), None),
            self.FirstColumnRows.CUISINE: (_translate("DataEditor", "Cuisine"), ":/icons/cutleries.png"),
            self.FirstColumnRows.YIELD_UNITS: (_translate("DataEditor", "Yield units"), ":/icons/plates.png"),
        }

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """ There's only one column regardless of the depth of the tree """
        return 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        column = index.internalId()
        row = index.row()

        if column == self.ROOTCOLUMN:
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(self._first_column[row][0])
            if role == QtCore.Qt.DecorationRole and self._first_column[row][1] is not None:
                return QtCore.QVariant(QtGui.QIcon(self._first_column[row][1]))
            #if role == QtCore.Qt.FontRole:
            #    return QtCore.QVariant(self._bold_font)
            return QtCore.QVariant()

    def Qflags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        return not parent.isValid()

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

        # Again - the "display" column, *not* the model column (which is alaways 0)
        child_column = child.internalId()
        if child_column == self.ROOTCOLUMN:
            # The items on the root level have no parent
            return QtCore.QModelIndex()
        return self.createIndex(self._parent_row[child_column - 1], 0, child_column - 1)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if parent.row()== -1:
            return self.FirstColumnRows.YIELD_UNITS + 1




