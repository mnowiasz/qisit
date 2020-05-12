""" Test adding ingredientlist to the recipe's ingredient list"""

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

__recipe = None
__group_one = None
__group_two = None


def __add_group(session, recipe: data.Recipe, group: data.Ingredient, position: int):
    """ Convenience method """

    new_entry = data.IngredientListEntry(recipe=recipe, ingredient=group, position=position,
                                         unit=data.IngredientUnit.unit_group)
    session.add(new_entry)
    session.commit()
    return new_entry


@pytest.fixture(autouse=True)
def init_data(db_session):
    global __recipe, __group_one, __group_two

    """ Setup one recipe and two groups for the tests"""
    __recipe = data.Recipe(title="Test Recipe")
    db_session.add(__recipe)
    db_session.commit()

    position_one = data.IngredientListEntry.get_position_for_new_group(db_session, recipe=__recipe)
    ingredient_one = data.Ingredient("Group One", True)
    db_session.add(ingredient_one)
    db_session.commit()
    __group_one = __add_group(db_session, recipe=__recipe, group=ingredient_one, position=position_one)

    position_two = data.IngredientListEntry.get_position_for_new_group(db_session, recipe=__recipe)
    ingredient_two = data.Ingredient("Group Two", True)
    db_session.add(ingredient_two)
    db_session.commit()
    __group_two = __add_group(db_session, recipe=__recipe, group=ingredient_two, position=position_two)

    yield

    for table in (data.Recipe, data.Ingredient, data.IngredientListEntry):
        cleanup(db_session, table)


def test_add_to_group(db_session):
    # 1.) The global group
    position = data.IngredientListEntry.get_position_for_ingredient(db_session, recipe=__recipe, parent=None)
    assert position == 1 * data.IngredientListEntry.GROUP_INGREDIENT_FACTOR \
           + data.IngredientListEntry.GROUP_GLOBAL * data.IngredientListEntry.GROUP_FACTOR

    # 2.) Group one
    position = data.IngredientListEntry.get_position_for_ingredient(db_session, recipe=__recipe,
                                                                    parent=__group_one.position)
    assert position == 1 * data.IngredientListEntry.GROUP_INGREDIENT_FACTOR + 0 * data.IngredientListEntry.GROUP_FACTOR;

    # 3.) Group Two
    position = data.IngredientListEntry.get_position_for_ingredient(db_session, recipe=__recipe,
                                                                    parent=__group_two.position)
    assert position == 1 * data.IngredientListEntry.GROUP_INGREDIENT_FACTOR + 1 * data.IngredientListEntry.GROUP_FACTOR;


def test_add_to_same_group(db_session):
    """ Now test adding the ingredient to the same group """

    ingredient_one = data.Ingredient("Pepper, red")
    ingredient_two = data.Ingredient("Pepper, green")
    ingredient_three = data.Ingredient("Pepper, orange")

    db_session.add(ingredient_one)
    db_session.add(ingredient_two)
    db_session.add(ingredient_three)
    db_session.commit()

    ingredient_counter = 2

    counter = 1

    for group in (None, __group_one, __group_two):
        counter = 1

        for ingredient in (ingredient_one, ingredient_two, ingredient_three):
            group_position = None

            if group is not None:
                group_position = group.position

            position = data.IngredientListEntry.get_position_for_ingredient(db_session, recipe=__recipe,
                                                                            parent=group_position)
            if group:
                expected = group.position + counter * data.IngredientListEntry.GROUP_INGREDIENT_FACTOR
            else:
                expected = counter * data.IngredientListEntry.GROUP_INGREDIENT_FACTOR \
                           + data.IngredientListEntry.GROUP_GLOBAL * data.IngredientListEntry.GROUP_FACTOR

            assert position == expected
            new_entry = data.IngredientListEntry(recipe=__recipe, unit=data.IngredientUnit.unit_group,
                                                 ingredient=ingredient, position=position)
            # yes, the unit is wrong, but using this there's no need to create a dummy unit
            db_session.add(new_entry)
            db_session.commit()
            counter += 1
            ingredient_counter += 1
            assert len(__recipe.ingredientlist) == ingredient_counter
