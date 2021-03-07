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

from abc import ABC
from enum import Enum, unique, auto

from babel.dates import format_timedelta, format_date

from qisit import translate
from qisit.core import default_locale
from qisit.core.db import data


# All supported fields to export
@unique
class ExportedFields(Enum):
    TITLE = auto()
    IMAGES = auto()
    CATEGORIES = auto()
    RATING = auto()
    YIELDS = auto()
    CUISINE = auto()
    AUTHOR = auto()
    PREPARATION_TIME = auto()
    COOKING_TIME = auto()
    TOTAL_TIME = auto()
    LAST_COOKED = auto()
    LAST_MODIFIED = auto()
    URL = auto()
    INGREDIENTS = auto()
    DESCRIPTION = auto()
    INSTRUCTIONS = auto()
    NOTES = auto()


# Abstract base class of all file based exporters.
class GenericFileExporter(ABC):

    def __init__(self):
        pass

    @property
    def available_exporters(self) -> dict:
        """
        The available exporters - there could be several, either "flavours" or templates (in the case of jinja2-exporters)

        Returns:
            Dictionary. Key is the name of the exporter (localized), value the internal ID (IntEnum)
        """
        raise NotImplementedError

    def file_suffix(self, export: Enum) -> str:
        """
        The generic/suggested file suffix used by the given exporter (.xml, .mcb, .rcb, ...)
        Args:
            export ():  The (internal) ID of the exporter

        Returns:
            The suggested suffix
        """
        raise NotImplementedError

    def supported_fields(self, exporter: Enum) -> set:
        """
        The supported fields of the specific exporter

        Args:
            exporter (): The (internal) ID of the exporter

        Returns:
            A set containing all supported fields
        """
        raise NotImplementedError

    def export_recipes(self, recipes: list, filename: str, exporter: Enum, exported_fields: set):
        """
        Export the list of recipes to the file referenced by filename using the selected exporter and the chosen fields

        Args:
            recipes (): The list of recipes to export
            filename (): The filename for the export
            exporter (): The given exporter
            exported_fields (): The fields to export

        Returns:

        """
        raise NotImplementedError


# Format certain fields according to the user's locale
class Formatter(object):

    def __init__(self):
        self._translate = translate

    def ingredient_entry(self, entry: data.IngredientListEntry):
        """
        Formats an ingredient entry

        Args:
            entry (): The entry

        Returns:
            A formatted string
        """

        # Groups. Not every format supports groups. In this case a special, marked ingredient ist created
        if entry.is_group(entry.position):
            return f"---- {entry.ingredient.name} ----"

        _translate = self._translate

        # THe level of the ingredient tree
        level = 0

        # Or
        alternative_string = ""

        # And
        optional_string = ""

        amount_string = entry.amount_string()
        group = entry.item_group(entry.position)
        if entry.optional:
            optional_string = f' {_translate("Exporter", "(optional)")}'

        # An ingredient that belongs under one group
        if group != entry.GROUP_GLOBAL * entry.GROUP_FACTOR:
            level = 1

        # Alternative to the ingredient "or". One level below the standard ingredient
        if entry.is_alternative(entry.position):
            level += 1
            alternative_string = f' {_translate("Exporter", "or")} '

        # A grouped alternative ("and"). Two levels below the standard ingredient
        elif entry.is_alternative_grouped(entry.position):
            level += 2
            alternative_string = f' {_translate("Exporter", "amd")} '

        level_string = "--" * level
        if level > 0:
            level_string += " "
        return f"{level_string}{alternative_string}{amount_string} {entry.name}{optional_string}"

    def time_delta(self, value: int):
        """
        Formats a time delta (preparation time, ...) in the user's locale
        Args:
            value (): Time delta value

        Returns:
            Formatted string
        """
        return format_timedelta(value, threshold=2, format="narrow", locale=default_locale)

    def _format_time(self, prefix: str, value) -> str:
        """
        Aux methods - do not repeat yourself. last_cooked and las_modified are identically, only the prefix is
        different

        Args:
            prefix (): The Prefix ("Last Modified")
            value (): The timevalue

        Returns:
            Formatted string
        """

        return f"{prefix} {format_date(value, format='short', locale=default_locale)}"

    def last_cooked(self, value) -> str:
        _translate = self._translate
        return self._format_time(_translate("Exporter", "Last cooked:"), value)

    def last_modified(self, value) -> str:
        _translate = self._translate
        return self._format_time(_translate("Exporter", "Last modified:"), value)
