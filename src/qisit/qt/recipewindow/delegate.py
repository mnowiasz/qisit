""" Delegates for the TreeView's editors """

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

from PyQt5 import Qt, QtCore, QtWidgets

from qisit.core.db import data
from qisit.qt.recipewindow.amounteditor import AmountEditor


class AmountDelegate(QtWidgets.QStyledItemDelegate):
    """ The amount editor (amount lineEdit, unit combobox combined) in the tree """

    illegalValue = QtCore.pyqtSignal(str)
    """ Emitted when the user has entered an illegal amount string """

    def __init__(self):
        super().__init__()
        self._combox_model = None
        self._editor = None

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        self._editor = AmountEditor(parent)
        return self._editor

    def set_combox_model(self, model):
        self._combox_model = model

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        (amount, range_amount), unit_string = index.data(QtCore.Qt.UserRole)
        self._editor.unitComboBox.setModel(self._combox_model)
        self._editor.amountLineEdit.setText(data.IngredientListEntry.format_amount_string(amount, range_amount))
        index = self._editor.unitComboBox.findText(unit_string)
        self._editor.unitComboBox.setCurrentIndex(index)

    def setModelData(self, editor: QtWidgets.QWidget, treeview_model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        (amount, range_amount), ok = self._editor.amount()
        if ok:
            unit_string = self._editor.unitComboBox.currentText().strip()
            treeview_model.setData(index, ((amount, range_amount), unit_string), QtCore.Qt.UserRole)
        else:
            self.illegalValue.emit(self._editor.amountLineEdit.text())


class EditorDelegate(QtWidgets.QStyledItemDelegate):
    """ Used to signal editing and item in the tree (so the recipe window can set itself to be modified) """

    beginEditing = QtCore.pyqtSignal()
    """ Emitted when the text is being edited """

    def __init__(self, completer: QtWidgets.QCompleter = None):
        super().__init__()
        self._completer = completer

    def createEditor(self, parent: QtWidgets.QWidget, option: Qt.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        self.beginEditing.emit()
        if self._completer is not None:
            widget = QtWidgets.QLineEdit(parent)
            widget.setCompleter(self._completer)
            return widget
        else:
            return super().createEditor(parent, option, index)
