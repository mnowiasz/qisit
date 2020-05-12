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

    for table in (data.Recipe, data.Category):
        cleanup(db_session, table)


def __setup_recipe(session, title="Test Recipe") -> data.Recipe:
    recipe = data.Recipe(title=title)
    session.add(recipe)
    session.commit()
    return recipe


def __setup_category(session, name="Test Category") -> data.Category:
    category = data.Category(name=name)
    session.add(category)
    session.commit()
    return category


def test_one_recipe_one_catagory(db_session):
    """ 1:1 """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Category).count() == 0

    the_recipe = __setup_recipe(db_session)
    the_category = __setup_category(db_session)

    the_category.recipes.append(the_recipe)
    db_session.commit()

    assert len(the_recipe.categories) == 1
    assert the_recipe.categories[0] == the_category


def test_one_recipe_many_categories(db_session):
    """ One Recipes, many categories """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Category).count() == 0

    the_recipe = __setup_recipe(db_session)
    category_one = __setup_category(db_session, "Category One")
    category_two = __setup_category(db_session, "Category Two")

    assert db_session.query(data.Category).count() == 2

    the_recipe.categories.append(category_one)
    the_recipe.categories.append(category_two)
    db_session.commit()

    assert len(the_recipe.categories) == 2
    assert category_one.recipes[0] == the_recipe
    assert category_two.recipes[0] == the_recipe


def test_many_recipes_many_categories(db_session):
    """ Many Recipes, many categories """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Category).count() == 0

    recipe_one = __setup_recipe(db_session, "Recipe One")
    recipe_two = __setup_recipe(db_session, "Recipe Two")

    category_one = __setup_category(db_session, "Category One")
    category_two = __setup_category(db_session, "Category Two")

    assert db_session.query(data.Recipe).count() == 2
    assert db_session.query(data.Category).count() == 2

    recipe_one.categories.append(category_one)
    category_two.recipes.append(recipe_one)

    category_one.recipes.append(recipe_two)
    recipe_two.categories.append(category_two)

    db_session.commit()

    assert category_one.recipes[0] == recipe_one
    assert category_one.recipes[1] == recipe_two

    assert recipe_one.categories[0] == category_one
    assert recipe_one.categories[1] == category_two

    assert category_two.recipes[0] == recipe_one
    assert category_two.recipes[1] == recipe_two

    assert recipe_two.categories[0] == category_one
    assert recipe_two.categories[1] == category_two


def test_unique_violations_recipe(db_session):
    """ A Recipe can have many categories, but not more than one of the same category """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Category).count() == 0

    the_recipe = __setup_recipe(db_session)
    the_category = __setup_category(db_session)

    the_recipe.categories.append(the_category)
    db_session.commit()

    the_category.recipes.append(the_recipe)

    # This is odd... Instead of throwing an exception the extra category will be silently discarded. Well, at least
    # There's no garbage in the database

    assert len(the_category.recipes) == 2
    assert len(the_recipe.categories) == 1  # Another oddity
    db_session.commit()
    assert len(the_category.recipes) == 1
    assert len(the_recipe.categories) == 1


def test_autodelete_recipe(db_session):
    """ Test if a deleted recipe will also deleted in the category's recipe list"""

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Category).count() == 0

    the_recipe = __setup_recipe(db_session)
    the_category = __setup_category(db_session)

    the_recipe.categories.append(the_category)
    db_session.commit()

    assert len(the_category.recipes) == 1

    db_session.delete(the_recipe)
    db_session.commit()

    assert len(the_category.recipes) == 0
    assert db_session.query(data.Category).count() == 1
    assert db_session.query(data.Recipe).count() == 0
