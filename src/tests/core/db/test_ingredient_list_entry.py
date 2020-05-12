""" Basic ingredientlist tests"""

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

__recipe = data.Recipe("Test Recipe")
__ingredient = data.Ingredient("Iest Ingredient")


@pytest.fixture(autouse=True, scope="module")
def init_data(db_session):
    db_session.add(__recipe)
    db_session.add(__ingredient)
    db_session.commit()
    yield

    for table in (data.Recipe, data.Ingredient):
        cleanup(db_session, table)


@pytest.mark.parametrize("amount, range_amount, exception_expected",
                         ((None, None, False),
                          (None, 1 / 2, True),
                          (1, 2, False),
                          (2, 1 / 2, True),
                          (1 / 4, 1 / 3, False),
                          (-1 / 3, None, True),
                          ))
def test_amounts(db_session, amount: float, range_amount: float, exception_expected):
    """ Test the validity of the amounts / range """

    assert db_session.query(data.IngredientListEntry).count() == 0

    entry = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                     amount=amount, range_amount=range_amount)

    error = add_integrity(db_session, entry, exception_expected)
    cleanup(db_session, data.IngredientListEntry)
    if error:
        pytest.fail(error)


def test_auto_delete(db_session):
    """ Test if there's a RESTRICT when deleting the ingredient """
    assert db_session.query(data.IngredientListEntry).count() == 0

    entry = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient)

    db_session.add(entry)
    db_session.commit()

    error = None

    try:
        db_session.delete(__ingredient)
        db_session.commit()
        error = "No exception raised"
    except Exception as e:
        pass
    finally:
        db_session.rollback()

    cleanup(db_session, data.IngredientListEntry)
    if error:
        pytest.fail(error)


@pytest.mark.parametrize("position, exception_expected", (
        (0, False),
        (-1, False),
        (99999999, False),
        (100000000, True)
))
def test_position(db_session, position: int, exception_expected: bool):
    """ Test valid positions """
    assert db_session.query(data.IngredientListEntry).count() == 0

    entry = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                     position=position)

    error = add_integrity(db_session, entry, exception_expected)

    # cleanup(db_session, data.IngredientList)
    if error:
        pytest.fail(error)


def test_unique_position(db_session):
    """ A position has to be unique for a given recipe """
    assert db_session.query(data.IngredientListEntry).count() == 0

    entry_1 = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                       name="Ingredient, green", position=15)
    entry_2 = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                       name="Ingredient, blue", position=15)

    db_session.add(entry_1)

    error = add_integrity(db_session, entry_2, True)
    cleanup(db_session, data.IngredientListEntry)

    if error:
        pytest.fail(error)


def test_ingredient_refs(db_session):
    """ Test the backrefs"""

    global __recipe

    assert db_session.query(data.IngredientListEntry).count() == 0

    entry_1 = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                       name="Ingredient, green", position=1)
    entry_2 = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group, ingredient=__ingredient,
                                       name="Ingredient, blue", position=2)

    db_session.add(entry_1)
    db_session.add(entry_2)
    db_session.commit()

    assert db_session.query(data.IngredientListEntry).count() == 2

    assert len(__recipe.ingredientlist) == 2
    assert len(__ingredient.recipes) == 1
    assert __ingredient.recipes[0] == __recipe
    assert entry_1.recipe == __recipe
    assert entry_2.recipe == __recipe

    # Delete the recipe -> auto delete should be in progress

    db_session.delete(__recipe)
    db_session.commit()

    assert db_session.query(data.IngredientListEntry).count() == 0
    assert len(__ingredient.recipes) == 0

    __recipe = data.Recipe("Test Recipe")
    cleanup(db_session, data.IngredientListEntry)


@pytest.mark.parametrize("position, expected", (
        (99000000, None),
        (10000, 0),
        (2010203, 2010200),
        (2010200, 2010000),
        (2010000, 2000000)
))
def test_ingredient_item_parent(position, expected):
    assert data.IngredientListEntry.item_parent(position) == expected
