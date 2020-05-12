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
from sqlalchemy.orm import relationship

from qisit.core import db
from .recipe import Recipe


class YieldUnitName(db.Base):
    """ A name of a recipe's "yield" unit """
    __tablename__ = "yield_unit_name"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key """

    name = sql.Column(sql.String(255), nullable=False, unique=True)
    """ The name of the yield unit, like glass, serving... """

    description = sql.Column(sql.Text, nullable=True)
    """ An optional description of the unit. Rich Text (HTML) """

    recipes = relationship("Recipe", order_by=Recipe.title, back_populates="yield_unit_name")
    """ All recipes where this yield unit is used """

    @classmethod
    def get_or_add_yield_unit_name(cls, session_: sql.orm.session, name: str):
        """
        Get an existing yield unit name  or - if not existing - create a new one and add it to the database

        Args:
            session_ (): The database session
            name (): The name/title of the yield unit

        Returns:
            A yield unit object (either preexisting or created)

        """

        return db.get_or_add_item(session_=session_, table=YieldUnitName, name=name)

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<YieldUnitName(name={self.name}, description={self.description})>"

    def __str__(self):
        return self.name
