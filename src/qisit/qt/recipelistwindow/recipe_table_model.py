""" The model of the recipe's table """

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

import typing
from enum import IntEnum

from PyQt5 import QtCore, QtGui
from babel.dates import format_timedelta, format_date
from babel.numbers import format_decimal
from sqlalchemy import func, orm

from qisit import translate
from qisit.core import db
from qisit.core.db import data


class RecipeTableModel(QtCore.QAbstractTableModel):
    """ Recipe's Table model """

    class RecipeColumns(IntEnum):
        """ Symbolic column names """
        ID = 0
        THUMBNAIL = 1
        TITLE = 2
        CATEGORIES = 3
        CUISINE = 4
        AUTHOR = 5
        YIELD = 6
        RATING = 7
        PREPARATION_TIME = 8
        COOK_TIME = 9
        TOTAL_TIME = 10
        LAST_COOKED = 11
        LAST_MODIFIED = 12

    sortable_columns = (
        int(RecipeColumns.TITLE), int(RecipeColumns.CATEGORIES), int(RecipeColumns.AUTHOR), int(RecipeColumns.CUISINE),
        int(RecipeColumns.YIELD), int(RecipeColumns.RATING), int(RecipeColumns.PREPARATION_TIME),
        int(RecipeColumns.COOK_TIME), int(RecipeColumns.TOTAL_TIME), int(RecipeColumns.LAST_COOKED),
        int(RecipeColumns.LAST_MODIFIED))
    """ Which columns are sortable? For example, there's no meaningful sort order for thumbnails. """

    def __init__(self, db_session: orm.Session, offset: int = 0, recipes_per_page: int = 10):
        super().__init__()
        self._translate = translate
        self.column_headers = {}
        self.__sort_criteria = {}
        self.__setup_column_headers()
        self.__setup_sort_criteria()
        self._session = db_session

        # The "base" query (i.e. the query without any limits, order_by or filters)
        self._base_query = self._session.query(data.Recipe, data.Author, data.Cuisine,
                                               db.group_concat(data.Category.name)) \
            .join(data.Author, isouter=True) \
            .join(data.Cuisine, isouter=True) \
            .join(data.CategoryList, isouter=True) \
            .join(data.Category, isouter=True) \
            .group_by(data.Recipe.id, data.Author.id, data.Cuisine.id)

        # There are four values relevant for displaying/filtering/paging:

        # The total number of recipes. Relatively constant, changes only when the user adds (either manually or
        # via import) or deletes recipes. Mainly used for statistics
        self.total_number_of_recipes = self._session.query(data.Recipe).count()

        # The number of filtered entries. Whenever the user applies (or deselects) a filter the number will change.
        # When no filter is active it should be identical with self.total_number_of_recipes
        self.number_of_filtered_recipes = self.total_number_of_recipes

        # The (maximum) number of recipes per page. The number might be larger then self.number_of_filtered_recipes
        # (in this case there's only one page) or smaller (in that case there's at least one more page)
        self.recipes_per_page = recipes_per_page

        # Offset. If the user selects paging this could be a multiple of self.recipes_per_page
        # (for example, page 3: offset == 3*self.recipes_per_page), but there's no reason to assume that - if the
        # user uses the scrollbar the offset might have any value within self.number_of_filtered_recipes
        # (the largest value should be self.number_of_filtered_recipes - self.recipes_per_page).
        # When a filter (or a search pattern) has been changed the offset will be reset to 0.
        self.offset = offset

        # The name-based entry filters
        self.filters = {
            data.Category: set(),
            data.Cuisine: set(),
            data.Author: set()
        }

        # Used when one column has been selected for sorting
        self.__order_by = None

        # The entry in the search text field
        self.search_title = None

        # The entries currently shown
        self._entries = []
        self.__setup_entries()

    def __setup_column_headers(self):
        """ Setup translations and icons for the headers """
        _translate = self._translate

        # Maybe make the icons locale specific?
        self.column_headers = {
            self.RecipeColumns.ID: (_translate("RecipeTableWindow", "ID"), None),
            self.RecipeColumns.THUMBNAIL: (_translate("RecipeTableWindow", "Picture"), ":/icons/picture.png"),
            self.RecipeColumns.TITLE: (_translate("RecipeTableWindow", "Title"), ":/icons/cards-stack.png"),
            self.RecipeColumns.CATEGORIES: (_translate("RecipeTableWindow", "Categories"), ":/icons/bread.png"),
            self.RecipeColumns.CUISINE: (_translate("RecipeTableWindow", "Cuisine"), ":/icons/cutleries.png"),
            self.RecipeColumns.YIELD: (_translate("RecipeTableWindow", "Yields"), ":/icons/plates.png"),
            self.RecipeColumns.AUTHOR: (_translate("RecipeTableWindow", "Author"), ":/icons/quill.png"),
            self.RecipeColumns.RATING: (_translate("RecipeTableWindow", "Rating"), ":/icons/star.png"),
            self.RecipeColumns.PREPARATION_TIME: (_translate("RecipeTableWindow", "Preparation"), ":/icons/clock.png"),
            self.RecipeColumns.COOK_TIME: (_translate("RecipeTableWindow", "Cooking"), ":/icons/clock.png"),
            self.RecipeColumns.TOTAL_TIME: (_translate("RecipeTableWindow", "Total"), ":/icons/clock.png"),
            self.RecipeColumns.LAST_COOKED: (
                _translate("RecipeTableWindow", "Last Cooked"), ":/icons/calendar-day.png"),
            self.RecipeColumns.LAST_MODIFIED: (
                _translate("RecipeTableWindow", "Last Modified"), ":/icons/calendar-day.png")
        }

    def __setup_entries(self):
        the_query = self._base_query

        # Let's construct the final query. First apply all active filters
        for table in (data.Category, data.Cuisine, data.Author):
            if len(self.filters[table]):
                the_query = the_query.filter(table.id.in_(self.filters[table]))

        # Search by recipe's title
        if self.search_title is not None:
            filter_clause = f"%{self.search_title}%"

            # The user can apply SQL wildcards (% and _). If he does, use the search fields without any changes
            contains_wildcards = "%" in self.search_title or "_" in self.search_title
            if contains_wildcards:
                filter_clause = self.search_title
            the_query = the_query.filter(data.Recipe.title.like(filter_clause))

        self.number_of_filtered_recipes = the_query.count()

        # Then the sort order
        if self.__order_by is not None:
            the_query = the_query.order_by(self.__order_by)

        # Finally pagination
        the_query = the_query.limit(self.recipes_per_page).offset(self.offset)

        self._entries = the_query.all()

    def __setup_sort_criteria(self):
        """
        Sort criteria for the columns. This has to be done dynamically at __init__, because otherwise
        db.group_concat might not be properly set when using PostgreSQL

        Returns:

        """

        # Title, database field, string?
        self.__sort_criteria = {
            self.RecipeColumns.TITLE: (data.Recipe.title, True),
            self.RecipeColumns.CATEGORIES: (db.group_concat(data.Category.name), True),
            self.RecipeColumns.CUISINE: (data.Cuisine.name, True),
            self.RecipeColumns.AUTHOR: (data.Author.name, True),
            self.RecipeColumns.YIELD: (data.Recipe.yields, False),
            self.RecipeColumns.RATING: (data.Recipe.rating, False),
            self.RecipeColumns.PREPARATION_TIME: (data.Recipe.preparation_time, False),
            self.RecipeColumns.COOK_TIME: (data.Recipe.cooking_time, False),
            self.RecipeColumns.TOTAL_TIME: (data.Recipe.total_time, False),
            self.RecipeColumns.LAST_COOKED: (data.Recipe.last_cooked, False),
            self.RecipeColumns.LAST_MODIFIED: (data.Recipe.last_modified, False)
        }

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return self.RecipeColumns.LAST_MODIFIED + 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        """ Display data  """
        column = index.column()
        row = index.row()

        recipe = self._entries[row][0]

        # Special consideration for the thumbnail column
        if column == self.RecipeColumns.THUMBNAIL:
            if role == QtCore.Qt.SizeHintRole or role == QtCore.Qt.DecorationRole:

                thumbnail = None

                if len(recipe.imagelist) != 0:
                    thumbnail = QtGui.QPixmap()
                    thumbnail.loadFromData(recipe.imagelist[data.RecipeImage.main_image_pos].thumbnail)
                else:
                    return None

                # Resize the thumb column to fit the thumbnail (usually 40 px height, but better do not assume anything
                if role == QtCore.Qt.SizeHintRole:
                    return thumbnail.size()

                if role == QtCore.Qt.DecorationRole:
                    return QtCore.QVariant(thumbnail)
                else:
                    return None
            else:
                return None

        if role != QtCore.Qt.DisplayRole:
            return None

        # Maybe replace the "magic" numbers [0], [1] with more symbolic names?
        if column == self.RecipeColumns.ID:
            return QtCore.QVariant(recipe.id)

        if column == self.RecipeColumns.TITLE:
            return QtCore.QVariant(recipe.title)

        if column == self.RecipeColumns.CATEGORIES:
            return QtCore.QVariant(self._entries[row][3])

        if column == self.RecipeColumns.CUISINE:
            cuisine = self._entries[row][2]
            if cuisine:
                return QtCore.QVariant(str(cuisine))
            else:
                return None

        if column == self.RecipeColumns.AUTHOR:
            author = self._entries[row][1]
            if author:
                return QtCore.QVariant(str(author))
            else:
                return None

        if column == self.RecipeColumns.YIELD:
            yields = recipe.yields
            yield_unit_name = recipe.yield_unit_name
            yield_string = None
            if yields > 0:
                if yield_unit_name:
                    yield_string = f"{format_decimal(yields)} {yield_unit_name}"
                else:
                    yield_string = format_decimal(yields)
            return QtCore.QVariant(yield_string)

        if column == self.RecipeColumns.RATING:
            if recipe.rating:
                return QtCore.QVariant(f"{recipe.rating}/10")
            else:
                return None

        if column in (self.RecipeColumns.PREPARATION_TIME, self.RecipeColumns.COOK_TIME,
                      self.RecipeColumns.TOTAL_TIME):
            value = None
            if column == self.RecipeColumns.PREPARATION_TIME:
                value = recipe.preparation_time
            elif column == self.RecipeColumns.COOK_TIME:
                value = recipe.cooking_time
            elif column == self.RecipeColumns.TOTAL_TIME:
                value = recipe.total_time

            if value:
                return QtCore.QVariant(format_timedelta(value, threshold=2, format="narrow"))
            else:
                return None

        if column in (self.RecipeColumns.LAST_COOKED, self.RecipeColumns.LAST_MODIFIED):
            value = None
            if column == self.RecipeColumns.LAST_COOKED:
                value = recipe.last_cooked
            elif column == self.RecipeColumns.LAST_MODIFIED:
                value = recipe.last_modified
            if value:
                return QtCore.QVariant(format_date(value, format="short"))
            else:
                return None

        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        """ Header data """
        if role == QtCore.Qt.DecorationRole and orientation == QtCore.Qt.Horizontal:
            icon_resource = self.column_headers[section][1]
            if icon_resource:
                return QtGui.QPixmap(icon_resource)
            else:
                return None

        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Vertical:
            return QtCore.QVariant(section + 1 + self.offset)

        return QtCore.QVariant(self.column_headers[section][0])

    def recipe_at_row(self, row: int):
        """
        Returns the recipe at the given row

        Args:
            row (): the row

        Returns: recipe

        """

        if row > self.recipes_per_page:
            return None
        return self._entries[row][0]

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if self.number_of_filtered_recipes < self.recipes_per_page:
            return self.number_of_filtered_recipes
        else:
            return self.recipes_per_page

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        """
        Sort the table by the given column

        Args:
            column ():
            order ():

        Returns:

        """

        if column not in self.sortable_columns:
            return

        sort_entry = None
        if column in self.__sort_criteria:
            crit, is_string = self.__sort_criteria[column]
            sort_entry = crit
            if is_string:
                sort_entry = func.lower(crit)
        else:
            return

        if order == QtCore.Qt.AscendingOrder:
            self.__order_by = sort_entry.asc()
        elif order == QtCore.Qt.DescendingOrder:
            self.__order_by = sort_entry.desc()

        self.update_model()

    def update_model(self):
        """
        A new filter has been applied, sort order has been changed..

        Returns:

        """
        self.beginResetModel()
        self.__setup_entries()
        self.endResetModel()
