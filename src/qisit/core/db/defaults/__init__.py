""" Insert some default values into a (newly created/emptied) database. The values are in localized
files because one unit in one language ("liter") might have no plural form in another ("Liter", Germany, both
singular and plural). This would make translation.. awkward and difficult. Furthermore ingredient_unit might differ
(for example, "Pound" - 500 gr (metric) or 400something) """

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

import importlib
import locale

from sqlalchemy.orm import session

from . import meta, ingredient_unit


def load_locale_defaults(package_name: str):
    """
    Load the best matching set of locale defaults. If your locale should be en_US, first defaults_en_US.py is
    tried, if not successful, defaults_en.py, and if this didn't work defaults.py
    Args:
        package_name (): The name of the package (ingredient_unit, categories..)

    Returns: None
    Raises:
        ImportError
    """

    def import_defaults(module_name: str):
        """ Try to import the file"""
        return importlib.import_module(f".{package_name}.{module_name}", __package__)

    locale_string, encoding = locale.getlocale()
    module_prefix = "defaults"

    # Try the whole string
    module_string = f"{module_prefix}_{locale_string}"

    try:
        return import_defaults(module_string)
    except ImportError:
        pass

    # Failed. Now try to use the language part only
    language = locale_string.split('_')
    module_string = f"{module_prefix}_{language[0]}"

    try:
        return import_defaults(module_string)
    except ImportError:
        pass

    # Failed. Try the global defaults
    return import_defaults(module_prefix)


def load_all(db_session: session):
    meta.load_values(db_session)
    ingredient_unit.load_values(db_session, load_locale_defaults("ingredient_unit"))
