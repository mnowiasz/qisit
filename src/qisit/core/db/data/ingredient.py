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
from sqlalchemy import orm
from qisit.core import db


class Ingredient(db.Base):
    """
    A single, unique ingredient. This is used for three purposes:
    1.) So you can search/filter more easily, for example: "onions, diced", or "onions, rings" would point to "onion".
        if you want to list each recipe containing onion the recipes containing "onions, diced" or "onions, rings"
        would be listed
    2.) For nutritional information (not yet (re-)implemented)
    3.) So ingredients can have an icon (so all tomato related ingredients have got a small tomato icon)
    """
    __tablename__ = "ingredient"
    __table_args__ = (sql.UniqueConstraint("name", "is_group"),)

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key"""

    name = sql.Column(sql.String(80), nullable=False, index=True)
    """ The (normalized) name of the ingredient, like "pepper, red" """

    is_group = sql.Column(sql.Boolean, nullable=False, default=False)
    """ The "ingredient" is in fact a name of a group ("For the sauce") """

    icon = sql.Column(sql.LargeBinary, nullable=True, default=None)
    """ An optional icon for this ingredient  """

    items = orm.relationship("IngredientListEntry", back_populates="ingredient")
    """ All items referring to this ingredient """

    recipes = orm.relationship("Recipe", secondary="ingredient_list_entry",
                           primaryjoin="Ingredient.id == IngredientListEntry.ingredient_id",
                           secondaryjoin="Recipe.id == IngredientListEntry.recipe_id", viewonly=True,
                           order_by="Recipe.title")
    """ All recipes that contain this ingredient """

    @classmethod
    def get_or_add_ingredient(cls, session_: sql.orm.session, name: str, is_group: bool = False):
        """
        Returns and existing ingredient object or create one if the ingredient doesn't exist (yes)

        Args:
            session_ (): The session
            name (): The name of the ingredient
            is_group (): If true, the ingredient is a group

        Returns:
            An  existing ingredient or a freshly created one

        """

        return db.get_or_add_item(session_=session_, table=Ingredient, name=name,
                                  filter_args=(Ingredient.name == name, Ingredient.is_group == is_group),
                                  is_group=is_group)

    def __init__(self, name: str, is_group: bool = False):
        """
        Create a new (normalized/unique) ingredient

        Args:
            name (): The name, must be unique ("Pepper, red")
            is_group (): The name is not a conventional ingredient but a group
        """
        self.name = name
        self.is_group = is_group
        self.icon = None

    def __repr__(self):
        return f"<Ingredient(name={self.name}, is_group={self.is_group}, icon={self.icon})>"

    def __str__(self):
        if self.is_group:
            return f"--- {self.name}: ---"
        else:
            return self.name
