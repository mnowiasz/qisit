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

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from sqlalchemy import create_engine, exc, func, orm

from qisit import translate
from qisit.core import db
from qisit.core.db import data
from qisit.core.util import nullify
from qisit.qt.dataeditor.ui import data_editor
from qisit.qt.dataeditor import data_editor_model

class DataEditorController(data_editor.Ui_dataEditor, Qt.QMainWindow):

    def __init__(self, session : orm.Session):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()
        self._session = session

        self.setupUi(self)
        self._model = data_editor_model.DataEditorModel(self._session)
        self.dataColumnView.setModel(self._model)
        self.init_ui()

    def init_ui(self):
       pass




