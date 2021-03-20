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
from babel.numbers import format_decimal
from babel.units import format_unit
from sqlalchemy import orm

from qisit.core import db, default_locale
from .ingredient import Ingredient
from .ingredient_unit import IngredientUnit
from .recipe import Recipe


class IngredientListEntry(db.Base):
    """ The list of a recipe's ingredientlist """
    __tablename__ = "ingredient_list_entry"
    __table_args__ = (sql.UniqueConstraint("recipe_id", "position"),)

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary Key """

    recipe_id = sql.Column(sql.Integer, sql.ForeignKey("recipe.id", ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False)
    """ The recipe the ingredient belongs to """

    amount = sql.Column(sql.Float,
                        sql.CheckConstraint("(amount >0.0) AND (amount IS NOT NULL OR range_amount IS NULL)"),
                        nullable=True, default=None)
    """ 
    The amount of the ingredient (0.125 l wine, 3 pieces of chocolate). If None/NULL, the user 
    hasn't entered a value - there might be no meaningful value for the unit, say something like "some salt"

    The second part of the CHECK constraints needs some explanation: It's to ensure that the range can't be NOT NULL 
    if the amount is null. If the amount is NULL and the range is NOT NULL the check will fail. In all other cases 
    (NULL + NULL, NOT NULL + NULL, NOT NULL + NOT NULL) the check will succeed
    """

    range_amount = sql.Column(sql.Float, sql.CheckConstraint(
        "range_amount IS NULL OR (range_amount >0.0 AND range_amount > amount)"),
                              nullable=True, default=None)
    """ 
    In case of ranges like 1-2 tomatoes, it's the second range value
    """

    unit_id = sql.Column(sql.Integer, sql.ForeignKey("ingredient_unit.id"), nullable=False)
    """ The unit the of amount (or range) """

    name = sql.Column(sql.String(255), nullable=True)
    """ 
    The (possible) verbose of the ingredient, for example "green pepper, chopped". If NULL/None, the ingredient_id's
    name will be taken.
    """

    ingredient_id = sql.Column(sql.Integer, sql.ForeignKey("ingredient.id"), nullable=False)
    """ 
    Reference to ingredient.  Non NULL / no Cascade: A "normal" ingredient wouldn't be a problem automatically
    deleting all entries in the ingredient_lists - although it might make no sense deleting (for example) oregano
    from all recipes), but if the ingredient would be a group, deleting it involves more work:
    The position of all items belonging to the group would need to be adjusted (or deleted)
    """

    optional = sql.Column(sql.Boolean, nullable=False, default=False)
    """ If the ingredient in question is optional """

    position = sql.Column(sql.Integer, sql.CheckConstraint("(position >=0 and position <=99999999) or position < 0"),
                          nullable=False)
    """ 
    The position of the ingredient. This is used to let the user sort the ingredientlist. It's also used as an encoding:

    gg|ii|oo|aa|

    * gg = group (1..99)
    * ii = ingredient (1..99)
    * oo = alternative ("or") 1..99
    * aa = alternative groups ("and").

    For example (a crazy one, just to demonstrate)
    For the sauce: <-- group
       500 ml milk <-- ingredient
       or 500 ml cream <--- alternative
       or 250 gr powdered milk <--- alternative 
          AND 250 ml water <--- alternative group
    
    The second term of the check constraint is used for temporarily renumbering the list - otherwise the unique
    constraint would fire up
    """
    ingredient = orm.relationship("Ingredient", back_populates="items")
    """ The (normalized) ingredient """

    recipe = orm.relationship("Recipe", back_populates="ingredientlist")
    """ The recipe"""

    unit = orm.relationship("IngredientUnit", back_populates="ingredientlist")
    """ The unit for the ingredient list entry"""

    GROUP_FACTOR = 1000000
    """ The group part of a position (0..98000000) """

    GROUP_INGREDIENT_FACTOR = 10000
    """ The (standard) ingredient part of a position (xx01yyzz - xx99yyzz)"""

    GROUP_INGREDIENT_ALTERNATIVE_FACTOR = 100
    """ The alternative ingredient part of a position (xxyy01zz - xxyy99zz"""

    GROUP_GLOBAL = 99
    """ A special group - ungrouped ingredientlist are part of this invisible group"""

    MAX_ENTRIES = 99
    """ Maxmimum number of entries per level """

    @classmethod
    def format_amount_string(cls, amount: float, range_amount: float, factor=1.0, locale=default_locale) -> str:
        """
        Convenience method for formatting amounts/range amounts

        Args:
            amount ():
            range_amount ():
            factor: The factor

        Returns:
            formatted string
        """

        if amount is None:
            return ""

        if range_amount is None:
            return format_decimal(amount * factor, locale=locale)
        else:
            return f"{format_decimal(amount * factor, locale=locale)} - {format_decimal(range_amount * factor, locale=locale)}"

    @classmethod
    def get_position_for_ingredient(cls, session_: sql.orm.session, recipe: Recipe, parent=None) -> int:
        """
        Calculates the next position for an ingredient in a group

        Args:
            session_ (): The session
            recipe (): The recipe
            parent (): The parent. If None, the global group will be used

        Returns:
            The position suitable for a new ingredient or -1 if all positions under the groups are full

        Raises:
            ValueError if the group doesn't belong to the recipe
        """

        position = -1
        lower_bound = 0
        upper_bound = 0
        increment = 0

        if parent is None:
            # Global group
            group_position = cls.GROUP_GLOBAL * cls.GROUP_FACTOR
            lower_bound = group_position
            upper_bound = lower_bound + cls.MAX_ENTRIES * cls.GROUP_INGREDIENT_FACTOR
            increment = cls.GROUP_INGREDIENT_FACTOR
        else:
            # Let's see what we got here

            if IngredientListEntry.is_group(parent):
                group_position = parent // cls.GROUP_FACTOR
                # Valid positions are now >group_position.010000 and < group.position.990000

                lower_bound = group_position * cls.GROUP_FACTOR
                upper_bound = lower_bound + cls.MAX_ENTRIES * cls.GROUP_INGREDIENT_FACTOR
                increment = cls.GROUP_INGREDIENT_FACTOR
            elif IngredientListEntry.is_alternative_grouped(parent):
                # It's an alternative grouped - "AND" - ingredient. These ingredients cannot have a level below them

                raise ValueError(f"Illegal position: {parent}")
            elif IngredientListEntry.is_alternative(parent):
                # An alternative - "or" ingredient. Valid Positions are now ggiipp.01-99
                lower_bound = (parent // cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR) \
                              * cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR
                upper_bound = lower_bound + cls.MAX_ENTRIES
                increment = 1
            else:
                # Ingredient
                lower_bound = (parent // cls.GROUP_INGREDIENT_FACTOR) * cls.GROUP_INGREDIENT_FACTOR
                upper_bound = lower_bound + cls.MAX_ENTRIES * cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR
                increment = cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR

        largest_ingredient_position = session_.query(sql.func.max(IngredientListEntry.position)).filter(
            IngredientListEntry.recipe == recipe, IngredientListEntry.position >= lower_bound,
            IngredientListEntry.position <= upper_bound).scalar()

        if largest_ingredient_position is None:
            # No ingredient has been added to the global group yet
            position = lower_bound + 1 * increment
        else:
            # There has to be at least one ingredient
            position = largest_ingredient_position + 1 * increment

            # Cut off trailing positions
            position = position // increment * increment

            # Have we reached the end of the possible positions?
            if position > upper_bound:
                position = -1
        return position

    @classmethod
    def get_position_for_new_group(cls, session_: sql.orm.session, recipe: Recipe) -> int:
        """
        Calculates the next position for a new group

        Args:
            session_ (): The DB session_
            recipe (): The recipe in question

        Returns:
            The position suitable for a new group or -1 if there are already 98 groups (unrealistic)
        """

        position = -1
        the_filter = (
            IngredientListEntry.recipe == recipe, IngredientListEntry.position < cls.GROUP_GLOBAL * cls.GROUP_FACTOR)

        # Find out if there's already a group in the specific ingredient list
        number_of_groups = session_.query(IngredientListEntry).filter(*the_filter).count()

        if number_of_groups > 0:
            largest_group_id = session_.query(sql.func.max(IngredientListEntry.position)).filter(*the_filter).scalar()

            # Isolate the group ID
            group_id = largest_group_id // cls.GROUP_FACTOR

            next_group_id = group_id + 1
            if next_group_id >= cls.GROUP_GLOBAL:
                return -1
            position = next_group_id * cls.GROUP_FACTOR
        else:
            # There's no group yet - so this is the first group, counting begins at 0
            position = 0 * cls.GROUP_FACTOR

        return position

    @classmethod
    def is_group(cls, position: int) -> bool:
        """
        Convenience method. Does the position describe a group?

        Args:
            position ():

        Returns:
            True, if it's a group
        """
        return (position % cls.GROUP_FACTOR) == 0

    @classmethod
    def is_alternative(cls, position: int) -> bool:
        """
        Convenience method. Is the position an alternative ("or") ingredient?

        Args:
            position ():

        Returns:

        """
        return position % cls.GROUP_INGREDIENT_FACTOR != 0 and not cls.is_alternative_grouped(position)

    @classmethod
    def is_alternative_grouped(cls, position: int) -> bool:
        """
        Convenience method. Does the position indicate an alternative grouped ("and") item?

        Args:
            position ():

        Returns:

        """
        return position % cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR != 0

    @classmethod
    def item_group(cls, position: int):
        """
        Convenience method. Returns the group number of the item

        Args:
            position (): The item's position

        Returns:
            The group
        """
        return (position // cls.GROUP_FACTOR) * cls.GROUP_FACTOR

    @classmethod
    def item_parent(cls, position: int) -> int:
        """
        Convenience method. Calculates the parent position of the position

        Args:
            position ():

        Returns:
            The parent position or None if the item hasn't got a parent
        """

        if cls.is_group(position):
            return None

        if cls.is_alternative_grouped(position):
            return (position // cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR) * cls.GROUP_INGREDIENT_ALTERNATIVE_FACTOR

        if cls.is_alternative(position):
            return (position // cls.GROUP_INGREDIENT_FACTOR) * cls.GROUP_INGREDIENT_FACTOR
        else:
            return cls.item_group(position)

    def __init__(self, recipe: Recipe, unit: IngredientUnit, ingredient: Ingredient, amount: float = None,
                 range_amount: float = None, name: str = None, optional: bool = False,
                 position: int = 0):
        """
        Add a (possible new) ingredient to the recipe's ingredient list.

        Args:
            recipe (): The recipe the list belongs to
            unit (): The unit of the amount.
            ingredient (): The "normalized" ingredient key, like "pepper, red"
            amount (): The amount (or None/NULL) for "undefined" ingredient_unit like "a bit", "some"..)
            range_amount (): For amounts like "1-1 1/2 apples". 1 1/2 would be the range amount, 1 the amount
            name (): The name of the ingredient like "red peppers, diced". If None/NULL, the ingredient's name will be used
            optional (): The ingredient is optional
            position ():  The position of the ingredient, so the user can sort the list. It's also used as code
        """

        self.recipe_id = recipe.id
        self.unit_id = unit.id

        self.ingredient_id = ingredient.id
        self.amount = amount
        self.range_amount = range_amount
        self.name = name
        self.optional = optional
        self.position = position

    def __str__(self):
        return self.name

    def amount_string(self, factor=1.0) -> str:
        """
        Returns a formatted - in the user's locale - string containing the amount and the unit

        Args:
            factor: The factor

        Returns:
            The formatted amount string
        """

        # CLDR = international valid units which are translated into the user's local
        if self.unit.cldr:
            if self.amount and self.range_amount is None:
                return format_unit(self.amount * factor, self.unit.name, locale=default_locale)
            else:
                return format_unit(self.format_amount_string(self.amount, self.range_amount, factor), self.unit.name,
                                   locale=default_locale)
        else:
            if self.amount:
                return f"{self.format_amount_string(self.amount, self.range_amount, factor)} {self.unit.name}"
            else:
                # Some generic units, like "some" where an amount wouldn't make much sense
                return self.unit.name

