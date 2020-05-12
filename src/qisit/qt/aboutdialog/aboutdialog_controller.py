""" A simple dialog """

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

import pkgutil

from PyQt5 import QtCore, QtWidgets

from qisit import translate
from qisit.qt.aboutdialog.ui import aboutdialog


class AboutdialogController(aboutdialog.Ui_AboutDialog, QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_ui()

    def init_ui(self):
        _translate = translate
        self.aboutLabel.setOpenExternalLinks(True)
        self.versionLabel.setText(
            _translate("AboutDialog", "Version: {}").format(QtCore.QCoreApplication.applicationVersion()))
        license_markdown = "**Unable to load License GPL V3!**\n\n"
        try:
            license_markdown = pkgutil.get_data("qisit", "LICENSE.md").decode("utf-8")
        except FileNotFoundError as e:
            license_markdown += str(e)
        self.licenseTextEdit.setMarkdown(license_markdown)
        self.setModal(True)
