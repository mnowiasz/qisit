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

from enum import IntEnum

import sqlalchemy as sql
from babel.units import get_unit_name, UnknownUnitError
from sqlalchemy import orm
from sqlalchemy.dialects import mysql

from qisit.core import db


# "AmountUnit" probably would have been a better name, but there's no sense in renaming the class/table, issueing
# database updates and so on.
class IngredientUnit(db.Base):
    """ A unit for an ingredient  (ml, kg, oz) """

    class UnitType(IntEnum):
        """ The type of the unit """
        QUANTITY = 0
        """ A quantity (dozen, pair, triple...) """

        MASS = 1
        """ Mass (gram, kg, oz, ...) """

        VOLUME = 2
        """ Volume (ml, tsp, pint, ...) """

        UNSPECIFIC = 3
        """ A unit that cant't be defined by itself and makes only sense in combination with an ingredient. For 
        example, 'small can', 'twig' (tyme, rosemary,...) 'cm' (!) (cinnamon), 'some'... """

        GROUP = 4
        """ The  'unit' is group/header . Since unit can't be None/NULL in ingredient_list_entry, this is a kind of 
        workaround """

    __tablename__ = "ingredient_unit"

    # TODO: Replace this by using the base units dictionary
    unit_group = None
    """ The pseudo unit a group has. units can't be NULL/None, hence this construct """

    id = sql.Column(sql.Integer, primary_key=True)
    """ Primary Key """

    type_ = sql.Column(sql.SmallInteger,
                       sql.CheckConstraint(f"type_ >={UnitType.QUANTITY} and type_ <={UnitType.GROUP}"),
                       nullable=False)
    """ The type of the unit - mass, volume, quantity (UnitType.QUANTITY, ...) """

    name = sql.Column(sql.String(80).with_variant(mysql.VARCHAR(80, binary=True), 'mysql'), nullable=False, unique=True)
    """ 
    The name of the unit - either CLDR data like 'volume-liter' or a custom unit like 'dozen'. Since MySQL in
    it's infinite wisdom ignores case when not having a binary collation the variant part compensates for MySQL's
    defective behaviour (sqlite, PostgreSQL do it correctly). Otherwise 'l' and 'L' would be the same to MySQL,
    causing constraint failures when importing 
    """

    cldr = sql.Column(sql.Boolean, nullable=False)
    """ The name references a CLDR unit. If false, it's a custom unit """

    factor = sql.Column(sql.Float, nullable=True)
    """ 
    The factor regarding to the *base* value (gr, ml, unit). For example, the factor for a dozen would be 12,
    the factor for a kg 1000. If None/NULL, the factor is depending on the ingredient: A small can of corn might
    weight less than a small can of tomatoes
    """

    description = sql.Column(sql.Text, nullable=True, default=None)
    """ An optional description for the unit ("US Gallon") """

    unit_dict = {}
    """ 
    A dictionary of unit (strings) to IngredientUnit. This dictionary will be a mixture of dynamically created
    items (the units in the user's local) and static items (the custom items stored in the database) 
    """

    base_units = {}
    """" The base unit for each type (apart from unspecific) """

    ingredientlist = orm.relationship("IngredientListEntry", order_by="IngredientListEntry.name")

    recipes = orm.relationship("Recipe", secondary="ingredient_list_entry",
                               primaryjoin="IngredientUnit.id == IngredientListEntry.unit_id",
                               secondaryjoin="Recipe.id == IngredientListEntry.recipe_id", viewonly=True,
                               order_by="Recipe.title")

    @classmethod
    def get_or_add_ingredient_unit_name(cls, session_: sql.orm.session, name: str,
                                        type_: UnitType = UnitType.QUANTITY):
        """
        Get an existing ingredient unit name  or - if not existing - create a new one and add it to the database

        Args:
            session_ (): The database session
            name (): The name/title of the ingredient unit

        Returns:
            An ingredient unit  object (either preexisting or created)

        """

        new_unit = db.get_or_add_item(session_=session_, table=IngredientUnit, name=name, type_=type_)
        IngredientUnit.update_unit_dict(session_)
        return new_unit

    @classmethod
    def update_unit_dict(cls, session: orm.Session):
        """
        Create/update the unit dictionary dynamically

        Args:
            session (db session):

        Returns:

        """

        cls.unit_dict.clear()
        ingredient_units = session.query(IngredientUnit).all()

        for ingredient_unit in ingredient_units:
            if ingredient_unit.cldr:
                # CLDR. Select the units from the current locale
                for length in ("short", "long"):
                    try:
                        unit_name = get_unit_name(ingredient_unit.name, length=length)
                        cls.unit_dict[unit_name] = ingredient_unit
                    except UnknownUnitError:
                        # This should not happen...
                        pass
            else:
                # Custom unit
                if ingredient_unit.type_ == cls.UnitType.GROUP:
                    # Special case: The group unit exists only once and shouldn't be used in the text fields
                    cls.unit_group = ingredient_unit
                else:
                    unit_name = ingredient_unit.name
                    if unit_name not in cls.unit_dict:
                        cls.unit_dict[unit_name] = ingredient_unit

                    # If unit_name is already in the dictionary: There's a clash between the official CLDR units
                    # and a custom one. CLDR units - the "official", international ones - should take precedence.

        # There's a bug currently in the CLDR data - "g" is not a short unit name for "Gram".
        gram_unit = session.query(IngredientUnit).filter(IngredientUnit.name == "mass-gram").first()
        cls.unit_dict["g"] = gram_unit

        # Setup the base units

        cls.base_units[cls.UnitType.MASS] = gram_unit
        cls.base_units[cls.UnitType.VOLUME] = session.query(IngredientUnit).filter(
            IngredientUnit.name == "volume-milliliter").first()
        cls.base_units[cls.UnitType.QUANTITY] = session.query(IngredientUnit).filter(IngredientUnit.name == "").first()
        cls.base_units[cls.UnitType.GROUP] = cls.unit_group

    def __init__(self, name: str, type_: UnitType = UnitType.QUANTITY, cldr: bool = False, factor=None,
                 description: str = None):
        """
        A new unit

        Args:
            type_ (): The type of the unit (UNIT_MASS.. UNIT_CATEGORY)
            name (): The name of the unit ("dozen", "mass-gram"
            cldr (): The name is a reference to a CLDR unit
            factor (): The factor regarding the base unit (kg would be 1000). If none the factor is variable
            description (): Optional description of the unit
        """

        self.type_ = type_
        self.name = name
        self.cldr = cldr
        self.factor = factor
        self.description = description

    def __repr__(self):
        return f"<IngredientUnit(type_={self.type_}, name={self.name}, cldr={self.cldr}, factor={self.factor}, " \
               f"description={self.description})>"

    def __str__(self):
        return self.name

    def unit_string(self):
        """
        Returns the unit string (if a CLDR, in the user's locale)

        Returns:
            The string
        """

        if self.cldr:
            return get_unit_name(self.name)
        else:
            return self.name
