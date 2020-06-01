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

""" Utility things """
from PyQt5 import QtWidgets, Qt, QtCore

from qisit import translate

errorMessage: QtWidgets.QErrorMessage = None
image_filter = None

class ErrorValue():
    """ Global definition for error values """
    illegal_value = "Illegal Value"


def setup():
    _translate = translate
    global image_filter, errorMessage, values
    errorMessage = QtWidgets.QErrorMessage()
    image_filter = _translate("ImageFilter", "Imagefiles ({})").format(" ".join(
        ["*.{}".format(supported_format.data().decode()) for supported_format in
         Qt.QImageReader.supportedImageFormats()]))

    values = Values()

class Values(object):
    def __init__(self):
        self.__settings = QtCore.QSettings()

    @property
    def ingredient_icon_height(self) -> int:
        """ The height of an (optional) ingredient icon"""
        return 24


values: Values = None

