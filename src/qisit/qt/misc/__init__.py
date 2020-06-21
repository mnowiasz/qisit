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

from enum import IntEnum

from PyQt5 import Qt, QtCore, QtWidgets

from qisit import translate

image_filter = None
whats_this_action = None


class IllegalValueEntered(IntEnum):
    """ The user has entered an illegal value """
    ISEMPTY = 0
    """ No value """
    ISNONUMBER = 1
    """ Unparsable number """
    ISZERO = 2
    """ The number is zero """
    ISDUPLICATE = 3
    """ Duplicate value """


def setup_image_filter():
    _translate = translate
    global image_filter, values

    image_filter = _translate("ImageFilter", "Imagefiles ({})").format(" ".join(
        ["*.{}".format(supported_format.data().decode()) for supported_format in
         Qt.QImageReader.supportedImageFormats()]))

    values = Values()

def setup_global_actions():
    global whats_this_action
    whats_this_action = QtWidgets.QWhatsThis.createAction()

class Values(object):
    def __init__(self):
        self.__settings = QtCore.QSettings()

    @property
    def ingredient_icon_height(self) -> int:
        """ The height of an (optional) ingredient icon"""
        return 24


values: Values = None
