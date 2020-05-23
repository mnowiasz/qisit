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

from sqlalchemy.orm import session

from qisit.core.db.data import IngredientUnit
from . import cldr


def load_values(db_session: session, module):
    def add_units(data, unit_type: IngredientUnit.UnitType, is_cldr: bool):
        for entry in data:
            unit = IngredientUnit(type_=unit_type, name=entry[0], factor=entry[1], description=entry[2], cldr=is_cldr)
            db_session.add(unit)

    def add_custom_units(data, unit_type: IngredientUnit.UnitType):
        for entry in data:
            unit = IngredientUnit(type_=unit_type, name=entry[0], factor=None, description=entry[1], cldr=False)
            db_session.add(unit)


    add_units(cldr.DATA_MASS, IngredientUnit.UnitType.MASS, is_cldr=True)
    add_units(cldr.DATA_VOLUME, IngredientUnit.UnitType.VOLUME, is_cldr=True)

    data_quantity = getattr(module, "DATA_QUANTITY")
    add_units(data_quantity, IngredientUnit.UnitType.QUANTITY, is_cldr=False)

    data_unspecific = getattr(module, "DATA_UNSPECIFIC")
    add_custom_units(data_unspecific, IngredientUnit.UnitType.UNSPECIFIC)

    db_session.commit()
