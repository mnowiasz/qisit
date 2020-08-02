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
from enum import IntEnum


# All supported fields to export
class ExportedFields(IntEnum):
    TITLE: 1


# Abstract base class of alle file based exporters.

class GenericExporter(ABC):

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

    @property
    def supported_fields(self, exporter: IntEnum) -> set:
        """
        The supported fields of the specific exporter

        Args:
            exporter (): The (internal) ID of the exporter

        Returns:
            A set containing all supported fields
        """
        raise NotImplementedError

