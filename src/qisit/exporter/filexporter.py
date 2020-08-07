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

