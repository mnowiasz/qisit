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
from babel.numbers import format_decimal, parse_decimal, NumberFormatError
from babel.units import format_unit
from sqlalchemy import orm

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify
from qisit.qt import misc


class ConversionTableModel(QtCore.QAbstractTableModel):
    changed = QtCore.pyqtSignal()
    """ Emitted when data have been changed """

    illegalValue = QtCore.pyqtSignal(misc.ValueError, str)
    """ Emitted when the user has entered an illegal value """

    def __init__(self, session: orm.Session):
        super().__init__()
        self._session = session

        self.bold_font = QtGui.QFont()
        self.bold_font.setBold(True)

        # The list of units displayed
        self._unit_list = []

        # Default type when nothing has been set
        self._unit_type = data.IngredientUnit.UnitType.MASS

    def load_model(self, unit_type: data.IngredientUnit.UnitType):
        """
        (Re)loads the model at start or whenever the user selects a new type

        Args:
            unit_type ():  The type of unit

        Returns:

        """
        self.beginResetModel()
        self._unit_type = unit_type
        # Sort order is by factor - the smallest one are the first, the largest one the last
        self._unit_list = self._session.query(data.IngredientUnit).filter(
            data.IngredientUnit.type_ == unit_type).order_by(data.IngredientUnit.factor).all()
        self.endResetModel()

    def reload_model(self):
        self.load_model(unit_type=self._unit_type)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:

        index_row = index.row()
        index_column = index.column()

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            unit_horizontal = self._unit_list[index_column]
            unit_vertical = self._unit_list[index_row]
            value = None

            # The same unit
            if index_row == index_column:
                value = 1

            # Compensate for a bug initializing the database with wrong defaults
            elif unit_vertical.factor is not None and unit_horizontal.factor is not None:
                value = unit_vertical.factor / unit_horizontal.factor
            if value is not None:
                if unit_horizontal.cldr and role == QtCore.Qt.DisplayRole:
                    return QtCore.QVariant(format_unit(value, unit_horizontal.name, length="short"))
                return QtCore.QVariant(format_decimal(value))

        if role == QtCore.Qt.FontRole:
            if index_row == index_column:
                return self.bold_font

        return None

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        index_row = index.row()
        index_column = index.column()

        if index_row == index_column:
            # Shouldn't happen.
            return False

        unit_horizontal = self._unit_list[index_column]
        unit_vertical = self._unit_list[index_row]
        factor = unit_horizontal.factor
        if factor is None:
            # Bug from initializing the database with wrong defaults
            factor = 1.0

        if unit_vertical in data.IngredientUnit.base_units.values():
            # Should also not happen - flags should have been set
            return False

        value = nullify(value)
        _translate = translate

        if value is None:
            self.illegalValue.emit(misc.ValueError.ISEMPTY, None)
            return False
        try:
            value = float(parse_decimal(value))
        except NumberFormatError:
            # The user has entered something strange.
            self.illegalValue.emit(misc.ValueError.ISNONUMBER, value)
            return False

        if value == 0:
            self.illegalValue.emit(misc.ValueError.ISZERO, "0")
            return False

        if value < 0.0:
            self.illegalValue.emit(misc.ValueError.ISNONUMBER, str(value))
            return False

        self.changed.emit()
        unit_vertical.factor = value * factor
        if unit_horizontal.factor is None:
            # Compensate for init bug
            unit_horizontal.factor = 1.0
        self.reload_model()
        return True

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        # Both horizontal and vertical header display the same unit
        unit = self._unit_list[section]
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return QtCore.QVariant(f"1 {unit.unit_string()} = ")
            return QtCore.QVariant(unit.unit_string())
        if role == QtCore.Qt.FontRole:
            if unit in data.IngredientUnit.base_units.values():
                return self.bold_font

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        flags = QtCore.Qt.ItemIsEnabled

        # row == column is also immutable
        if index.row() != index.column():
            # A vertical row containing a base unit is immutable
            unit_vertical = self._unit_list[index.row()]
            if unit_vertical not in data.IngredientUnit.base_units.values():
                flags |= QtCore.Qt.ItemIsEditable
        return flags

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unit_list)
