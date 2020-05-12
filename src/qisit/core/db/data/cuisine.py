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


class Cuisine(db.Base):
    """ An optional recipe's cuisine """
    __tablename__ = "cuisine"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key """

    name = sql.Column(sql.String(255), nullable=False, unique=True)
    """ The name of the cuisine like "american", "indian", ... """

    description = sql.Column(sql.Text, nullable=True)
    """ An optional description of the cuisine (HTML) """

    recipes = relationship("Recipe", order_by=Recipe.title, back_populates="cuisine")
    """ All recipes having this cusine  """

    @classmethod
    def get_or_add_cusine(cls, session_: sql.orm.session, name: str):
        """
        Get an existing cuisine or - if not existing - create a new one and add it to the database

        Args:
            session_ (): The database session
            name (): The name/title of the cuisine

        Returns:
            A cuisine object (either preexisting or created)

        """

        return db.get_or_add_item(session_=session_, table=Cuisine, name=name)

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Cuisine(name={self.name}, description={self.description})>"

    def __str__(self):
        return self.name
