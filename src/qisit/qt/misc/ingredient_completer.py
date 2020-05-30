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
from qisit.core.db import data
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from babel.numbers import format_decimal, parse_decimal, NumberFormatError
from sqlalchemy import orm, func


class IngredientCompleter(QtWidgets.QCompleter):
    """ A completer for the ingredients """

    class _CompleterModel(QtCore.QAbstractListModel):
        """ It's model. For some reasons mulitple inheritance doesn't work here .."""
        def __init__(self, session: orm.Session):
            self._session = session
            self._ingredient_list = []
            self._load_model()
            super().__init__()

        def _load_model(self):
            self._ingredient_list = self._session.query(data.Ingredient).order_by(func.lower(data.Ingredient.name)).all()

        def reload_model(self):
            self.beginResetModel()
            self._load_model()
            self.endResetModel()

        def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
            return len(self._ingredient_list)

        def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
            if index.isValid() and role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(self._ingredient_list[index.row()].name)
            return QtCore.QVariant()

    def __init__(self, session: orm.Session):
        self._session = session
        self._model = self._CompleterModel(self._session)
        super(QtWidgets.QCompleter, self).__init__(self._model, None)
        self.setCompletionRole(QtCore.Qt.DisplayRole)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def reload_model(self):
        self._model.reload_model()

