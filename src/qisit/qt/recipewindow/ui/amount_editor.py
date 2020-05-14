# -*- coding: utf-8 -*-

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
