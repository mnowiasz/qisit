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
        """ Symoblic column names """

        ROOT = 0
        ITEMS = 1
        REFERENCED = 2
        RECIPES = 3  # Only for ingredients, otherwise REFERENCED is the last column

    class FirstColumnData(IntEnum):
        """ Symbolic names for self:_first_column """
        TABLE = 0
        NAME = 1
        ICON = 2

    mime_type = "application/x-qisit-dataeditor"

    dataChanged = QtCore.pyqtSignal()
    """ Data have been changed """

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

        self._model_changed = False

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

        # For whatever reason rowCount() is called multiple times (at least four). This is to prevent unnecessary
        # loading
        self._item_parent_rows = [None for column in self.Columns]

        # Item is a CLDR unit, therefore not editable (the name of the item is generated dymically using the
        # user's locale
        self._cldr_font = QtGui.QFont()
        self._cldr_font.setItalic(True)

        # Base unit - neither editable nor deletable
        self._baseunit_font = QtGui.QFont()
        self._baseunit_font.setBold(True)
        self._baseunit_font.setItalic(True)

        # Recipes that are affected by the changes
        self.affected_recipe_ids = set()

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
                QtCore.Qt.UserRole):
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

        root_row = self._parent_row[self.Columns.ROOT]
        if column == self.Columns.ITEMS:
            item = self._item_lists[self.Columns.ITEMS][row]
            count = item[1]
            if role == QtCore.Qt.UserRole:
                return QtCore.QVariant(count)

            if role == QtCore.Qt.DisplayRole:
                title = f"{item[0].name} ({count})"
                if root_row == self.RootItems.INGREDIENTUNITS:
                    # Display the unit in the user's locale
                    if item[0].cldr:
                        title = f"{item[0].unit_string()} ({count})"
                return QtCore.QVariant(title)

            if role == QtCore.Qt.EditRole:
                return QtCore.QVariant(item[0].name)

            if root_row == self.RootItems.INGREDIENTUNITS:
                ingredient_unit = item[0]
                is_base_unit = ingredient_unit in data.IngredientUnit.base_units.values()

                if role == QtCore.Qt.FontRole:
                    if is_base_unit:
                        return QtCore.QVariant(self._baseunit_font)
                    elif ingredient_unit.cldr:
                        return QtCore.QVariant(self._cldr_font)

                if role == QtCore.Qt.DecorationRole:
                    return QtCore.QVariant(QtGui.QIcon(self._ingredient_unit_icons[ingredient_unit.type_]))

        elif column == self.Columns.REFERENCED:
            item = self._item_lists[column][row]
            if role == QtCore.Qt.UserRole:
                if root_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTUNITS):
                    # Ingredients and ingredient units  have a fourth column - the recipe
                    return 1
                else:
                    return 0

            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
                # Different items have different leaves: Author, Cuisine, ... have the recipes' belonging to them
                # displayed in it's leaf ("referenced") column. Ingredients on the other hand have got
                # Ingredientlist entries displayed there. Recipes have got a title, all other tables a name (this was
                # probably an oversight, if a recipe would have a name instead of a title, the code underneath would be
                # unnecessary). But too much bother to change the database now.
                if root_row in (self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTUNITS):
                    return QtCore.QVariant(item.name)
                else:
                    return QtCore.QVariant(item.title)

        elif column == self.Columns.RECIPES:
            if role == QtCore.Qt.DisplayRole:
                recipe = self._item_lists[column][row]
                return QtCore.QVariant(recipe.title)
            if role == QtCore.Qt.UserRole:
                # Last column
                return 0
        return QtCore.QVariant(None)

    def dropMimeData(self, mimedata: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                     parent: QtCore.QModelIndex) -> bool:

        index_list = pickle.loads(mimedata.data(self.mime_type))
        target_row = parent.row()
        # Not used  currently - only drops on the Item columns are allowed
        target_column = parent.internalId()
        root_row = self._parent_row[self.Columns.ROOT]
        recipes_ids = set()
        self.dataChanged.emit()

        for (index_row, index_column) in index_list:
            if index_column == target_column:
                # Merge operation
                merge_item = self._item_lists[target_column][index_row][0]
                target_item = self._item_lists[target_column][target_row][0]

                # Merging an item with itself is useless
                if merge_item != target_item:
                    recipes_ids= recipes_ids.union([recipe.id for recipe in merge_item.recipes])
                    if root_row == self.RootItems.AUTHOR:
                        self.beginRemoveRows(self.createIndex(root_row, 0, self.Columns.ROOT), index_row, index_row)

                        self._session.query(data.Recipe).filter(data.Recipe.author_id == merge_item.id).update({data.Recipe.author_id: target_item.id}, synchronize_session='evaluate')
                        self._session.expire_all()
                        self._session.delete(merge_item)
                    elif root_row == self.RootItems.CUISINE:
                        self.beginRemoveRows(self.createIndex(root_row, 0, self.Columns.ROOT), index_row, index_row)
                        self._session.query(data.Recipe).filter(data.Recipe.cuisine_id == merge_item.id).update({data.Recipe.cuisine_id: target_item.id}, synchronize_session='evaluate')
                        self._session.expire_all()
                        self._session.delete(merge_item)
                        self.endRemoveRows()
                    elif root_row == self.RootItems.YIELD_UNITS:
                        self.beginRemoveRows(self.createIndex(root_row, 0, self.Columns.ROOT), index_row, index_row)
                        self._session.query(data.Recipe).filter(data.Recipe.yield_unit_id == merge_item.id).update({data.Recipe.yield_unit_id: target_item.id}, synchronize_session='evaluate')
                        self._session.expire_all()
                        self._session.delete(merge_item)
                        self.endRemoveRows()

        self._model_changed = True
        self.layoutChanged.emit()
        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        column = index.internalId()

        is_editable = False
        is_drop_enabled = False
        is_drag_enabled = False

        if column in (self.Columns.ITEMS, self.Columns.REFERENCED):

            # Only certain combinations of drag&drop make sense: The item column can drag itself on another item
            # and recipes can be dragged to another author or cuisine. All other combination aren't very useful
            is_drag_enabled = (column == self.Columns.ITEMS or self._parent_row[self.Columns.ROOT] in (
                self.RootItems.INGREDIENTS, self.RootItems.CUISINE))

            root_row = self._parent_row[self.Columns.ROOT]

            if column == self.Columns.ITEMS:
                is_drop_enabled = True
                if root_row == self.RootItems.INGREDIENTUNITS:
                    ingredient_unit = self._item_lists[self.Columns.ITEMS][index.row()][0]
                    is_editable = not ingredient_unit.cldr and not ingredient_unit in data.IngredientUnit.base_units.values()
                    is_drag_enabled = is_editable
                else:
                    is_editable = True
                    is_drag_enabled = True
            else:
                is_editable = root_row in (
                    self.RootItems.INGREDIENTS, self.RootItems.INGREDIENTGROUPS, self.RootItems.INGREDIENTUNITS)

        if is_editable:
            flags |= QtCore.Qt.ItemIsEditable

        if is_drop_enabled:
            flags |= QtCore.Qt.ItemIsDropEnabled

        if is_drag_enabled:
            flags |= QtCore.Qt.ItemIsDragEnabled

        return flags

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

    def mimeData(self, indexes: typing.Iterable[QtCore.QModelIndex]) -> QtCore.QMimeData:
        index_list = [(index.row(), index.internalId()) for index in indexes]

        mime_data = QtCore.QMimeData()
        mime_data.setData(self.mime_type, pickle.dumps(index_list))
        return mime_data

    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:

        # Again - the "display" column, *not* the model column (which is always 0)
        child_column = child.internalId()
        if child_column == self.Columns.ROOT:
            # The items on the root level have no parent
            return QtCore.QModelIndex()
        return self.createIndex(self._parent_row[child_column - 1], 0, child_column - 1)

    def reset(self):
        """
        Resets the model to the last state.

        Returns:

        """
        self._model_changed = True
        self.affected_recipe_ids.clear()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if parent.row() == -1:
            return self.RootItems.YIELD_UNITS + 1

        column = parent.internalId() + 1

        # Lazily load the columns. Note: Usually this is done using fetchMore() / canFetchMore. However, since
        # counting the rows and fetching the data at the same time is more efficient than first counting the rows
        # and then fetching the data (duplicating the same joins) this is done here
        parent_row = parent.row()

        # Depending on the previous content or the repeated calls of rowCount(), either load the content or
        # do nothing
        if parent_row != self._item_parent_rows[column] or self._model_changed:

            self._model_changed = False

            # Reset all further columns, otherwise odd things might happen: if the next column has the same parent_row
            # as before, it wouldn't be reloaded creating odd effects
            for the_column in range(column + 1, self.Columns.RECIPES + 1):
                self._item_parent_rows[the_column] = None
            self._item_parent_rows[column] = parent_row

            if column == self.Columns.ITEMS:
                the_table = self._first_column[parent_row][self.FirstColumnData.TABLE]

                # Construct the query
                query = None

                if parent_row == self.RootItems.INGREDIENTUNITS:
                    # Ingredients (or better: amount units) are rather special - due to the handling of
                    # CLDR the query has too little in common wit the other ones. There's also the one
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
                        query = self._session.query(the_table, func.count(data.Recipe.id).label("count"))

                        # Categories need an additional join
                        if parent_row == self.RootItems.CATEGORIES:
                            query = query.join(data.CategoryList, data.Category.id == data.CategoryList.category_id,
                                               isouter=True)

                        query = query.join(data.Recipe, isouter=True)

                    self._item_lists[column] = query.group_by(the_table.id).order_by(func.lower(the_table.name)).all()

            elif column == self.Columns.REFERENCED:
                item = self._item_lists[self.Columns.ITEMS][parent_row][0]
                root_row = self._parent_row[self.Columns.ROOT]

                # Copy the lists. Otherwise - when cleared - they would be erased from the
                # database itself: items/recipes are sqlalchemy lists, very convenient - but changes
                # there will cause database changes, too, so clearing() such a list will cause the references
                # to be deleted for real.
                item_list = None
                if root_row == self.RootItems.INGREDIENTS:
                    item_list = item.items
                elif root_row == self.RootItems.INGREDIENTUNITS:
                    item_list = item.ingredientlist
                else:
                    item_list = item.recipes
                self._item_lists[column] = [item_data for item_data in item_list]

            elif column == self.Columns.RECIPES:
                recipe = self._item_lists[self.Columns.REFERENCED][parent_row].recipe
                self._item_lists[column] = [recipe, ]
            else:
                return 0

        return len(self._item_lists[column])

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        value = nullify(value)

        if value is None:
            return False

        column = index.internalId()
        row = index.row()
        root_row = self._parent_row[self.Columns.ROOT]

        item = None
        if column == self.Columns.REFERENCED:
            item = self._item_lists[self.Columns.REFERENCED][row]
            changed_recipes = [item.recipe_id, ]
        else:
            item = self._item_lists[column][row][0]
            changed_recipes = [recipe.id for recipe in item.recipes]

        # Test if the value already exists
        the_table = self._first_column[root_row][0]
        duplicate = self._session.query(the_table).filter(the_table.name == value).first()
        if duplicate:
            if duplicate == item:
                # The same item. Nothing to do here.
                return False
            else:
                # Duplicate item. There three possible ways to deal with this:
                # 1.) Silently discard the change
                # 2.) Open a Error dialog telling the user about the problem
                # 3.) Like in drag&drop, merge both items.

                # Currently: Choice 1.)
                return False
        self.dataChanged.emit()
        self.affected_recipe_ids = self.affected_recipe_ids.union(changed_recipes)
        item.name = value
        return True
