""" Utility functions and settings which are useful on a global scale, like converters, settings... """

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

from sqlalchemy import create_engine
from sqlalchemy.orm import session
from qisit.core import db
from qisit.core.db import data
from qisit.core.db.defaults import load_all


def nullify(string: str):
    """
    Convenience method to convert a empty string to None (or if was None before, just none). Otherwise strip the string

    Args:
        string (): The string to convert

    Returns:

    """
    if string:
        stripped = string.strip()
        if stripped:
            return stripped

    return None


def initialize_db(my_session: session, load_data: bool = True):
    """

    Args:
        load_data (): Load the default date (false for tests)

    Returns:

    """

    db.Base.metadata.drop_all(db.engine, checkfirst=True)
    db.Base.metadata.create_all(db.engine, checkfirst=True)

    if load_data:
        load_all(my_session)

    # Setup the default ingredient_unit
    unit_group = data.IngredientUnit(name="Internal group unit", cldr=False, factor=None,
                                        type_=data.IngredientUnit.UnitType.GROUP)
    my_session.add(unit_group)
    my_session.commit()
    data.IngredientUnit.update_unit_dict(my_session)

