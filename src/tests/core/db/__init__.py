""" Don't repeat yourself... """


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

def cleanup(session, table_class):
    """ Empty the table """
    session.query(table_class).delete()
    session.commit()


def add_integrity(session, test_object, exception_expected):
    """
    Test integrity errors

    Args:
        session (): The session
        test_object (): The test object
        exception_expected (): Is an error epected?

    Returns:

    """
    error = None
    try:
        session.add(test_object)
        session.merge(test_object)
        if exception_expected:
            error = "No exception raised"
    except Exception as e:
        if not exception_expected:
            error = f"Unexpected Exception: {e}"
        pass
    finally:
        session.rollback()

    return error
