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


class Category(db.Base):
    """ A single recipe's category """
    __tablename__ = "category"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key"""

    name = sql.Column(sql.String(80), nullable=False, unique=True)
    """ 
    The name of a category like curry, cake, whatever. There's no point in having two categories with the same 
    name in the database
    """

    recipes = relationship("Recipe", secondary="category_list", cascade="none", passive_deletes=True,
                           back_populates="categories", order_by="Recipe.title")
    """ The lists of recipes belonging to the category  """

    @classmethod
    def get_or_add_category(cls, session_: sql.orm.session, name: str):
        """
        Returns an already existing category object or creates if it's not existing. Useful for importing recipes or
        creating categories on the fly (when the user adds a new recipe)

        Args:
            session_ (): The database session.
            name (): The title of the category

        Returns:
            A category object
        """

        return db.get_or_add_item(session_=session_, table=Category, name=name)

    def __init__(self, name: str):
        """
        Creates a new category

        Args:
            name (): The name of the category
        """
        self.name = name

    def __repr__(self):
        return f"<Category(name={self.name})>"

    def __str__(self):
        return self.name
