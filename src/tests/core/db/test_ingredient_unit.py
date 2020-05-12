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

import pytest

from qisit.core.db.data import IngredientUnit
from . import add_integrity


@pytest.mark.parametrize("type_, exception_expected", (
        (IngredientUnit.UnitType.MASS, False),
        (IngredientUnit.UnitType.VOLUME, False,),
        (IngredientUnit.UnitType.QUANTITY, False),
        (IngredientUnit.UnitType.UNSPECIFIC, False),
        (IngredientUnit.UnitType.GROUP, False),
        (-1, True),
        (IngredientUnit.UnitType.GROUP + 1, True)))
def test_constraints(db_session, type_, exception_expected):
    """ Test the constraints """
    assert db_session.query(IngredientUnit).count() == 1

    test_item = IngredientUnit(name="Test", type_=type_)

    error = add_integrity(db_session, test_item, exception_expected)

    db_session.rollback()
    if error:
        pytest.fail(error)
