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

import datetime

import sqlalchemy as sql
from sqlalchemy.orm import relationship

from qisit.core import db


class Recipe(db.Base):
    """ A singe recipe """
    __tablename__ = "recipe"

    id = sql.Column(sql.Integer, primary_key=True)
    """ The primary key """

    author_id = sql.Column(sql.Integer, sql.ForeignKey("author.id", ondelete="SET NULL", onupdate="CASCADE"),
                           nullable=True, default=None)
    """ An optional author for this recipe """

    cuisine_id = sql.Column(sql.Integer, sql.ForeignKey("cuisine.id", ondelete="SET NULL", onupdate="CASCADE"),
                            nullable=True, default=None)
    """ An optional cuisine """

    title = sql.Column(sql.String(255), nullable=False, index=True)
    """ The title of the recipe ("Pizza Margherita") """

    description = sql.Column(sql.Text, nullable=True, default=None)
    """ An optional description, like "My uncle's favorite recipe". Markdown """

    instructions = sql.Column(sql.Text, nullable=True, default=None)
    """ The instructions. Although None/NULL doesn't make much sense, there might be cases... Markdown """

    notes = sql.Column(sql.Text, nullable=True, default=None)
    """ Optional notes done by the user ("Tastes horrible"). Markdown """

    rating = sql.Column(sql.SmallInteger, sql.CheckConstraint("rating >=0 AND rating <=10"),
                        nullable=True, default=None)
    """ Optional rating (0 - 10, 10 is the best). If NULL/None , the recipe hasn't been rated yet """

    preparation_time = sql.Column(sql.Integer, sql.CheckConstraint("preparation_time >=0"), nullable=True,
                                  default=None)
    """ (Optional) preparation time in seconds """

    cooking_time = sql.Column(sql.Integer, sql.CheckConstraint("cooking_time >=0"), nullable=True, default=None)
    """ (optional) cook time in seconds """

    total_time = sql.Column(sql.Integer, sql.CheckConstraint("total_time >=0"), nullable=True, default=None)
    """ 
    (optional) total time. This is not necessary the same as cook_time + preparation_time, because there might
    be periods of rest where the item in questions marinates or rests
    """

    yields = sql.Column(sql.Float, sql.CheckConstraint("yields >=0"), nullable=False, default=0.0)
    """ yield/servings  """

    yield_unit_id = sql.Column(sql.Integer,
                               sql.ForeignKey("yield_unit_name.id", ondelete="SET NULL", onupdate="CASCADE"),
                               nullable=True, default=None)
    """ The yield unit name """

    url = sql.Column(sql.String(255), nullable=True, default=None)
    """ An optional url pointing to the recipe's origin """

    last_cooked = sql.Column(sql.Date, nullable=True, default=None)
    """ The user can set a date when he/she's  cooked it the last time"""

    last_modified = sql.Column(sql.Date, nullable=False)
    """ When has the recipe been created or modified?"""

    categories = relationship("Category", secondary="category_list", cascade="all", passive_deletes=True,
                              back_populates="recipes", order_by="Category.name")
    """ The categories (0..n) the recipe has """

    author = relationship("Author", back_populates="recipes")
    """ The (optional) author of the recipe """

    cuisine = relationship("Cuisine", back_populates="recipes")
    """ The optional cuisine """

    imagelist = relationship("RecipeImage", order_by="RecipeImage.position", cascade="all, delete, delete-orphan",
                             passive_deletes=False, back_populates="recipe")
    """ All images the recipe has (None to ...) """

    ingredientlist = relationship("IngredientListEntry", order_by="IngredientListEntry.position", cascade="all",
                                  passive_deletes=True, back_populates="recipe")
    """ All ingredients (IngredientListEntries) of the recipe """

    yield_unit_name = relationship("YieldUnitName", back_populates="recipes")
    """ The unit for yields """

    def __init__(self, title: str = None, description: str = None, instructions: str = None, notes: str = None,
                 rating: int = 0, preparation_time: int = None, cooking_time: int = None, total_time: int = None,
                 yields: float = 0.0, url: str = None, last_cooked: datetime.date = None,
                 last_modified: datetime.date = None):
        """
        Creates a new Recipe object

        Args:
            title (): The recipes's title ("Cupcake")
            description ():(Optional) description of the recipe
            instructions (): Instructions for the recipe
            notes (): (Optional) notes ("This recipe is *really* hot)
            rating ():  (Optional) rating in the range 0..10 (0 is horrible, 10 is best)
            preparation_time (): (Optional) time (in seconds) how  long it takes to prepare the ingredientlist
            cooking_time ():  (Optional) how long it takes (in seconds) to cook/bake/whatever the recipe
            total_time (): (Optional) total time (in seconds) , including time to let it rest
            yields (): Number of servings (or breads, glasses, whatever)
            url (): (Optional) URL of the recipe / where the recipe came from / was imported from
            last_cooked (): (Optional) the last time the recipe was cooked, If none, the recipes hasn't been cooked yet
            last_modified (): When the recipe was created/modified the last time
        """
        self.title = title
        self.description = description
        self.instructions = instructions
        self.notes = notes
        self.rating = rating
        self.preparation_time = preparation_time
        self.cooking_time = cooking_time
        self.total_time = total_time
        self.yields = yields
        self.url = url
        self.last_cooked = last_cooked

        # Just for convenience sake
        if last_modified is None:
            self.last_modified = datetime.datetime.now()
        else:
            self.last_modified = last_modified

    def __repr__(self):
        """ Doesn't make much sense if you consider the binaries, but for completeness' sake.. """
        return f"<Recipe(title={self.title}, description={self.description}, notes={self.notes}, " \
               f"rating={self.rating}, preparation_time={self.preparation_time}, cooking_time={self.cooking_time}," \
               f" total_time={self.total_time}, yields={self.yields}, url={self.url}, " \
               f"last_cooked={self.last_cooked}, last_modified={self.last_modified})> "

    def __str__(self):
        if self.rating:
            return f"{self.title} ({self.rating})"
        else:
            return self.title
