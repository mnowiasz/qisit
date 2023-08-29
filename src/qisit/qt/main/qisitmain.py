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

from PyQt5 import Qt, QtCore, QtWidgets
from sqlalchemy import create_engine, exc

from qisit import translate
from qisit.core import db
from qisit.core.db import data
from qisit.core.util import initialize_db, nullify
from qisit.qt import misc
from qisit.qt.recipelistwindow.recipe_list_window_controller import RecipeListWindow


# TODO: *massive* rework, this is just a fast hack
def ask_database() -> (str, bool):
    _translate = translate
    initialize = True

    home_directory = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.HomeLocation)
    suggested_filename = QtCore.QDir(home_directory).filePath("qisit.db")
    filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(None, caption=_translate("StartUp",
                                                                                       "Open or create new database"),
                                                              directory=suggested_filename,
                                                              options=QtWidgets.QFileDialog.DontConfirmOverwrite)
    database = nullify(filename)
    if database is not None:
        initialize = not QtCore.QFileInfo.exists(filename)
        database = f"sqlite:///{database}"
    return database, initialize


def qtmain():
    QtCore.QCoreApplication.setOrganizationDomain("qisit.app")
    QtCore.QCoreApplication.setOrganizationName("qisit")
    QtCore.QCoreApplication.setApplicationName("qisit")
    QtCore.QCoreApplication.setApplicationVersion("0.9.0")
    # CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    settings = QtCore.QSettings()

    app = QtWidgets.QApplication(sys.argv)
    misc.setup_image_filter()
    misc.setup_global_actions()
    initialize = False
    db_error = False
    db_open = False

    # Iterate till either the user has canceled opening/creating a db or the database is open
    while db_open is False:
        if not settings.contains("database") or db_error is True:
            database, initialize = ask_database()
            print(f"database = {database}, init = {initialize}")
            if database is None:
                exit(0)
            else:
                settings.setValue("database", database)
        else:
            database = settings.value("database")

        try:
            db.engine = create_engine(database, echo=False)
            db.Session.configure(bind=db.engine)
            if db.engine.driver == "psycopg2":
                db.group_concat = db.postgres_group_concat
            session = db.Session()
            if initialize:
                initialize_db(session, load_data=True)
            data.IngredientUnit.update_unit_dict(session)
            db_open = True
            db_error = False
        except exc.DatabaseError as db_exception:
            _translate = translate
            Qt.QMessageBox.critical(None, _translate("StartUp", "Database Error!"),
                                    _translate("Startup", "Error opening {}: {}".format(database, str(db_exception.orig))))
            db_error = True
            db_open = False

    recipe_list_controller = RecipeListWindow(session)
    app.exec_()
    session.close()


if __name__ == '__main__':
    qtmain()
