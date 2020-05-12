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

from qisit.core.db import data
from . import cleanup


def __setup_recipe(session) -> data.Recipe:
    recipe = data.Recipe("Test recipe")
    session.add(recipe)
    session.merge(recipe)
    return recipe


def __setup_cuisine(session) -> data.Cuisine:
    cuisine = data.Cuisine("Test Cuisine")
    session.add(cuisine)
    session.merge(cuisine)
    return cuisine


def test_author(db_session):
    """ Just test the relationship between recipe and cuisine """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Cuisine).count() == 0

    recipe = __setup_recipe(db_session)

    assert db_session.query(data.Recipe).count() == 1

    recipe.cuisine = data.Cuisine("Test source")
    db_session.commit()

    assert db_session.query(data.Cuisine).count() == 1

    # Now delete the author
    db_session.delete(recipe.cuisine)
    db_session.commit()
    assert db_session.query(data.Cuisine).count() == 0
    assert recipe.cuisine is None

    cleanup(db_session, data.Recipe)
    cleanup(db_session, data.Cuisine)


def test_cuisine_recpipe(db_session):
    """ Now the other way around"""

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Cuisine).count() == 0

    cuisine = __setup_cuisine(db_session)
    recipe = __setup_recipe(db_session)

    assert db_session.query(data.Recipe).count() == 1
    assert db_session.query(data.Cuisine).count() == 1

    recipe.cuisine = cuisine
    db_session.commit()

    db_session.delete(recipe)

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Cuisine).count() == 1

    cleanup(db_session, data.Recipe)
    cleanup(db_session, data.Cuisine)
