""" Import Gourmet.db """

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

import time
from datetime import datetime

from sqlalchemy import orm

import qisit.importer.gourmetdb.data as gdata
from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify


class ImportGourmet(object):

    def __init__(self, gourmet: orm.session, qisit: orm.session):
        super()
        self._gourmet = gourmet
        self._qisit = qisit
        self._is_aborted = False
        self._count_recipes = 0
        self._duplicate_recipes = 0
        self._imported_recipes = 0
        self._imported_ingredient_units = 0

        self._translate = translate

    def abort(self):
        """
        Aborts the import process. Makes only sense when running in a thread or something similar

        Returns:
        """

        self._is_aborted = True

    def is_aborted(self):
        return self._is_aborted

    def show_info(self, output: str):
        print(output)

    def show_progress(self, current: int, upper: int, message: str, title: str = None):
        """
        Displays (probably in a GUI) progress of the import process

        Args:
            current (): The current number (x / upper)
            upper ():  The number of items to process
            message (): What to display (The title of the recipe, what ever)
            title ():  What the process currently does ("Importing Recipes")

        Returns:
            None
        """
        print(f"{current}/{upper}: {message}")

    def __check_gourmet_version(self):
        """

        Returns:
            None
        Raises:
            ValueError if the db version is older (or newer, which is highly impropable) than the supported version
        """

        __error = "Unsupported version of Gourmet's db"

        gourmet_info = self._gourmet.query(gdata.Info).first()

        # Currently all versions between 0.14.7 and 0.17.4 are supported
        if gourmet_info.version_super > 0:
            raise ValueError(__error)

        if gourmet_info.version_major not in range(14, 17 + 1):
            raise ValueError(__error)

        if gourmet_info.version_major == 14 and gourmet_info.version_minor < 7:
            raise ValueError(__error)

    def __find_duplicate(self, gourmet_recipe: gdata.Recipe) -> data.Recipe:
        """
        Try to find if the recipe to be imported already exist in the database. This is unreliable.

        Args:
            gourmet_recipe (): The recipe to import

        Returns:
            None if the recipe hasn't been found, Qisit's recipe (if it looks like a duplicate)
        """

        # Warning: This is not reliable, no matter how many sophisticated tests one applies. Gourmet tries to
        # solve this problem by storing hash values (for recipes and ingredient), but this isn't very reliable, either -
        # in the end the user has to take care not to import the same recipe twice. And even if he does, he can just
        # delete the duplicates

        # Current criteria: titles and  last_modified must be the same

        return self._qisit.query(data.Recipe).filter(data.Recipe.title == gourmet_recipe.title,
                                                     data.Recipe.last_modified == datetime.fromtimestamp(
                                                         gourmet_recipe.last_modified).date()).first()

    def __import_recipe(self, gourmet_recipe: gdata.Recipe) -> data.Recipe:
        """
        Convert / Import a Gourmet recipe into Qisit (basic data like title, categories, author..)

        Args:
            gourmet_recipe (): The recipe

        Returns:
            New Qisit's recipe
        """
        # 1.) Fill out all the recipes data

        # Gourmet uses 0 in rating to mark the recipes as unrated. Qisit uses None for this purpose, allowing
        # 0 to be a valid rating
        rating = gourmet_recipe.rating
        if rating == 0:
            rating = None

        # Empty links are stored as "" in Gourmet
        url = nullify(gourmet_recipe.link)

        last_modified = datetime.fromtimestamp(gourmet_recipe.last_modified).date()

        qisit_recipe = data.Recipe(title=gourmet_recipe.title, description=gourmet_recipe.description,
                                   instructions=nullify(gourmet_recipe.instructions),
                                   notes=nullify(gourmet_recipe.modifications), rating=rating,
                                   preparation_time=gourmet_recipe.preptime, cooking_time=gourmet_recipe.cooktime,
                                   yields=gourmet_recipe.yields, url=url, last_modified=last_modified)
        self._qisit.add(qisit_recipe)

        # 2.) Yield unit
        gourmet_yield_unit = nullify(gourmet_recipe.yield_unit)
        if gourmet_yield_unit is not None:
            qisit_recipe.yield_unit_name = data.YieldUnitName.get_or_add_yield_unit_name(session_=self._qisit,
                                                                                         name=gourmet_yield_unit)

        # 3.) Author
        gourmet_source = nullify(gourmet_recipe.source)
        if gourmet_source:
            qisit_recipe.author = data.Author.get_or_add_author(self._qisit, gourmet_source)

        # 4.) Cuisine
        gourmet_cuisine = nullify(gourmet_recipe.cuisine)
        if gourmet_cuisine:
            qisit_recipe.cuisine = data.Cuisine.get_or_add_cusine(self._qisit, gourmet_cuisine)

        # 5.) Categories
        # Gourmet really *does* support multiple categories, although this is rather well hidden in the UI
        category_list = []
        gourmet_category_list = gourmet_recipe.categories

        if gourmet_category_list:
            for gourmet_category in gourmet_category_list:
                category_list.append(nullify(gourmet_category.category))

        for gourmet_item in category_list:
            if gourmet_item:
                qisit_category = data.Category.get_or_add_category(self._qisit, gourmet_item)
                qisit_recipe.categories.append(qisit_category)

        self._qisit.merge(qisit_recipe)
        return qisit_recipe

    def __import_ingredients(self, gourmet_ingredient: gdata.Ingredients, qisit_recipe: data.Recipe):
        """
        Import an ingredient into a recipe

        Args:
            gourmet_ingredient (): Gourmet's ingredient
            qisit_recipe (): The recipe to import to

        Returns:

        """
        _translate = self._translate

        # Test if the ingredient is part of a group
        gourmet_inggroup = nullify(gourmet_ingredient.inggroup)
        group_item = None

        if gourmet_inggroup:
            # The ingredient is part of the group stored in gourmet_inggroup
            group = data.Ingredient.get_or_add_ingredient(self._qisit, gourmet_inggroup, is_group=True)

            # Find out if there's already a group with the name in the ingredient list. Note: assumes that there's
            # only one group (or none) with the name stored in gourmet_inggroup. This is a safe assumption, two
            # (or more) groups of ingredients with the same name make no sense, although Qisit's db design would
            # theoretically allow this (there's no way to prevent it with a simple CHECK constraint)
            group_item = self._qisit.query(data.IngredientListEntry).filter(
                data.IngredientListEntry.recipe == qisit_recipe,
                data.IngredientListEntry.ingredient == group).first()
            if not group_item:
                # New group for the recipe
                group_position = data.IngredientListEntry.get_position_for_new_group(self._qisit, qisit_recipe)
                group_item = data.IngredientListEntry(recipe=qisit_recipe, ingredient=group,
                                                      unit=data.IngredientUnit.unit_group, position=group_position)
                self._qisit.add(group_item)
                self._qisit.merge(group_item)

        # Convert the ingredient data
        qisit_amount = gourmet_ingredient.amount
        qisit_range_amount = gourmet_ingredient.rangeamount

        # For an empty (or None/NULL) unit there's a special unit/unit_name: the base unit, singular ""
        if not gourmet_ingredient.unit:
            gourmet_unit_name = ""
        else:
            gourmet_unit_name = gourmet_ingredient.unit.strip()

        qisit_ingredient_unit = None

        if gourmet_unit_name in data.IngredientUnit.unit_dict:
            qisit_ingredient_unit = data.IngredientUnit.unit_dict[gourmet_unit_name]
        else:
            # A (yet) unknown unit. Well, time to take a guess - volume? mass? quantity? Probably unspecific
            qisit_ingredient_unit = data.IngredientUnit(type_=data.IngredientUnit.UnitType.UNSPECIFIC,
                                                        name=gourmet_unit_name, factor=None, cldr=False,
                                                        description=_translate("ImportGourmet",
                                                                               f"{gourmet_unit_name} (imported)"))
            self._qisit.add(qisit_ingredient_unit)
            self._qisit.merge(qisit_ingredient_unit)
            data.IngredientUnit.unit_dict[gourmet_unit_name] = qisit_ingredient_unit
            self._imported_ingredient_units += 1

        qisit_name = nullify(gourmet_ingredient.item)

        gourmet_ingkey = nullify(gourmet_ingredient.ingkey)

        if gourmet_ingkey is None:
            # Such an ingredient shouldn't be in the database. Unfortunately Gourmet doesn't check input
            # very thoroughly...
            if qisit_name:
                # This shouldn't be possible, but better safe than sorry
                gourmet_ingkey = qisit_name
            else:
                return

        group_position = None
        if group_item is not None:
            group_position = group_item.position
        qisit_ingredient = data.Ingredient.get_or_add_ingredient(self._qisit, gourmet_ingkey)
        qisit_position = data.IngredientListEntry.get_position_for_ingredient(self._qisit, recipe=qisit_recipe,
                                                                              parent=group_position)
        # Time to put everything together
        qisit_ingredient_list_entry = data.IngredientListEntry(recipe=qisit_recipe, unit=qisit_ingredient_unit,
                                                               ingredient=qisit_ingredient, amount=qisit_amount,
                                                               range_amount=qisit_range_amount, name=qisit_name,
                                                               optional=gourmet_ingredient.optional,
                                                               position=qisit_position)
        self._qisit.add(qisit_ingredient_list_entry)
        self._qisit.merge(qisit_ingredient_list_entry)

    def import_gourmet(self, check_duplicates: bool = False) -> dict:
        """
        Imports a gourmet db into a qisit db
        Args:

        Returns:
            A dictionary of errors (recipe title: error message) or None if everything went well

        """
        _translate = self._translate

        start = time.time()
        self.__check_gourmet_version()

        number_of_recipes = self._gourmet.query(gdata.Recipe).count()
        self._count_recipes = 0
        self._imported_recipes = 0
        self._imported_ingredient_units = 0
        self._is_aborted = False

        error_dict = {}

        for gourmet_recipe in self._gourmet.query(gdata.Recipe).order_by(gdata.Recipe.title):
            if self.is_aborted():
                break

            self._count_recipes += 1
            self.show_progress(current=self._count_recipes, upper=number_of_recipes,
                               message=_translate("ImportGourmet", f"importing {gourmet_recipe.title}"))
            try:
                with self._qisit.begin_nested():
                    if check_duplicates:
                        if self.__find_duplicate(gourmet_recipe):
                            self._duplicate_recipes += 1
                            continue

                    qisit_recipe = self.__import_recipe(gourmet_recipe)

                    # Images
                    if gourmet_recipe.image:
                        new_image = data.RecipeImage(recipe=qisit_recipe, image=gourmet_recipe.image,
                                                     thumbnail=gourmet_recipe.thumb,
                                                     position=data.RecipeImage.main_image_pos)
                        self._qisit.add(new_image)
                        self._qisit.merge(new_image)

                    # 4.) Now the ingredient list
                    for gourmet_ingredient in gourmet_recipe.ingredients:
                        self.__import_ingredients(gourmet_ingredient=gourmet_ingredient, qisit_recipe=qisit_recipe)

                    self._imported_recipes += 1
            except Exception as e:
                error_dict[gourmet_recipe.title] = str(e)

        if self.is_aborted():
            self._qisit.rollback()
            if self._imported_ingredient_units > 0:
                data.IngredientUnit.update_unit_dict(self._qisit)
        else:
            self._qisit.commit()

        number_of_errors = len(error_dict)
        self.show_info(_translate("ImportGourmet",
                                  f"Imported {self._imported_recipes} recipes of {number_of_recipes}"
                                  f" ({self._duplicate_recipes} duplicates, {number_of_errors} errors), "
                                  f"added {self._imported_ingredient_units} new ingredient units.\n"
                                  f"Took {(time.time() - start):.2f} seconds"))

        return error_dict
