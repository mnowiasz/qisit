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

import pytest

from qisit.qt.recipewindow.amount_editor_controller import AmountEditor


@pytest.mark.parametrize("test_string, locale, expected, exception_expected", (
        ("2.0", "en_US", (2.0, None), False),
        ("2.000", "de_DE", (2000, None), False),
        ("Foo", "en_US", (None, None), True),
        ("", "en_US", (None, None), False),
        (None, "en_US", (None, None), False),
        ("1 - 5 - 6", "en_US", (None, None), True),
        ("1.5  - 3", "en_US", (1.5, 3.0), False),
        ("-5.0", "en_US", (None, None), True),
        ("5 - 3", "en_US", (3.0, 5.0), False)
))
def test_parse_amount(test_string: str, locale: str, expected: typing.Tuple[float, float], exception_expected: bool):
    if exception_expected:
        with pytest.raises(ValueError):
            AmountEditor.parse_amount(test_string)
    else:
        amount, range_amount = AmountEditor.parse_amount(test_string, locale)
        if amount is not None:
            assert amount == pytest.approx(expected[0])
        else:
            assert amount == expected[0]
        if range_amount is not None:
            assert range_amount == pytest.approx(expected[1])
        else:
            assert range_amount == expected[1]
