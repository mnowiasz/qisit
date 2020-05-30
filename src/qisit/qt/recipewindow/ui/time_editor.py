# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'time_editor.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_timeEditor(object):
    def setupUi(self, timeEditor):
        timeEditor.setObjectName("timeEditor")
        timeEditor.resize(413, 168)
        self.horizontalLayout = QtWidgets.QHBoxLayout(timeEditor)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.daysSpinBox = QtWidgets.QSpinBox(timeEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.daysSpinBox.sizePolicy().hasHeightForWidth())
        self.daysSpinBox.setSizePolicy(sizePolicy)
        self.daysSpinBox.setSuffix("")
        self.daysSpinBox.setObjectName("daysSpinBox")
        self.horizontalLayout.addWidget(self.daysSpinBox)
        self.hoursSpinBox = QtWidgets.QSpinBox(timeEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hoursSpinBox.sizePolicy().hasHeightForWidth())
        self.hoursSpinBox.setSizePolicy(sizePolicy)
        self.hoursSpinBox.setWrapping(True)
        self.hoursSpinBox.setMaximum(24)
        self.hoursSpinBox.setObjectName("hoursSpinBox")
        self.horizontalLayout.addWidget(self.hoursSpinBox)
        self.minutesSpinBox = QtWidgets.QSpinBox(timeEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.minutesSpinBox.sizePolicy().hasHeightForWidth())
        self.minutesSpinBox.setSizePolicy(sizePolicy)
        self.minutesSpinBox.setWrapping(True)
        self.minutesSpinBox.setMaximum(300)
        self.minutesSpinBox.setObjectName("minutesSpinBox")
        self.horizontalLayout.addWidget(self.minutesSpinBox)
        self.clearButton = QtWidgets.QPushButton(timeEditor)
        self.clearButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/cross.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.clearButton.setIcon(icon)
        self.clearButton.setObjectName("clearButton")
        self.horizontalLayout.addWidget(self.clearButton)

        self.retranslateUi(timeEditor)
        QtCore.QMetaObject.connectSlotsByName(timeEditor)

    def retranslateUi(self, timeEditor):
        _translate = QtCore.QCoreApplication.translate
        timeEditor.setWindowTitle(_translate("timeEditor", "Form"))
        self.clearButton.setText(_translate("timeEditor", "Clear"))


