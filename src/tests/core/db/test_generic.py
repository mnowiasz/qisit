""" Generic tests like __str__, add/delete, uniqueness.. """
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

from qisit.core.db import data
from . import cleanup, add_integrity



# Database classes/tables, expected, unique, arguments passed to __init__
__test_data = [(data.Category, "Cookies", True, ["Cookies", ]),
               (data.Ingredient, "Pepper", True, ["Pepper", False]),
               (data.Ingredient, "--- For the Sauce: ---", True, ["For the Sauce", True]),
               (data.Recipe, "Vindaloo", False, ["Vindaloo", ]),
               (data.Recipe, "Chicken Madras (5)", False, ["Chicken Madras", None, None, None, 5]),
               (data.Author, "Gramma", True, ["Gramma", ]),
               (data.Cuisine, "American", True, ["American", ]),
               (data.YieldUnitName, "Servings", True, ["Servings", ]),
               ]

# Database classes/tables that can't have a NULL string as a name
__test_data_none = (data.Category, data.Ingredient, data.Recipe, data.Author)


@pytest.mark.parametrize("test_table, expected, unique, args", __test_data)
def test_str(test_table, expected, unique, args):
    """ A simple test for __str__  unique is not used"""

    test_object = test_table(*args)
    assert str(test_object) == expected


@pytest.mark.parametrize("test_table, expected, unique, args", __test_data)
def test_add_delete(db_session, test_table, expected, unique, args):
    """ Just a simple add. expected won't be used, and so is unique """

    # Assert that the table is empty before performing test
    assert db_session.query(test_table).count() == 0

    test_object = test_table(*args)
    db_session.add(test_object)
    db_session.commit()
    assert db_session.query(test_table).count() == 1

    db_session.delete(test_object)
    db_session.commit()
    assert db_session.query(test_table).count() == 0


@pytest.mark.parametrize("test_table", __test_data_none)
def test_not_null(db_session, test_table):
    """ Test the NOT NULL-Constraint. Unique ist not used """

    # Assert that the table is empty before performing test
    assert db_session.query(test_table).count() == 0

    test_object = test_table(None)

    error = add_integrity(db_session, test_object, True)
    if error:
        pytest.fail(error)


@pytest.mark.parametrize("test_table, expected, unique, args", __test_data)
def test_unique(db_session, test_table, expected, unique, args):
    """ Test the UNIQUE constraint"""

    # Assert that the table is empty before performing test
    assert db_session.query(test_table).count() == 0

    test_object_one = test_table(*args)
    test_object_two = test_table(*args)

    db_session.add(test_object_one)
    assert db_session.query(test_table).count() == 1

    error = add_integrity(db_session, test_object_two, unique)
    cleanup(db_session, test_table)

    if error:
        pytest.fail(error)
