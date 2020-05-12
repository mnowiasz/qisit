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


@pytest.fixture(autouse=True)
def cleanup_after_tests(db_session):
    yield
    cleanup(db_session, data.Ingredient)


def __setup_test_ingredient(session, name: str = "Test Ingredient", group: bool = False):
    ingredient = data.Ingredient(name=name, is_group=group)
    session.add(ingredient)
    session.commit()
    return ingredient


def test_ingredient_uniqueness(db_session):
    """ Test the uniqueness of an ingredient"""

    test_one = "Pepper, red"
    test_two = "Apple, green"

    # Assert that the table is empty before performing test
    assert db_session.query(data.Ingredient).count() == 0

    ingredient_one = __setup_test_ingredient(db_session, test_one)
    ingredient_two = __setup_test_ingredient(db_session, test_two)
    assert db_session.query(data.Ingredient).count() == 2

    # There might be an ingredient AND a group with the same name (difficult to imagine, but there might be a valid
    # reason for this.
    ingredient_group = data.Ingredient(test_one, is_group=True)

    error = add_integrity(db_session, ingredient_group, False)

    if error:
        pytest.fail(error)


def test_get_existing_ingredient(db_session):
    """ Test getting an existing ingredient """

    test_string = "Cream"
    assert db_session.query(data.Ingredient).count() == 0
    ingredient = __setup_test_ingredient(db_session, test_string, False)
    assert db_session.query(data.Ingredient).count() == 1

    test_ingredient = data.Ingredient.get_or_add_ingredient(db_session, test_string, False)
    assert db_session.query(data.Ingredient).count() == 1

    assert test_ingredient == ingredient


def test_get_new_ingredient(db_session):
    """ Some tests regarding getting non-existing ingredientlist """

    test_string = "Cream"

    assert db_session.query(data.Ingredient).count() == 0
    ingredient = __setup_test_ingredient(db_session, test_string, False)
    assert db_session.query(data.Ingredient).count() == 1

    # An "ingredient" that is a group can coexist with an ingredient that is an ingredient
    group = data.Ingredient.get_or_add_ingredient(db_session, test_string, True)
    assert db_session.query(data.Ingredient).count() == 2
    assert group.name == test_string
    assert group.is_group

    # Finally test a complete new ingredient

    test_string2 = "Pepper, red"

    new_ingredient = data.Ingredient.get_or_add_ingredient(db_session, test_string2, False)
    assert db_session.query(data.Ingredient).count() == 3
    assert new_ingredient.name == test_string2
    assert not new_ingredient.is_group
