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
from . import cleanup


@pytest.fixture(autouse=True)
def cleanup_after_tests(db_session):
    yield
    cleanup(db_session, data.Recipe)  # This will automagically cleanup the ingredientlist
    cleanup(db_session, data.Ingredient)


def __setup_recipe(session, title: str = "Test Recipe") -> data.Recipe:
    recipe = data.Recipe(title=title)
    session.add(recipe)
    session.commit()
    return recipe


def __add_group(session, recipe: data.Recipe, group: data.Ingredient, position: int):
    """ Convenience method """
    new_entry = data.IngredientListEntry(recipe=recipe, ingredient=group, position=position,
                                         unit=data.IngredientUnit.unit_group)
    session.add(new_entry)
    session.commit()


def test_append_group(db_session):
    """ Add a group to a recipe """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Ingredient).count() == 0

    test_recipe = __setup_recipe(db_session)
    assert db_session.query(data.Recipe).count() == 1
    assert len(test_recipe.ingredientlist) == 0

    the_group = data.Ingredient("For the sauce", True)
    db_session.add(the_group)
    db_session.commit()
    assert db_session.query(data.Ingredient).count() == 1

    position = data.IngredientListEntry.get_position_for_new_group(db_session, recipe=test_recipe)
    __add_group(db_session, recipe=test_recipe, group=the_group, position=position)
    assert len(test_recipe.ingredientlist) == 1
    assert test_recipe.ingredientlist[0].position == 0

    # Now add a second and third group to the recipe
    second_group = data.Ingredient("My second group", True)
    db_session.add(second_group)
    db_session.commit()
    second_position = data.IngredientListEntry.get_position_for_new_group(db_session, recipe=test_recipe)
    __add_group(db_session, recipe=test_recipe, group=second_group, position=second_position)

    third_group = data.Ingredient("My third group", True)
    db_session.add(third_group)
    db_session.commit()
    third_position = data.IngredientListEntry.get_position_for_new_group(db_session, recipe=test_recipe)
    __add_group(db_session, recipe=test_recipe, group=third_group, position=third_position)

    assert db_session.query(data.Ingredient).count() == 3
    assert len(test_recipe.ingredientlist) == 3

    assert test_recipe.ingredientlist[0].ingredient == the_group
    assert test_recipe.ingredientlist[1].ingredient == second_group
    assert test_recipe.ingredientlist[2].ingredient == third_group
