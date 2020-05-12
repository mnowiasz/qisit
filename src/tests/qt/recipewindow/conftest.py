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
from sqlalchemy import create_engine
from sqlalchemy.orm import session

from qisit.core import db
from qisit.core.util import initialize_db


@pytest.fixture(scope="session")
def db_session():
    db.engine = create_engine("sqlite:///:memory:", echo=False)
    # db.engine = create_engine("mysql://qisit:qisit@127.0.0.1:33060/qisittest")
    # db.engine = create_engine("postgresql+psycopg2://qisit:qisit@127.0.0.1:54320/qisittest")

    db.Session.configure(bind=db.engine)
    the_session = db.Session()
    initialize_db(the_session, load_data=False)
    yield the_session
    session.close_all_sessions()
