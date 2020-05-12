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
from . import add_integrity, cleanup


@pytest.fixture(autouse=True)
def cleanup_after_tests(db_session):
    yield
    cleanup(db_session, data.Recipe)


@pytest.mark.parametrize("yields, exception_expected",
                         ((0, False),
                          (-1, True),
                          ))
def test_yields_constraints(db_session, yields, exception_expected):
    """ Test serving's db constraints
    """
    assert db_session.query(data.Recipe).count() == 0

    test_object = data.Recipe("Some recipe")
    test_object.yields = yields

    error = add_integrity(db_session, test_object, exception_expected)

    if error:
        pytest.fail(error)


@pytest.mark.parametrize("rating, exception_expected",
                         ((None, False),
                          (0, False),
                          (10, False),
                          (-1, True),
                          (11, True)
                          ))
def test_rating_constraints(db_session, rating, exception_expected):
    """ Test valid/invalid ratings """

    assert db_session.query(data.Recipe).count() == 0

    test_object = data.Recipe("Some recipe", rating=rating)

    error = add_integrity(db_session, test_object, exception_expected)

    if error:
        pytest.fail(error)


@pytest.mark.parametrize("preparation_time, cook_time, total_time, exception_expected",
                         ((None, None, None, False),
                          (0, 0, 0, False),
                          (-1, None, None, True),
                          (None, -2, None, True),
                          (None, None, -5, True)
                          ))
def test_time_constraints(db_session, preparation_time, cook_time, total_time, exception_expected):
    """ Test illegal times (i.e. negative times - doesn't make much sense) """

    assert db_session.query(data.Recipe).count() == 0
    test_object = data.Recipe("Some Recipe", preparation_time=preparation_time, cooking_time=cook_time,
                              total_time=total_time)

    error = add_integrity(db_session, test_object, exception_expected)
    if error:
        pytest.fail(error)

