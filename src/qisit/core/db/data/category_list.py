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

from qisit.core import db


class CategoryList(db.Base):
    """ Aux table m:n (catgory to recipe) """
    __tablename__ = "category_list"

    recipe_id = sql.Column(sql.Integer, sql.ForeignKey("recipe.id", ondelete="CASCADE", onupdate="CASCADE"),
                           primary_key=True, nullable=False)
    category_id = sql.Column(sql.Integer, sql.ForeignKey("category.id", ondelete="CASCADE", onupdate="CASCADE"),
                             primary_key=True, nullable=False)
