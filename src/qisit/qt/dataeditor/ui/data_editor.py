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
        self.dataColumnView.setFocusPolicy(QtCore.Qt.NoFocus)
        self.dataColumnView.setDragEnabled(True)
        self.dataColumnView.setDragDropOverwriteMode(True)
        self.dataColumnView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.dataColumnView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.dataColumnView.setObjectName("dataColumnView")
        self.verticalLayout.addWidget(self.dataColumnView)
        dataEditor.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(dataEditor)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 735, 30))
        self.menubar.setObjectName("menubar")
        self.menuData = QtWidgets.QMenu(self.menubar)
        self.menuData.setObjectName("menuData")
        dataEditor.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(dataEditor)
        self.statusbar.setObjectName("statusbar")
        dataEditor.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(dataEditor)
        self.toolBar.setObjectName("toolBar")
        dataEditor.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionSave = QtWidgets.QAction(dataEditor)
        self.actionSave.setEnabled(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/disk.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon)
        self.actionSave.setObjectName("actionSave")
        self.actionRevert = QtWidgets.QAction(dataEditor)
        self.actionRevert.setEnabled(False)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/arrow-return-180-left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRevert.setIcon(icon1)
        self.actionRevert.setObjectName("actionRevert")
        self.actionDelete = QtWidgets.QAction(dataEditor)
        self.actionDelete.setEnabled(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDelete.setIcon(icon2)
        self.actionDelete.setObjectName("actionDelete")
        self.menuData.addAction(self.actionSave)
        self.menuData.addAction(self.actionRevert)
        self.menubar.addAction(self.menuData.menuAction())
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionRevert)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionDelete)

        self.retranslateUi(dataEditor)
        QtCore.QMetaObject.connectSlotsByName(dataEditor)

    def retranslateUi(self, dataEditor):
        _translate = QtCore.QCoreApplication.translate
        dataEditor.setWindowTitle(_translate("dataEditor", "Data Editor"))
        self.menuData.setTitle(_translate("dataEditor", "Data"))
        self.toolBar.setWindowTitle(_translate("dataEditor", "toolBar"))
        self.actionSave.setText(_translate("dataEditor", "Save"))
        self.actionRevert.setText(_translate("dataEditor", "Revert"))
        self.actionDelete.setText(_translate("dataEditor", "Delete"))
from qisit.qt.resources import resources_rc
