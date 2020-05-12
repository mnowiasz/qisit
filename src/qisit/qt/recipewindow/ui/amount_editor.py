# -*- coding: utf-8 -*-

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

# Form implementation generated from reading ui file 'amount_editor.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_amountEditor(object):
    def setupUi(self, amountEditor):
        amountEditor.setObjectName("amountEditor")
        amountEditor.setEnabled(True)
        amountEditor.resize(777, 52)
        amountEditor.setWindowTitle("")
        amountEditor.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.horizontalLayout = QtWidgets.QHBoxLayout(amountEditor)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.amountLineEdit = QtWidgets.QLineEdit(amountEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.amountLineEdit.sizePolicy().hasHeightForWidth())
        self.amountLineEdit.setSizePolicy(sizePolicy)
        self.amountLineEdit.setObjectName("amountLineEdit")
        self.horizontalLayout.addWidget(self.amountLineEdit)
        self.unitComboBox = QtWidgets.QComboBox(amountEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.unitComboBox.sizePolicy().hasHeightForWidth())
        self.unitComboBox.setSizePolicy(sizePolicy)
        self.unitComboBox.setEditable(True)
        self.unitComboBox.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
        self.unitComboBox.setObjectName("unitComboBox")
        self.horizontalLayout.addWidget(self.unitComboBox)

        self.retranslateUi(amountEditor)
        QtCore.QMetaObject.connectSlotsByName(amountEditor)

    def retranslateUi(self, amountEditor):
        _translate = QtCore.QCoreApplication.translate
        self.amountLineEdit.setPlaceholderText(_translate("amountEditor", "Amount"))
