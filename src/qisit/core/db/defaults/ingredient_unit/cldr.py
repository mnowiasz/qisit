""" The CLDR units"""

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

from qisit import translate

_translate = translate

# Name, Factor, Description
DATA_MASS = (
    ("mass-gram", 1.0, _translate("IngredientUnit", "Gram (base unit)")),
    ("mass-kilogram", 1000.0, _translate("IngredientUnit", "Kilogram")),
    ("mass-milligram", 1 / 1000, _translate("IngredientUnit", "Milligram")),
    ("mass-stone", 6.35029318 * 1000.0, translate("IngredientUnit", "Stone")),
    ("mass-pound", 0.453592370 * 1000.0, _translate("IngredientUnit", "Pound")),
    ("mass-ounce", 28.349523125, _translate("IngredientUnit", "Ounce")),
    ("mass-ounce-troy", 31.1034768, _translate("IngredientUnit", "Troy Ounce")),
    ("mass-carat", 0.2, _translate("IngredientUnit", "Carat")),
)

DATA_VOLUME = (
    ("volume-milliliter", 1.0, _translate("IngredientUnit", "Millilter (base unit)")),
    ("volume-cubic-meter", 1000000.0, _translate("IngredientUnit", "Cubic meter")),
    ("volume-cubic-centimeter", 1.0, _translate("IngredientUnit", "Cubic centimter")),
    ("volume-cubic-inch", 16.3871, _translate("IngredientUnit", "Cubic inch")),
    ("volume-cubic-foot", 28316.8, _translate("IngredientUnit", "Cubic foot")),
    ("volume-hectoliter", 100 * 1000.0, _translate("IngredientUnit", "Hectoliter")),
    ("volume-liter", 1000.0, _translate("IngredientUnit", "Liter")),
    ("volume-deciliter", 100.0, _translate("IngredientUnit", "Deciliter")),
    ("volume-centiliter", 10.0, _translate("IngredientUnit", "Centiliter")),
    ("volume-pint-metric", 500.0, _translate("IngredientUnit", "Pint (metric)")),
    ("volume-cup-metric", 250.0, _translate("IngredientUnit", "Cup (metric)")),
    ("volume-bushel", 36.36872 * 1000.0, _translate("IngredientUnit", "Bushel")),
    ("volume-gallon", 3.785411784 * 1000.0, _translate("IngredientUnit", "Gallon")),
    ("volume-gallon-imperial", 4.54609 * 1000.0, _translate("IngredientUnit", "Gallon (Imperial)")),
    ("volume-quart", 1.1365 * 1000.0, _translate("IngredientUnit", "Quart")),
    ("volume-pint", 568.26125, _translate("IngredientUnit", "Pint")),
    ("volume-cup", 236.5882365, _translate("IngredientUnit", "Cup")),
    ("volume-fluid-ounce", 29.5735295625, _translate("IngredientUnit", "Fluid ounce")),
    ("volume-fluid-ounce-imperial", 28.4130625, _translate("IngredientUnit", "Fluid ounce (Imperial)")),
    ("volume-tablespoon", 15.0, _translate("IngredientUnit", "Tablespoon")),
    ("volume-teaspoon", 5.0, _translate("IngredientUnit", "Teaspoon")),
    ("volume-barrel", 119.0 * 1000, _translate("IngredientUnit", "Barrel"))
)
