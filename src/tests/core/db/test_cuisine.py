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
    cleanup(db_session, data.Cuisine)


def __setup_cuisine(session, name="Test Cuisine") -> data.Cuisine:
    cuisine = data.Cuisine(name=name)
    session.add(cuisine)
    session.commit()
    return cuisine


def test_get_existing_cuisine(db_session):
    """ Get an already existing Source"""

    test_name = "Test Cuisine"
    assert db_session.query(data.Cuisine).count() == 0
    the_cuisine = __setup_cuisine(db_session, test_name)
    assert db_session.query(data.Cuisine).count() == 1

    test_cuisine = data.Cuisine.get_or_add_cusine(db_session, test_name)
    assert db_session.query(data.Cuisine).count() == 1
    assert test_cuisine == the_cuisine


def test_get_non_existing_cuisine(db_session):
    """ Get a non-existing category, creating it in the process """

    assert db_session.query(data.Cuisine).count() == 0
    __setup_cuisine(db_session)
    assert db_session.query(data.Cuisine).count() == 1

    test_name = "Another Cuisine"
    new_cuisine = data.Cuisine.get_or_add_cusine(db_session, test_name)
    assert db_session.query(data.Cuisine).count() == 2
    assert new_cuisine
    assert new_cuisine.name == test_name
