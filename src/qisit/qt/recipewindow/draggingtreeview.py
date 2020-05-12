""" A Treeview that drags all items (even the invisible ones) """

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

from PyQt5 import QtCore
from PyQt5 import QtWidgets


# Since there are two invisible columns which store some essential data this workaround is necessary to ensure
# that all data are being dragged correctly
# See https://bugreports.qt.io/browse/QTBUG-30242
class DraggingTreeView(QtWidgets.QTreeView):
    def selectedIndexes(self) -> typing.List[QtCore.QModelIndex]:
        return self.selectionModel().selectedIndexes()
