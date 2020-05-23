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
from PyQt5 import QtCore, QtGui
from sqlalchemy import orm, func, text
from babel.numbers import format_decimal

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify

class ConversionTableModel(QtCore.QAbstractTableModel):

    def __init__(self, session: orm.Session):
        super().__init__()
        self._session = session
        self._unit_list = []

        self._baseunit_font = QtGui.QFont()
        self._baseunit_font.setBold(True)

    def load_model(self, unit_type: data.IngredientUnit.UnitType):
        self.beginResetModel()
        self._unit_list = []
        self._unit_list = self._session.query(data.IngredientUnit).filter(data.IngredientUnit.type_ == unit_type).order_by(data.IngredientUnit.factor).all()
        self.endResetModel()

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        index_row = index.row()
        index_column = index.column()

        if role == QtCore.Qt.DisplayRole:
            if index_row == index_column:
                return QtCore.QVariant(1)
            # Calculate
            unit_horizontal = self._unit_list[index_column]
            unit_vertical = self._unit_list[index_row]
            if unit_vertical.factor is None or unit_horizontal.factor is None:
                # Bug from defaults!
                value = 0
            else:
                value = unit_vertical.factor/ unit_horizontal.factor

            return QtCore.QVariant(format_decimal(value))
        if role == QtCore.Qt.FontRole:
            if index_row == index_column:
                return self._baseunit_font

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        unit = self._unit_list[section]
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(unit.unit_string())
        if role == QtCore.Qt.FontRole:
            if unit in data.IngredientUnit.base_units.values():
                return self._baseunit_font


    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)

