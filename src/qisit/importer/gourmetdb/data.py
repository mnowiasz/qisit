""" The ORM definitions of Gourmet's database """

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

from qisit.importer import gourmetdb


class Recipe(gourmetdb.GourmetBase):
    """ Gourmet's recipe table  -> Recipe """
    __tablename__ = "recipe"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key. Won't be used/converted """

    title = sql.Column(sql.String)
    """ The recipe's title ("Vindaloo") -> Recipe.title """

    instructions = sql.Column(sql.Text)
    """ Instructions -> Recipe.instructions """

    modifications = sql.Column(sql.Text)
    """ Modifications/Comments -> Recipe.notes (name changed to reflect the purpose)"""

    cuisine = sql.Column(sql.String)
    """  Cuisine (Indian, German,...) -> Cuisine.name """

    rating = sql.Column(sql.Integer)
    """ Rating (1..10) -> Recipe.rating (0..10, nullable) """

    description = sql.Column(sql.Text)
    """ Description. Not used by Gourmet, but used in Recipe.description """

    source = sql.Column(sql.String)
    """ Source. Now a separate Table and renamed to author -> Author.name """

    preptime = sql.Column(sql.Integer)
    """ Preparation time -> Recipe.preparation_time (more readable name) """

    cooktime = sql.Column(sql.Integer)
    """ Cook time -> Recipe.cooking_time (more readable name) """

    servings = sql.Column(sql.Float)
    """ Legacy column, not used anymore by Gourmet """

    yields = sql.Column(sql.Float)
    """ Yields ->  Recipe.yields """

    yield_unit = sql.Column(sql.String)
    """ The unit for yields -> YieldUnitName.name """

    image = sql.Column(sql.LargeBinary)
    """ The recipes image -> RecipeImage.image (first on Recipes.ImageList) """

    thumb = sql.Column(sql.LargeBinary)
    """ Thumbnail -> RecipeImage.thumbnail (more readable name) (first on Recipes.ImageList)"""

    deleted = sql.Column(sql.Boolean)
    """ Recipe is in the trash can. Ignored/not imported """

    recipe_hash = sql.Column(sql.String)
    """ Hash (for determining duplicates). Ignored/not imported """

    ingredient_hash = sql.Column(sql.String)
    """ Ingredient hash (for determining duplicates). Ignored/not imported """

    link = sql.Column(sql.String)
    """ URL of the recipe -> Recipe.url """

    last_modified = sql.Column(sql.Integer)
    """ Last modified/created -> Recipe.last_modified"""

    ingredients = relationship("Ingredients", order_by="Ingredients.position", foreign_keys="Ingredients.recipe_id")
    categories = relationship("Categories")


class Categories(gourmetdb.GourmetBase):
    """ A category belonging to a recipe -> Category """
    __tablename__ = "categories"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key. Won't be used/converted """

    recipe_id = sql.Column(sql.Integer, sql.ForeignKey("recipe.id"))
    """ The recipe the category belongs to """

    category = sql.Column(sql.String)
    """ The title of the category -> Category.name """

    recipes = relationship("Recipe", back_populates="categories", order_by="Categories.category")


class Ingredients(gourmetdb.GourmetBase):
    """
    Ingredient list for a recipe. Spit into a couple of  tables:
    Ingredient, IngredientListEntry, Unit, and UnitName
    """

    __tablename__ = "ingredients"

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary key. Not used/converted """

    recipe_id = sql.Column(sql.Integer, sql.ForeignKey("recipe.id"))
    """ The recipe the category belongs to. Converted into IngredientListEntry.recipe_id """

    refid = sql.Column(sql.Integer, sql.ForeignKey("recipe.id"))
    """ 
     If set the ingredient is another recipe. Not used/ignored, there are better (planned)
     ways to create menus 
    """

    unit = sql.Column(sql.String)
    """ The unit for the amount. Converted into Unit.id and UnitName.name """

    amount = sql.Column(sql.Float)
    """ Amount of the unit -> IngredientListEntry.amount """

    rangeamount = sql.Column(sql.Float)
    """  Optional range amount -> IngredientListEntry.range_amount """

    item = sql.Column(sql.String)
    """ The description of the Item -> IngredientListEntry.name """

    ingkey = sql.Column(sql.String)
    """ The ingredient "key". Converted into Ingredient.name """

    optional = sql.Column(sql.Boolean)
    """ The ingredient is optional -> IngredientListEntry.optional """

    shopoptional = sql.Column(sql.Boolean)
    """ The ingredient is an optional item on the shopping list. Ingored """

    inggroup = sql.Column(sql.String)
    """  The group the item belongs to. Converted into Ingredient.name and  IngredientListEntry.position """

    position = sql.Column(sql.Integer)
    """ The position on the ingredient list. Converted into IngredientListEntry.position"""

    deleted = sql.Column(sql.Boolean)
    """ The item has been deleted/put into trash. Ignored"""

    recipe = relationship("Recipe", back_populates="ingredients", foreign_keys=recipe_id)


class Info(gourmetdb.GourmetBase):
    """ Meta information. Not converted, but used in the import process """

    __tablename__ = "info"

    version_super = sql.Column(sql.Integer)
    """ 0.17.4 -> version_super = 0"""

    version_major = sql.Column(sql.Integer)
    """ 0.17.4 -> version major = 17 """

    version_minor = sql.Column(sql.Integer)
    """ 0.17.4 -> version minor = 4 """

    rowid = sql.Column(sql.Integer, primary_key=True)
    """ Primary key. Makes no sense at all here """
