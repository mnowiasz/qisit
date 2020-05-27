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

import pickle
import typing
from enum import IntEnum

from PyQt5 import QtCore, QtGui
from sqlalchemy import orm, func, text

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify

class RecipeListModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._recipe_list = []

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._recipe_list)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self._recipe_list[index.row()].title)
        return QtCore.QVariant()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        _translate = translate
        print("Hui")
        if role == QtCore.Qt.DisplayRole and orientation ==QtCore.Qt.Horizontal:
            return QtCore.QVariant(_translate("DataEditor", "Recipes"))

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 1

    def get_item(self, row: int):
        return self._recipe_list[row]

    def set_recipe_list(self, recipe_list: typing.List):
        self.beginResetModel()
        self._recipe_list = recipe_list
        self.endResetModel()