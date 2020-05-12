""" A validator that strips the left input from whitespaces """

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

import typing

from PyQt5.Qt import QValidator


class LStripValidator(QValidator):

    def __init__(self):
        super().__init__()

    def validate(self, input: str, pos: int) -> typing.Tuple['QValidator.State', str, int]:
        valid = QValidator.Invalid

        stripped_string = input.lstrip()
        if len(stripped_string) == len(input):
            valid = QValidator.Acceptable

        return valid, input, pos

    def fixup(self, input: str) -> str:
        return input.lstrip()
