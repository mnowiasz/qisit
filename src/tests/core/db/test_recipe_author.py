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


def __setup_author(session) -> data.Author:
    author = data.Author("Test Author")
    session.add(author)
    session.merge(author)
    return author


def test_author(db_session):
    """ Just test the relationship between recipe and author """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Author).count() == 0

    recipe = __setup_recipe(db_session)

    assert db_session.query(data.Recipe).count() == 1

    recipe.author = data.Author("Test source")
    db_session.commit()

    assert db_session.query(data.Author).count() == 1

    # Now delete the author
    db_session.delete(recipe.author)
    db_session.commit()
    assert db_session.query(data.Author).count() == 0
    assert recipe.author is None

    cleanup(db_session, data.Recipe)
    cleanup(db_session, data.Author)


def test_author_recipe(db_session):
    """ Now the other way around"""

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Author).count() == 0

    author = __setup_author(db_session)
    recipe = __setup_recipe(db_session)

    assert db_session.query(data.Recipe).count() == 1
    assert db_session.query(data.Author).count() == 1

    recipe.author = author
    db_session.commit()

    db_session.delete(recipe)

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.Author).count() == 1

    cleanup(db_session, data.Recipe)
    cleanup(db_session, data.Author)
