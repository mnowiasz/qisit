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

import pytest

from qisit.core.db import data
from . import cleanup, add_integrity


def __setup_recipe(session) -> data.Recipe:
    recipe = data.Recipe("Test recipe")
    session.add(recipe)
    session.merge(recipe)
    return recipe


def test_recipe_image(db_session):
    """ Test if two entries cannot have the same position """

    assert db_session.query(data.Recipe).count() == 0
    assert db_session.query(data.RecipeImage).count() == 0

    recipe = __setup_recipe(db_session)
    image_one = data.RecipeImage(recipe, position=0, image=b"", thumbnail=b"")
    db_session.add(image_one)
    db_session.commit()

    assert db_session.query(data.Recipe).count() == 1
    assert db_session.query(data.RecipeImage).count() == 1

    image_two = data.RecipeImage(recipe, position=0, image=b"", thumbnail=b"")

    error = add_integrity(db_session, image_two, True)
    cleanup(db_session, data.Recipe)
    cleanup(db_session, data.RecipeImage)

    if error:
        pytest.fail(error)
