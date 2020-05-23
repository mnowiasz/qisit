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
from babel.numbers import format_decimal, parse_decimal, NumberFormatError
from babel.units import format_unit

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify

class ConversionTableModel(QtCore.QAbstractTableModel):

    changed = QtCore.pyqtSignal()
    """ Data have been changed """

    def __init__(self, session: orm.Session):
        super().__init__()
        self._session = session
        self._unit_list = []

        self._baseunit_font = QtGui.QFont()
        self._baseunit_font.setBold(True)
        self._unit_type = data.IngredientUnit.UnitType.MASS

    def load_model(self, unit_type: data.IngredientUnit.UnitType):
        self.beginResetModel()
        self._unit_list = []
        self._unit_list = self._session.query(data.IngredientUnit).filter(data.IngredientUnit.type_ == unit_type).order_by(data.IngredientUnit.factor).all()
        self._unit_type = unit_type
        self.endResetModel()

    def reload_model(self):
        self.load_model(unit_type = self._unit_type)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        index_row = index.row()
        index_column = index.column()

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if index_row == index_column:
                return QtCore.QVariant(1)
            # Calculate
            unit_horizontal = self._unit_list[index_column]
            unit_vertical = self._unit_list[index_row]
            if unit_vertical.factor is None or unit_horizontal.factor is None:
                # Bug from initializing the database with wrong defaults
                value = None
            else:
                value = unit_vertical.factor/ unit_horizontal.factor
            if value:
                if unit_horizontal.cldr and role == QtCore.Qt.DisplayRole:
                    return QtCore.QVariant(format_unit(value, unit_horizontal.name, length="short"))
                return QtCore.QVariant(format_decimal(value))
            else:
                return None
        if role == QtCore.Qt.FontRole:
            if index_row == index_column:
                return self._baseunit_font

        return None

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        index_row = index.row()
        index_column = index.column()

        if index_row == index_column:
            # Shouldn't happen
            return False
        unit_horizontal = self._unit_list[index_column]
        unit_vertical = self._unit_list[index_row]
        factor = unit_horizontal.factor
        if factor is None:
            # Bug from initializing the database with wrong defaults
            factor = 1.0
        if unit_vertical in data.IngredientUnit.base_units.values():
            return False

        new_value = nullify(value)
        number = 0
        if new_value is None:
            return False
        try:
            number = float(parse_decimal(new_value))
        except NumberFormatError:
            return False

        if number == 0:
            return False

        self.changed.emit()
        unit_vertical.factor = number * factor
        if unit_horizontal.factor is None:
            # Correct bug
            unit_horizontal.factor = 1.0
        self.reload_model()
        return True

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        unit = self._unit_list[section]
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return QtCore.QVariant(f"1 {unit.unit_string()} = ")
            return QtCore.QVariant(unit.unit_string())
        if role == QtCore.Qt.FontRole:
            if unit in data.IngredientUnit.base_units.values():
                return self._baseunit_font

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        flags = QtCore.Qt.ItemIsEnabled
        if index.row() != index.column():
            unit_vertical = self._unit_list[index.row()]
            if unit_vertical not in data.IngredientUnit.base_units.values():
                flags |= QtCore.Qt.ItemIsEditable
        return flags

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)

