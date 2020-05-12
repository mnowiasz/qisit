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
    cleanup(db_session, data.Category)


def __setup_category(session, name="Test Category") -> data.Category:
    category = data.Category(name=name)
    session.add(category)
    session.commit()
    return category


def test_get_existing_category(db_session):
    """ Get an already existing category """

    test_title = "Test Category"
    assert db_session.query(data.Category).count() == 0
    the_category = __setup_category(db_session, test_title)
    assert db_session.query(data.Category).count() == 1

    test_category = data.Category.get_or_add_category(db_session, test_title)
    assert db_session.query(data.Category).count() == 1
    assert test_category == the_category


def test_get_non_existing_category(db_session):
    """ Get a non-existing category, creating it in the process """

    assert db_session.query(data.Category).count() == 0
    __setup_category(db_session)
    assert db_session.query(data.Category).count() == 1

    test_name = "Another Category"
    new_category = data.Category.get_or_add_category(db_session, test_name)
    assert db_session.query(data.Category).count() == 2
    assert new_category
    assert new_category.name == test_name
