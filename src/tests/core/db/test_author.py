""" Test the get_or_add-method"""

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
    cleanup(db_session, data.Author)


def __setup_author(session, name="Testsource") -> data.Author:
    source = data.Author(name=name)
    session.add(source)
    session.commit()
    return source


def test_get_existing_category(db_session):
    """ Get an already existing author"""

    test_name = "Test Author"
    assert db_session.query(data.Author).count() == 0
    the_author = __setup_author(db_session, test_name)
    assert db_session.query(data.Author).count() == 1

    test_author = data.Author.get_or_add_author(db_session, test_name)
    assert db_session.query(data.Author).count() == 1
    assert test_author == the_author


def test_get_non_existing_author(db_session):
    """ Get a non-existing category, creating it in the process """

    assert db_session.query(data.Author).count() == 0
    __setup_author(db_session)
    assert db_session.query(data.Author).count() == 1

    test_name = "Another Author"
    new_author = data.Author.get_or_add_author(db_session, test_name)
    assert db_session.query(data.Author).count() == 2
    assert new_author
    assert new_author.name == test_name
