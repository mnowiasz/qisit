# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'data_editor.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dataEditor(object):
    def setupUi(self, dataEditor):
        dataEditor.setObjectName("dataEditor")
        dataEditor.resize(735, 552)
        dataEditor.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.centralwidget = QtWidgets.QWidget(dataEditor)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.dataColumnView = QtWidgets.QColumnView(self.centralwidget)
        self.dataColumnView.setObjectName("dataColumnView")
        self.verticalLayout.addWidget(self.dataColumnView)
        dataEditor.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(dataEditor)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 735, 30))
        self.menubar.setObjectName("menubar")
        dataEditor.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(dataEditor)
        self.statusbar.setObjectName("statusbar")
        dataEditor.setStatusBar(self.statusbar)

        self.retranslateUi(dataEditor)
        QtCore.QMetaObject.connectSlotsByName(dataEditor)

    def retranslateUi(self, dataEditor):
        _translate = QtCore.QCoreApplication.translate
        dataEditor.setWindowTitle(_translate("dataEditor", "Data Editor"))
from qisit.qt.resources import resources_rc
