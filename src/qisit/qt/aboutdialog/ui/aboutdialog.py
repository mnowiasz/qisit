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

# Form implementation generated from reading ui file 'aboutdialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(400, 323)
        AboutDialog.setSizeIncrement(QtCore.QSize(1, 1))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(AboutDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.imageLabel = QtWidgets.QLabel(AboutDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imageLabel.sizePolicy().hasHeightForWidth())
        self.imageLabel.setSizePolicy(sizePolicy)
        self.imageLabel.setMinimumSize(QtCore.QSize(128, 128))
        self.imageLabel.setSizeIncrement(QtCore.QSize(1, 1))
        self.imageLabel.setText("")
        self.imageLabel.setPixmap(QtGui.QPixmap(":/logos/qisit_128x128.png"))
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setObjectName("imageLabel")
        self.horizontalLayout_2.addWidget(self.imageLabel)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.programLabel = QtWidgets.QLabel(AboutDialog)
        font = QtGui.QFont()
        font.setPointSize(24)
        self.programLabel.setFont(font)
        self.programLabel.setObjectName("programLabel")
        self.horizontalLayout.addWidget(self.programLabel)
        self.gplLabel = QtWidgets.QLabel(AboutDialog)
        self.gplLabel.setText("")
        self.gplLabel.setPixmap(QtGui.QPixmap(":/logos/gplv3-88x31.png"))
        self.gplLabel.setScaledContents(False)
        self.gplLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.gplLabel.setObjectName("gplLabel")
        self.horizontalLayout.addWidget(self.gplLabel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.versionLabel = QtWidgets.QLabel(AboutDialog)
        self.versionLabel.setObjectName("versionLabel")
        self.verticalLayout.addWidget(self.versionLabel)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.tabWidget = QtWidgets.QTabWidget(AboutDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.aboutLabel = QtWidgets.QLabel(self.tab)
        self.aboutLabel.setWordWrap(True)
        self.aboutLabel.setObjectName("aboutLabel")
        self.verticalLayout_4.addWidget(self.aboutLabel)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.licenseTextEdit = QtWidgets.QTextEdit(self.tab_2)
        self.licenseTextEdit.setReadOnly(True)
        self.licenseTextEdit.setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Noto Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.licenseTextEdit.setObjectName("licenseTextEdit")
        self.verticalLayout_3.addWidget(self.licenseTextEdit)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(AboutDialog)
        self.buttonBox.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(AboutDialog)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(AboutDialog.accept)
        self.buttonBox.rejected.connect(AboutDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        _translate = QtCore.QCoreApplication.translate
        AboutDialog.setWindowTitle(_translate("AboutDialog", "About"))
        self.programLabel.setText(_translate("AboutDialog", "Qisit"))
        self.versionLabel.setText(_translate("AboutDialog", "Version"))
        self.aboutLabel.setText(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Noto Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Qisit - © 2020 <a href=\"https://mark.nowiasz.de/\"><span style=\" text-decoration: underline; color:#2980b9;\">Mark Nowiasz</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Some icons by <a href=\"http://p.yusukekamiyamane.com/\"><span style=\" text-decoration: underline; color:#2980b9;\">Yusuke Kamiyamane</span></a>. Licensed under a <a href=\"http://creativecommons.org/licenses/by/3.0/\"><span style=\" text-decoration: underline; color:#2980b9;\">Creative Commons Attribution 3.0 License</span></a>.</p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("AboutDialog", "About"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("AboutDialog", "License"))
from qisit.qt.resources import resources_rc
