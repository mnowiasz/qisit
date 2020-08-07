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
# Jina exporter

from enum import Enum, auto

from babel.dates import format_timedelta
from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy import create_engine

from qisit import translate
from qisit.core import db
from qisit.core.db import data
from qisit.exporter import filexporter


class Jinja2Exporter(filexporter.GenericFileExporter):
    class Exporters(Enum):
        MYCOOKBOOK_XML = auto()
        MYCOOKBOOK_MCB = auto()

    def __init__(self):
        _translate = translate

        self._exporters = {self.Exporters.MYCOOKBOOK_XML: _translate("Exporter", "MyCookBook (XML, no Images)"),
                           self.Exporters.MYCOOKBOOK_MCB: _translate("Exporter", "MyCookBook (MCB archive)")}

        self._suffix = {self.Exporters.MYCOOKBOOK_XML: "xml",
                        self.Exporters.MYCOOKBOOK_MCB: "mcb"}
        self._supported_fields = {self.Exporters.MYCOOKBOOK_XML: {field for field in filexporter.ExportedFields if
                                                                  field != filexporter.ExportedFields.IMAGES},
                                  self.Exporters.MYCOOKBOOK_MCB: {field for field in filexporter.ExportedFields}}

        self._jinja2_env = Environment(loader=PackageLoader('qisit.exporter.jinja2', 'templates'),
                                       autoescape=select_autoescape(['html', 'xml']))
        self._templates = {self.Exporters.MYCOOKBOOK_XML: "mycookbook.xml",
                           self.Exporters.MYCOOKBOOK_MCB: "mycookbook.xml"}

    @property
    def available_exporters(self) -> dict:
        return self._exporters

    def file_suffix(self, export: Exporters) -> str:
        return self._suffix[export]

    def supported_fields(self, exporter: Exporters) -> set:
        return self._supported_fields[exporter]

    def export_recipes(self, recipes: list, filename: str, exporter: Enum, exported_fields: set):
        template_file = self._templates[exporter]

        template = self._jinja2_env.get_template(template_file)
        time_format = lambda value: format_timedelta(value, threshold=2, format="narrow")

        print(template.render(recipes=recipes, selected_fields=exported_fields, fields=filexporter.ExportedFields,
                              time_format=time_format, ingredient_formatter=self.format_ingredient_entry))

    def format_ingredient_entry(self, entry: data.IngredientListEntry):
        """
        Formats an ingredient entry

        Args:
            entry (): The entry

        Returns:
            A formatted string
        """

        # TODO: translate/comment
        if entry.is_group(entry.position):
            return f"---- {entry.ingredient.name} ----"

        level = 0
        alternative_string = ""
        optional_string = ""
        amount_string = entry.amount_string()
        group = entry.item_group(entry.position)
        if entry.optional:
            optional_string = " (optional)"

        if group != entry.GROUP_GLOBAL * entry.GROUP_FACTOR:
            level = 1
        if entry.is_alternative(entry.position):
            level += 1
            alternative_string = "or "
        elif entry.is_alternative_grouped(entry.position):
            level += 2
            alternative_string = "and "
        level_string = "--" * level
        if level > 0:
            level_string += " "
        return f"{level_string}{alternative_string}{amount_string} {entry.name}{optional_string}"


if __name__ == '__main__':
    database = f"sqlite:////home/mark/qisit-test.db"
    db.engine = create_engine(database, echo=False)
    db.Session.configure(bind=db.engine)

    session = db.Session()
    data.IngredientUnit.update_unit_dict(session)

    recipes = session.query(data.Recipe).all()

    exp = Jinja2Exporter()

    print(exp.file_suffix(Jinja2Exporter.Exporters.MYCOOKBOOK_XML))
    print(exp.supported_fields(Jinja2Exporter.Exporters.MYCOOKBOOK_XML))
    print(exp.available_exporters)

    exp.export_recipes(recipes, "/tmp/zeugs.xml", Jinja2Exporter.Exporters.MYCOOKBOOK_XML,
                       exp.supported_fields(Jinja2Exporter.Exporters.MYCOOKBOOK_XML))
