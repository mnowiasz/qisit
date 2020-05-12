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
from sqlalchemy.orm import relationship, deferred
from qisit.core import db
from .recipe import Recipe


class RecipeImage(db.Base):
    """ A list of (optional) images for a recipe"""
    __tablename__ = "recipe_image"
    __table_args__ = (sql.UniqueConstraint('recipe_id', 'position'),)

    main_image_pos = 0
    """ The main image """

    id = sql.Column(sql.Integer, primary_key=True)
    """ The primary key """

    recipe_id = sql.Column(sql.Integer, sql.ForeignKey("recipe.id", ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False)
    """ The recipe the image/thumb belongs to """

    position = sql.Column(sql.Integer, nullable=False)
    """ The position in the recipe's image list. The main image is at main_image_pos """

    image = deferred(sql.Column(sql.LargeBinary, nullable=False))
    """ The image in full size """

    thumbnail = deferred(sql.Column(sql.LargeBinary, nullable=False))
    """ The thumbnail for the image"""

    description = sql.Column(sql.String(255), nullable=True, default=None)
    """ An (optional) description for the image """

    recipe = relationship("Recipe", back_populates="imagelist")

    def __init__(self, recipe: Recipe, position: int, image, thumbnail, description: str = None):
        """
        Initializes a image

        Args:
            recipe (): The recipe
            position (): Position in recipe's image list
            image (): The image
            thumbnail (): The thumbnail
            description (): The (optional) title of the image
        """
        self.recipe_id = recipe.id
        self.position = position
        self.image = image
        self.thumbnail = thumbnail
        self.description = description

    def __str__(self):
        return self.description
