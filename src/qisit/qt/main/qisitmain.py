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

import signal
import sys

from PyQt5 import QtCore, QtWidgets
from sqlalchemy import create_engine, orm

import qisit.core.db as db
import qisit.core.db.data as data
from qisit.core.util import initialize_db
from qisit.qt import misc
from qisit.qt.recipelistwindow.recipe_list_window_controller import RecipeListWindow


# TODO: *massive* rework, this is just a fast hack

def ask_database() -> str:
    home_directory = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.HomeLocation)
    database = f"sqlite:///{home_directory}/qisit.db"
    return database


def qtmain():
    QtCore.QCoreApplication.setOrganizationDomain("qisit.app")
    QtCore.QCoreApplication.setOrganizationName("qisit")
    QtCore.QCoreApplication.setApplicationName("qisit")
    QtCore.QCoreApplication.setApplicationVersion("0.5.2")

    # CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    settings = QtCore.QSettings()

    initialize = False
    if not settings.contains("database"):
        database = ask_database()
        if database is None:
            exit(0)
        else:
            settings.setValue("database", database)
            initialize = True
    else:
        database = settings.value("database")

    db.engine = create_engine(database, echo=False)
    db.Session.configure(bind=db.engine)
    if db.engine.driver == "psycopg2":
        db.group_concat = db.postgres_group_concat

    session = db.Session()

    if initialize:
        initialize_db(session, load_data=True)
    data.IngredientUnit.update_unit_dict(session)
    # db.engine = create_engine("mysql://qisit:qisit@127.0.0.1:33060/qisittest", echo=False)
    # db.engine = create_engine("postgresql+psycopg2://qisit:qisit@127.0.0.1:54320/qisittest")

    app = QtWidgets.QApplication(sys.argv)
    recipe_list_controller = RecipeListWindow(session)
    misc.setup()

    app.exec_()
    session.close()

if __name__ == '__main__':
    qtmain()
