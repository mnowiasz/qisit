""" The GUI version of gourmet's importer """

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

from PyQt5 import Qt, QtWidgets
from sqlalchemy import orm

from qisit import translate
from qisit.importer.gourmetdb.gourmet_import import ImportGourmet


class QTImportGourmet(ImportGourmet):

    def __init__(self, progress_dialog: QtWidgets.QProgressDialog, gourmet: orm.Session, qisit: orm.Session):
        super().__init__(gourmet, qisit)
        self.progress_dialog = progress_dialog

    def is_aborted(self):
        return self.progress_dialog.wasCanceled()

    def show_info(self, output: str):
        _translate = translate
        Qt.QMessageBox.information(self.progress_dialog, _translate("RecipeWindow", "Finished Import"), output)

    def show_progress(self, current: int, upper: int, message: str, title: str = None):
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(upper)
        self.progress_dialog.setValue(current)
        self.progress_dialog.setLabelText(message)
