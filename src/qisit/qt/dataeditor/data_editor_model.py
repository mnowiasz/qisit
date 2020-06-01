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

import pickle
import typing
from enum import IntEnum

from PyQt5 import QtCore, QtGui
from sqlalchemy import orm, func, text

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify
from qisit.qt import misc


class DataEditorModel(QtCore.QAbstractItemModel):
    class RootItems(IntEnum):
        """ Symbolic row names """
        AUTHOR = 0
        CATEGORIES = 1
        CUISINE = 2
        INGREDIENTS = 3
        INGREDIENTGROUPS = 4
        INGREDIENTUNITS = 5
        YIELD_UNITS = 6

    class Columns(IntEnum):
        """ Symbolic column names """

        ROOT = 0
        ITEMS = 1
        INGREDIENTLIST_ENTRIES = 2

    class FirstColumnData(IntEnum):
        """ Symbolic names for self:_first_column """
        TABLE = 0
        NAME = 1
        ICON = 2

    mime_type = "application/x-qisit-dataeditor"

    changed = QtCore.pyqtSignal()
    """ Data have been changed """

    changeSelection = QtCore.pyqtSignal(QtCore.QModelIndex)
    """ Tell the view to change it's selection to the index. This is also a workaround for a strange bug:
    When merging two or more items *and* a ingredient unit has been selected the selection becomes odd and
    the first column is duplicated. Odd. """

    illegalValue = QtCore.pyqtSignal(misc.ValueError, str)
    """ The user entered a duplicate value """

    def __init__(self, session: orm.Session):

        super().__init__()
        self._session = session

        # This needs some explanation. index() need to save information about it's parent so parent() can extract these
        # to create a valid index. Unfortunately it's not possible to save information into index's.internalPointer() -
        # Python's garbage collector causes havoc in this case, deleting the object stored into internalPointer(). So
        # apart from saving the information in the model (i.e. in a structure like a list, dictionary or tree) - which
        # is overkill in this case - this is used to store *which row* has been selected as a parent in the given
        # column.
        self._parent_row = {}

        # Table, Text, Icon.
        self._first_column = {}
        self.__setup_first_column()

        # Icons / ingredient unit types
        self._ingredient_unit_icons = {
            data.IngredientUnit.UnitType.MASS: ":/icons/weight.png",
            data.IngredientUnit.UnitType.VOLUME: ":/icons/beaker.png",
            data.IngredientUnit.UnitType.QUANTITY: ":/icons/sum.png",
            data.IngredientUnit.UnitType.UNSPECIFIC: ":/icons/paper-bag.png"
        }

        # The list of items displayed in the column
        self._item_lists = {column: [] for column in self.Columns}

        # Item is a CLDR unit, therefore not editable (the name of the item is generated dymically using the
        # user's locale
        self._cldr_font = QtGui.QFont()
        self._cldr_font.setItalic(True)

        # Base unit - neither editable nor deletable
        self._baseunit_font = QtGui.QFont()
        self._baseunit_font.setBold(True)
        self._baseunit_font.setItalic(True)

    def __setup_first_column(self):
        _translate = translate
        # Table, Item, Icon
        self._first_column = {
            self.RootItems.AUTHOR: (data.Author, _translate("DataEditor", "Author"), ":/icons/quill.png"),
            self.RootItems.CATEGORIES: (
                data.Category, _translate("DataEditor", "Categories"), ":/icons/bread.png"),
            self.RootItems.CUISINE: (data.Cuisine, _translate("DataEditor", "Cuisine"), ":/icons/cutleries.png"),
            self.RootItems.INGREDIENTS: (
                data.Ingredient, _translate("DataEditor", "Ingredients"), ":/icons/mushroom.png"),
            self.RootItems.INGREDIENTGROUPS: (
                data.Ingredient, _translate("DataEditor", "Ingredient Groups"), ":/icons/edit-bold.png"),
            self.RootItems.INGREDIENTUNITS: (
                data.IngredientUnit, _translate("DataEditor", "Amount units"), ":/icons/beaker.png"),
            self.RootItems.YIELD_UNITS: (
                data.YieldUnitName, _translate("DataEditor", "Yield units"), ":/icons/plates.png"),
        }

    @property
    def root_row(self) -> int:
        return self._parent_row.get(self.Columns.ROOT, None)

    def canDropMimeData(self, data: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                        parent: QtCore.QModelIndex) -> bool:

        if not data.hasFormat(self.mime_type):
            return False

        # Only drops on the Item columns are allowed. And then only dropping directly on an item - the seconds
        # clause takes care of that. Otherwise it would be possible (at least visibly) to move an item to a leaf above
        # or beneath another item
        return parent.internalId() == self.Columns.ITEMS and column < 0

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """ There's only one column regardless of the depth of the tree """
        return 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role not in (
                QtCore.Qt.DisplayRole, QtCore.Qt.DecorationRole, QtCore.Qt.EditRole, QtCore.Qt.FontRole,
                QtCore.Qt.UserRole, QtCore.Qt.SizeHintRole):
            return QtCore.QVariant(None)

        column = index.internalId()
        row = index.row()
        count = 0
        if column == self.Columns.ROOT:
            # TODO: This needs optimization, for example caching.
            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.UserRole):
                # Construct a query, i.e. which table to query
                query = self._session.query(self._first_column[row][self.FirstColumnData.TABLE])

                # Ingredients and ingredient groups only differ whether to display ingredients groups
                # (and no ingredients) or only ingredients (and not groups)
                if row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTGROUPS):
                    group = (row == self.RootItems.INGREDIENTGROUPS)
                    # is False/is True wouldn't work here
                    query = query.filter(data.Ingredient.is_group == group)
                count = query.count()

                if role == QtCore.Qt.DisplayRole:
                    return QtCore.QVariant(f"{self._first_column[row][self.FirstColumnData.NAME]} ({count})")
                if role == QtCore.Qt.UserRole:
                    return QtCore.QVariant(count)

            if role == QtCore.Qt.DecorationRole:
                icon = self._first_column[row][self.FirstColumnData.ICON]
                if icon is not None:
                    return QtCore.QVariant(QtGui.QIcon(icon))

            return QtCore.QVariant()

        if column == self.Columns.ITEMS:
            item = self._item_lists[self.Columns.ITEMS][row][0]
            count = self._item_lists[self.Columns.ITEMS][row][1]
            if role == QtCore.Qt.UserRole:
                if self.root_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTUNITS):
                    return QtCore.QVariant(count)
                else:
                    return 0

            if role == QtCore.Qt.DisplayRole:
                title = f"{item.name} ({count})"
                if self.root_row == self.RootItems.INGREDIENTUNITS:
                    # Display the unit in the user's locale
                    if item.cldr:
                        title = f"{item.unit_string()} ({count})"
                return QtCore.QVariant(title)

            if role == QtCore.Qt.EditRole:
                return QtCore.QVariant(item.name)

            # Ingredient icon
            if self.root_row == self.RootItems.INGREDIENTS:
                if role == QtCore.Qt.SizeHintRole:
                    return QtCore.QVariant(QtCore.QSize(0, misc.values.ingredient_icon_height))
                elif role == QtCore.Qt.DisplayRole and item.icon is not None:
                    pixmap = QtGui.QPixmap()
                    if pixmap.loadFromData(item.icon):
                        return QtCore.QVariant(pixmap)

            if self.root_row == self.RootItems.INGREDIENTUNITS:
                ingredient_unit = item
                is_base_unit = ingredient_unit in data.IngredientUnit.base_units.values()

                if role == QtCore.Qt.FontRole:
                    if is_base_unit:
                        return QtCore.QVariant(self._baseunit_font)
                    elif ingredient_unit.cldr:
                        return QtCore.QVariant(self._cldr_font)

                if role == QtCore.Qt.DecorationRole:
                    return QtCore.QVariant(QtGui.QIcon(self._ingredient_unit_icons[ingredient_unit.type_]))

        elif column == self.Columns.INGREDIENTLIST_ENTRIES:
            item = self._item_lists[column][row]
            if role == QtCore.Qt.UserRole:
                return 0

            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
                return QtCore.QVariant(item.name)

        return QtCore.QVariant(None)

    def delete_item(self, index: QtCore.QModelIndex):
        """
        Deletes an item (if allowed, that is)

        Args:
            index (): The index

        Returns:

        """

        if self.is_deletable(index):
            self.changed.emit()
            index_row = index.row()
            self.beginRemoveRows(self.createIndex(self.root_row, 0, self.Columns.ROOT), index_row, index_row)
            the_item = self._item_lists[index.internalId()][index_row][0]
            self._session.delete(the_item)
            self.endRemoveRows()

    def dropMimeData(self, mimedata: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                     parent: QtCore.QModelIndex) -> bool:

        index_list = pickle.loads(mimedata.data(self.mime_type))
        target_row = parent.row()
        target_column = parent.internalId()

        # The affected recipes
        recipes_ids = set()

        # Merge vs append
        merged = False
        cached = {}

        # This is needed because of the rows that will be removed - the indexes aren't valid after that, so
        # this is to conserve (temporarily) the status quo ante
        for (index_row, index_column) in index_list:
            cached[(target_column, target_row)] = self._item_lists[target_column][target_row][0]
            if index_column == target_column:
                cached[(target_column, index_row)] = self._item_lists[target_column][index_row][0]
            else:
                cached[(index_column, index_row)] = self._item_lists[index_column][index_row]

        for (index_row, index_column) in index_list:
            if index_column == target_column:
                # Merge operation
                merged = True

                source_item = cached[(target_column, index_row)]
                target_item = cached[(target_column, target_row)]

                # Merging an item with itself is useless
                if source_item == target_item:
                    return False

                self.changed.emit()

                recipes_ids = recipes_ids.union([recipe.id for recipe in source_item.recipes])
                self.beginRemoveRows(self.createIndex(self.root_row, 0, self.Columns.ROOT), index_row, index_row)

                the_table = None
                if self.root_row in (self.RootItems.AUTHOR, self.RootItems.CUISINE, self.RootItems.YIELD_UNITS):
                    the_query = self._session.query(data.Recipe)
                    if self.root_row == self.RootItems.AUTHOR:
                        the_query.filter(data.Recipe.author_id == source_item.id).update(
                            {data.Recipe.author_id: target_item.id}, synchronize_session='evaluate')
                    elif self.root_row == self.RootItems.CUISINE:
                        the_query.filter(data.Recipe.cuisine_id == source_item.id).update(
                            {data.Recipe.cuisine_id: target_item.id}, synchronize_session='evaluate')
                    elif self.root_row == self.RootItems.YIELD_UNITS:
                        the_query.filter(data.Recipe.yield_unit_id == source_item.id).update(
                            {data.Recipe.yield_unit_id: target_item.id}, synchronize_session='evaluate')

                elif self.root_row == self.RootItems.CATEGORIES:
                    # Categories are special. TODO: Maybe construct a (rather complicated, probably) Query instead
                    # of this

                    # Need to copy the list recipes - because making changes will alter the original recipes
                    recipes = [recipe for recipe in source_item.recipes]
                    for recipe in recipes:
                        if target_item not in recipe.categories:
                            recipe.categories.append(target_item)
                        recipe.categories.remove(source_item)
                        self._session.merge(recipe)
                elif self.root_row in (self.RootItems.INGREDIENTGROUPS, self.RootItems.INGREDIENTS):
                    self._session.query(data.IngredientListEntry).filter(
                        data.IngredientListEntry.ingredient_id == source_item.id).update(
                        {data.IngredientListEntry.ingredient_id: target_item.id}, synchronize_session='evaluate')
                elif self.root_row == self.RootItems.INGREDIENTUNITS:
                    self._session.query(data.IngredientListEntry).filter(
                        data.IngredientListEntry.unit_id == source_item.id).update(
                        {data.IngredientListEntry.unit_id: target_item.id}, synchronize_session='evaluate')
                self._session.expire_all()
                self._session.delete(source_item)
            else:
                # Append operation. Only allowed on Cuisine or Ingredients
                self.changed.emit()
                # target_item = self._item_lists[target_column][target_row][0]
                target_item = cached[(target_column, target_row)]
                parent_index = self._parent_row[target_column]
                self.beginRemoveRows(self.createIndex(parent_index, 0, self.Columns.ITEMS), index_row, index_row)
                if self.root_row == self.RootItems.CUISINE:
                    recipe = cached[(index_column, index_row)]
                    recipe.cuisine = target_item

                elif self.root_row == self.RootItems.INGREDIENTS:
                    ingredient_list_entry = cached[(index_column, index_row)]
                    ingredient_list_entry.ingredient = target_item
                self._session.refresh(target_item)

            self.endRemoveRows()

        if merged:
            self.changeSelection.emit(parent)

        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        column = index.internalId()

        is_editable = False
        is_drop_enabled = False
        is_drag_enabled = False

        if column in (self.Columns.ITEMS, self.Columns.INGREDIENTLIST_ENTRIES):

            # Only certain combinations of drag&drop make sense: The item column can drag itself on another item
            # and recipes can be dragged to another author or cuisine. All other combination aren't very useful
            is_drag_enabled = (column == self.Columns.ITEMS or self._parent_row[self.Columns.ROOT] in (
                self.RootItems.INGREDIENTS, self.RootItems.CUISINE))

            if column == self.Columns.ITEMS:
                is_drop_enabled = True
                if self.root_row == self.RootItems.INGREDIENTUNITS:
                    ingredient_unit = self._item_lists[self.Columns.ITEMS][index.row()][0]
                    is_editable = not ingredient_unit.cldr and not ingredient_unit in data.IngredientUnit.base_units.values()
                    is_drag_enabled = is_editable
                else:
                    is_editable = True
                    is_drag_enabled = True
            else:
                is_editable = self.root_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTUNITS)

        if is_editable:
            flags |= QtCore.Qt.ItemIsEditable

        if is_drop_enabled:
            flags |= QtCore.Qt.ItemIsDropEnabled

        if is_drag_enabled:
            flags |= QtCore.Qt.ItemIsDragEnabled

        return flags

    def get_item(self, row: int, column: int):
        return self._item_lists[column][row]

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        # Number of children is stored in the item's user role
        return not parent.isValid() or parent.data(QtCore.Qt.UserRole) > 0

    def index(self, row: int, column: int, parent: QtCore.QModelIndex = ...) -> QtCore.QModelIndex:
        if not parent.isValid():
            # The very first column, the root column. There's only one (model) column, hence the 0
            return self.createIndex(row, 0, self.Columns.ROOT)
        else:
            # The "display" column, *not* the model column
            parent_column = parent.internalId()
            self._parent_row[parent_column] = parent.row()
            return self.createIndex(row, 0, parent_column + 1)

    def is_deletable(self, index: QtCore.QModelIndex) -> bool:
        """
        Returns if an item is deletable

        Args:
            index (): The index

        Returns:
            True, if it can be deleted, false if not
        """

        column = index.internalId()
        # All deletable items are in the Items column
        if column != self.Columns.ITEMS:
            return False

        # These can be deleted in any case
        if self.root_row in (
                self.RootItems.AUTHOR, self.RootItems.CATEGORIES, self.RootItems.CUISINE, self.RootItems.YIELD_UNITS):
            return True

        # All other items may be only deleted if they are "empty" i.e. have no children
        number_of_items = index.data(QtCore.Qt.UserRole)
        if number_of_items > 0:
            return False

        # Last but not least: The base units cannot be deleted
        if self.root_row == self.RootItems.INGREDIENTUNITS:
            ingredient_unit = self._item_lists[self.Columns.ITEMS][index.row()][0]
            return ingredient_unit not in data.IngredientUnit.base_units

        return True

    def mimeData(self, indexes: typing.Iterable[QtCore.QModelIndex]) -> QtCore.QMimeData:
        index_list = [(index.row(), index.internalId()) for index in indexes]

        mime_data = QtCore.QMimeData()
        mime_data.setData(self.mime_type, pickle.dumps(index_list))
        return mime_data

    def new_ingredient_item(self):
        """
        A new ingredient item has been added to the database

        Returns:

        """

        # Instead of inserting rows and so on just reload the list of ingredients :-)
        ingredient_index = self.createIndex(self.RootItems.INGREDIENTS, 0, 0)
        self.dataChanged.emit(ingredient_index, ingredient_index)

    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:

        # Again - the "display" column, *not* the model column (which is always 0)
        child_column = child.internalId()
        if child_column == self.Columns.ROOT:
            # The items on the root level have no parent
            return QtCore.QModelIndex()
        return self.createIndex(self._parent_row[child_column - 1], 0, child_column - 1)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if parent.row() == -1:
            return self.RootItems.YIELD_UNITS + 1

        column = parent.internalId() + 1

        # Lazily load the columns. Note: Usually this is done using fetchMore() / canFetchMore. However, since
        # counting the rows and fetching the data at the same time is more efficient than first counting the rows
        # and then fetching the data (duplicating the same joins) this is done here
        parent_row = parent.row()

        # TODO: Restore/optimize by caching
        if column == self.Columns.ITEMS:
            the_table = self._first_column[parent_row][self.FirstColumnData.TABLE]

            # Construct the query
            query = None
            if parent_row == self.RootItems.INGREDIENTUNITS:
                # Ingredients (or better: amount units) are rather special - due to the handling of
                # CLDR the query has too little in common with the other ones. There's also the one
                # special class for Ingredient Groups
                self._item_lists[column] = self._session.query(the_table, func.count(data.IngredientListEntry.id)) \
                    .join(data.IngredientListEntry, data.IngredientUnit.id == data.IngredientListEntry.unit_id,
                          isouter=True).order_by(text('cldr DESC, type_ ASC,  lower(ingredient_unit.name) ASC')) \
                    .group_by(the_table.id) \
                    .filter(data.IngredientUnit.type_ != data.IngredientUnit.UnitType.GROUP).all()
            else:
                if parent_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTGROUPS):
                    # Ingredient groups and Ingredients are virtually the same - the only difference is that
                    # Ingredients have is_group = False, where for Ingredients groups it's true
                    group = (parent_row == self.RootItems.INGREDIENTGROUPS)
                    query = self._session.query(the_table, func.count(data.IngredientListEntry.id).label("count")) \
                        .join(data.IngredientListEntry, isouter=True).filter(data.Ingredient.is_group == group)
                else:
                    # Items which have recipes attached to them
                    query = self._session.query(the_table, func.count(data.Recipe.id).label("count"))

                    # Categories need an additional join
                    if parent_row == self.RootItems.CATEGORIES:
                        query = query.join(data.CategoryList, data.Category.id == data.CategoryList.category_id,
                                           isouter=True)
                    query = query.join(data.Recipe, isouter=True)

                self._item_lists[column] = query.group_by(the_table.id).order_by(func.lower(the_table.name)).all()

        elif column == self.Columns.INGREDIENTLIST_ENTRIES:
            # Potential effects of Drag & Drop
            if len(self._item_lists[self.Columns.ITEMS]) > 0:
                item = self._item_lists[self.Columns.ITEMS][parent_row][0]

                # Copy the lists. Otherwise - when cleared - they would be erased from the
                # database itself: items/recipes are sqlalchemy lists, very convenient - but changes
                # there will cause database changes, too, so clearing() such a list will cause the references
                # to be deleted for real.
                item_list = None
                if self.root_row == self.RootItems.INGREDIENTS:
                    item_list = item.items
                else:
                    item_list = item.ingredientlist
                self._item_lists[column] = [item_data for item_data in item_list]
        else:
            return 0

        return len(self._item_lists[column])

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        # TODO: Maybe test for the role?
        value = nullify(value)
        if value is None:
            return False

        column = index.internalId()
        row = index.row()
        root_row = self._parent_row[self.Columns.ROOT]

        item = None
        if column == self.Columns.INGREDIENTLIST_ENTRIES:
            item = self._item_lists[self.Columns.INGREDIENTLIST_ENTRIES][row]
        else:
            item = self._item_lists[column][row][0]

        if item.name == value:
            # User has double clicked without changing the value
            return False

        # Test if the value already exists - but only in case of items.
        if column == self.Columns.ITEMS:
            the_table = self._first_column[root_row][0]
            duplicate = self._session.query(the_table).filter(the_table.name == value).first()
            if duplicate:
                if duplicate == item:
                    # The same item - user has double clicked and then again. Nothing to do here.
                    return False
                else:
                    # Duplicate item. There three possible ways to deal with this:
                    # 1.) Silently discard the change
                    # 2.) Open a Error dialog telling the user about the problem
                    # 3.) Like in drag&drop, merge both items.

                    # Currently: #2

                    self.illegalValue.emit(misc.ValueError.ISDUPLICATE, value)
                    return False

        self.changed.emit()
        item.name = value
        self.dataChanged.emit(index, index)
        return True
