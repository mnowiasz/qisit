""" The model for a combobox """

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

from PyQt5 import Qt, QtCore
from sqlalchemy import func, orm

from qisit import translate
from qisit.core import db
from qisit.core.db import data
from qisit.core.util import nullify


class DBComboBoxModel(QtCore.QAbstractListModel):
    """ A Model for the Author, Cuisine and Yieldunits """

    none_index = 0
    """ The index of the 'none' value """

    def __init__(self, db_session: orm.Session, table: db.Base):
        """
        Creates a combobox model

        Args:
            db_session (): The data base session
            table (): The table (data.YieldUnitName, data.Cuisine, ...)
        """

        super(DBComboBoxModel, self).__init__(None)
        self._session = db_session
        self._database_table = table
        self._items = []

        # This is a hack to allow NULL/None values in the combobox (i.e. let the user delete cuisine or author)
        # The first value in the combobox's list is the "empty the box/set index=1-value"
        _translate = translate
        self._text_none = [(_translate("QisitComboBoxModel", "- None -")), ]

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        row = index.row()
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        else:
            return str(self._items[row])

    def index_of_item(self, item: db.Base):
        """
        Get the index of the item (to set the combobox's index)

        Args:
            item (): The item (yield_unit_name, cuisine, author)

        Returns:
            The index or None if there isn't any (which shouldn't happen)

        """
        try:
            index = self._items.index(item)
            return index
        except ValueError:
            return None

    def insertRows(self, row: int, count: int, parent: QtCore.QModelIndex = ...) -> bool:
        """ I'm not sure why this is necessary to implement - without it won't work. Odd. """
        super().beginInsertRows(parent, row, row + count)
        return True

    def item_at(self, index):
        """
        Returns the item at the index

        Args:
            index (): the index

        Returns:
            the item in question or None if the none-item
        """
        if index == self.none_index:
            return None
        else:
            return self._items[index]

    def reload_model(self):
        """
        Reloads the model

        Returns:

        """
        super().beginResetModel()
        self._items = self._text_none + self._session.query(self._database_table).order_by(
            func.lower(self._database_table.name)).all()
        super().endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._items)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:

        if role != QtCore.Qt.EditRole:
            return False

        text = value.strip()
        if len(text) == 0:
            return False

        db.get_or_add_item(session_=self._session, table=self._database_table, name=text)
        super().endInsertRows()
        self.reload_model()
        return True


class UnitComboBoxModel(QtCore.QStringListModel):
    """ The Unit's ComboBox model """

    unitsToBeChanged = Qt.pyqtSignal()
    """ Emitted when the user enters a new unit """

    def __init__(self, db_session: orm.Session):
        """
        Creates UnitComboBoxModel

        Args:
            db_session (): The base session
        """

        self.session = db_session

        super(UnitComboBoxModel, self).__init__()
        # self.reload_model()

    def reload_model(self):
        """
        (Re-loads) the model

        Returns:

        """

        if len(data.IngredientUnit.unit_dict) == 0:
            data.IngredientUnit.update_unit_dict(self.session)

        units = sorted(data.IngredientUnit.unit_dict, key=str.casefold)
        super().setStringList(units)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        unitname = nullify(value)
        # This should never happen, because there *is* a empty value as a valid unit
        if unitname is None:
            return False

        self.unitsToBeChanged.emit()

        # It's pure guesswork which type of unit the user wanted
        data.IngredientUnit.get_or_add_ingredient_unit_name(self.session, name=unitname,
                                                            type_=data.IngredientUnit.UnitType.UNSPECIFIC)
        data.IngredientUnit.update_unit_dict(self.session)
        return super().setData(index, value, role)
