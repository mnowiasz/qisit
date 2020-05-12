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

import sqlalchemy as sql

from qisit.core import db


class Meta(db.Base):
    """ Meta information about the database """
    __tablename__ = "meta"

    version = sql.Column(sql.Integer, nullable=False, primary_key=True)
    """ The schema's version, used to check if there need to be db migrations """

    def __init__(self, version: int):
        self.version = version

    def __repr__(self):
        return f"<Meta(version={self.version})>"

    def __str__(self):
        return str(self.version)
