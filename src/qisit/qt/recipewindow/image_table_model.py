""" The model for recipe's image table """

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
from qisit.core.db import data
from qisit.core.util import nullify


class ImageTableModel(QtGui.QStandardItemModel):
    class ImageTableColumns(IntEnum):
        """ Symbolic column names """
        IMAGE = 0
        DESCRIPTION = 1

    beginReordering = QtCore.pyqtSignal()
    """ Emitted when a drop took place """

    def __init__(self, session: orm.Session, recipe: data.Recipe):
        super().__init__()
        self._session = session
        self._recipe = recipe
        self.__editable = False

    @property
    def editable(self) -> bool:
        return self.__editable

    @editable.setter
    def editable(self, editable: bool):
        self.__editable = editable

        # Set all the description items editable (or not)
        for row in range(0, self.rowCount(self.invisibleRootItem().index())):
            description_item = self.item(row, self.ImageTableColumns.DESCRIPTION)
            description_item.setEditable(editable)

    def canDropMimeData(self, data: 'QMimeData', action: QtCore.Qt.DropAction, row: int, column: int,
                        parent: QtCore.QModelIndex) -> bool:
        # Drop on an item is not permitted. Only moves
        if row == -1 and column == -1:
            return False

        # Drop only on the image column
        if column != self.ImageTableColumns.IMAGE:
            return False

        return super().canDropMimeData(data, action, row, column, parent)

    def dropMimeData(self, data: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                     parent: QtCore.QModelIndex) -> bool:
        self.beginReordering.emit()
        return super().dropMimeData(data, action, row, column, parent)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if role != QtCore.Qt.DisplayRole:
            return None

        __translate = translate
        if orientation == QtCore.Qt.Vertical:
            return QtCore.QVariant(section + 1)
        elif orientation == QtCore.Qt.Horizontal:
            if section == self.ImageTableColumns.IMAGE:
                return QtCore.QVariant(__translate("RecipeWindow", "Image"))
            elif section == self.ImageTableColumns.DESCRIPTION:
                return QtCore.QVariant(__translate("RecipeWindow", "Description"))
        return None

    def load_model(self):
        """
        (Re)loads the model

        Returns:

        """
        self.clear()

        imagelist_row = 0
        for imagelist_entry in self._recipe.imagelist:
            new_row = self.setup_row(imagelist_entry)
            new_row[self.ImageTableColumns.IMAGE].setData(imagelist_row, QtCore.Qt.UserRole)
            self.appendRow(new_row)
            imagelist_row += 1

    def reorder_imagelist(self):
        """
        Reorders recipe's imagelist's positions so they reflect the model - done when saving the recipe

        Returns:
        """

        # To avoid triggering the unique constraints the reordering will be done in two steps.

        # Step 1: create temporary positions - negative ones. 0 becomes -1, 1 -2, and so on
        for row in range(0, self.rowCount(self.invisibleRootItem().index())):
            image_item = self.item(row, self.ImageTableColumns.IMAGE)
            imagelist_index = int(image_item.data(QtCore.Qt.UserRole))

            # Save the final index in the model - no need to do it in the second step
            image_item.setData(row, QtCore.Qt.UserRole)
            self._recipe.imagelist[imagelist_index].position = (-1 * row) - 1

        # Necessary, otherwise sqlalchemy would try to optimize the UPDATE statemens -> constraint triggered
        self._session.merge(self._recipe)
        self._session.refresh(self._recipe)

        # Step 2: The final positions
        for row in range(0, len(self._recipe.imagelist)):
            imagelist_item = self._recipe.imagelist[row]
            imagelist_item.position = (-1 * imagelist_item.position) - 1

        self._session.merge(self._recipe)
        self._session.refresh(self._recipe)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        column = index.column()
        row = index.row()

        if row >= 0 and column == self.ImageTableColumns.DESCRIPTION:
            imagelist_row = int(index.siblingAtColumn(self.ImageTableColumns.IMAGE).data(QtCore.Qt.UserRole))
            self._recipe.imagelist[imagelist_row].description = nullify(value)

        return super().setData(index, value, role)

    def setup_row(self, imagelist_entry: data.RecipeImage) -> typing.List[QtGui.QStandardItem]:
        """
        Sets up a new row and fills most of the data

        Args:
            imagelist_entry (): The entry

        Returns:

        """

        new_row = [QtGui.QStandardItem() for column in self.ImageTableColumns]
        defaultflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

        image = QtGui.QPixmap()
        image.loadFromData(imagelist_entry.thumbnail)

        new_row[self.ImageTableColumns.IMAGE].setData(image, QtCore.Qt.DecorationRole)
        new_row[self.ImageTableColumns.IMAGE].setData(image.size(), QtCore.Qt.SizeHintRole)
        new_row[self.ImageTableColumns.IMAGE].setFlags(defaultflags | QtCore.Qt.ItemIsDropEnabled)

        new_row[self.ImageTableColumns.DESCRIPTION].setData(imagelist_entry.description, QtCore.Qt.DisplayRole)
        if self.editable:
            new_row[self.ImageTableColumns.DESCRIPTION].setFlags(defaultflags | QtCore.Qt.ItemIsEditable)
        else:
            new_row[self.ImageTableColumns.DESCRIPTION].setFlags(defaultflags)

        return new_row
