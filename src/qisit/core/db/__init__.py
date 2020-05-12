""" Database backend"""

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

from sqlite3 import Connection as SQLite3Connection

import sqlalchemy as sql
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropTable

Base = declarative_base()
""" The base class for the ORM mappings """

Session = sessionmaker()
""" The session """

engine = None
""" The database engine """

group_concat = sql.func.group_concat
""" Workaround for postgres which hasn't a group_concat aggregate function (but from 9.0 up, something similar"""


def postgres_group_concat(args):
    """ Postgres' version of group_concat"""
    return sql.func.string_agg(args, ',')


@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    """ Otherwise drop_all() won't work """
    return compiler.visit_drop_table(element) + " CASCADE"


@event.listens_for(Engine, "connect")
def _set_dialect(dbapi_connection, connection_record):
    """ Some dialect specific options """
    if isinstance(dbapi_connection, SQLite3Connection):
        # Ugly hack for sqlite to enable foreign keys
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
        # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#pysqlite-serializable
        dbapi_connection.isolation_level = None


@event.listens_for(Engine, "begin")
def do_begin(conn):
    #  https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#pysqlite-serializable
    conn.execute("BEGIN")


def get_or_add_item(session_: sql.orm.session, table: Base, name: str, filter_args=None, *args, **kwargs):
    """
    Returns an already existing database object or creates if it's not existing. Useful for importing recipes or
    creating items  on the fly (when the user adds a new recipe)

    Args:
        session_ (): Database session
        table (): The table
        name (): The name (for querying)
        filter_args (): Optional args for the filter
        *arg (): args to pass to __init__
        **kwargs (): keyword args

    Returns:
        Either an existing object or a newly created one
    """

    if not filter_args:
        the_item = session_.query(table).filter(table.name == name).first()
    else:
        the_item = session_.query(table).filter(*filter_args).first()

    if the_item:
        return the_item

    # Doesn't exist (yet), so create it
    new_item = table(name, *args, **kwargs)
    session_.add(new_item)
    session_.merge(new_item)
    return new_item
