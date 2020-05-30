""" The model for ingredient's tree """

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

import math
import pickle
import typing
from enum import IntEnum

from PyQt5 import QtCore, QtGui
from sqlalchemy import orm

from qisit import translate
from qisit.core.db import data
from qisit.core.util import nullify


# Maybe a proxy model would be more efficient?
class IngredientTreeViewModel(QtGui.QStandardItemModel):
    class IngredientColumns(IntEnum):
        """ Symbolic column names """
        INGREDIENT = 0
        AMOUNT = 1
        ALTERNATIVE = 2
        OPTIONAL = 3
        POSITION = 4
        INGREDIENTLISTROW = 5

    class IngredientLevels(IntEnum):
        """ Depth of the tree """
        ROOT = 0
        INGREDIENT = 1
        ALTERNATIVE = 2
        ALTERNATIVEGROUP = 3

    editable_columns = (IngredientColumns.INGREDIENT, IngredientColumns.AMOUNT)
    """ Which columns can be edited? Optional is checkable, not editable """

    dataToBeChanged = QtCore.pyqtSignal()
    """ Emitted just before a value is to be changed - needed for the optional checkbox.  """

    firstColumnSpanned = QtCore.pyqtSignal(int, QtCore.QModelIndex)
    """ Emitted when a group has been added to model """

    mime_type = "application/x-qisit-dataeditor"
    """ Drag & Drop """

    def __init__(self, recipe: data.Recipe):
        super().__init__()
        self._translate = translate
        self._recipe = recipe
        self.__editable = False

        # For the group
        self._bold_font = QtGui.QFont()
        self._bold_font.setBold(True)

        # Alternative texts
        self.alternative_or = self._translate("RecipeWindow", "or")
        self.alternative_and = self._translate("RecipeWindow", "and")

        self.factor = 1.0

    @property
    def editable(self) -> bool:
        return self.__editable

    @editable.setter
    def editable(self, editable: bool):
        self.__editable = editable
        self._set_items_editable(editable=editable, parent=self.invisibleRootItem().index())

    def _get_ingredient_list_indexes(self, parent: QtCore.QModelIndex, index_set: typing.Set[int]):
        """
        Gets all ingredients list indexes (the index of recipe's ingredient_list stored in the model's column)

        Args:
            parent (): The parent index
            index_set ():  The set to store the integer indexes into

        Returns:

        """

        for row in range(0, self.rowCount(parent)):
            ingredient_index = self.index(row, self.IngredientColumns.INGREDIENT, parent)
            ingredient_list_index = self.index(row, IngredientTreeViewModel.IngredientColumns.INGREDIENTLISTROW, parent)
            index_set.add(int(ingredient_list_index.data(QtCore.Qt.DisplayRole)))

            if self.hasChildren(ingredient_index):
                self._get_ingredient_list_indexes(ingredient_index, index_set)

    def _recalculate_amount_items(self, parent: QtCore.QModelIndex):
        """
        Recalculates all the amount items (just for display, no changes in the database)

        Args:
            parent ():

        Returns:

        """

        rows = self.rowCount(parent)
        for row in range(0, rows):
            ingredient_index = self.index(row, self.IngredientColumns.INGREDIENT, parent)
            self._recalculate_amount_item(ingredient_index)
            if self.hasChildren(ingredient_index):
                self._recalculate_amount_items(ingredient_index)

    def _recalculate_amount_item(self, ingredient_index: QtCore.QModelIndex):
        """
        Recalulate one amount item

        Args:
            ingredient_index (): The index of the ingredient item

        Returns:

        """
        ingedient_list_index = ingredient_index.siblingAtColumn(self.IngredientColumns.INGREDIENTLISTROW)
        ingredient = self._recipe.ingredientlist[ingedient_list_index.data(int(QtCore.Qt.DisplayRole))]
        amount_index = ingedient_list_index.siblingAtColumn(self.IngredientColumns.AMOUNT)

        self.setData(amount_index, ingredient.amount_string(factor=self.factor), QtCore.Qt.DisplayRole)

        # Display a small icon to indicate that the amount is calculated and not the amount stored in the database
        if math.isclose(self.factor, 1.0):
            self.itemFromIndex(amount_index).setIcon(QtGui.QIcon())

            # (Re)set the user data - otherwise the editor will do odd things when the amounts have been scaled
            self.setData(amount_index, ((ingredient.amount, ingredient.range_amount), ingredient.unit.unit_string()),
                         QtCore.Qt.UserRole)
        else:
            if ingredient.amount:
                self.itemFromIndex(amount_index).setIcon(QtGui.QIcon(":/icons/calculator.png"))

    def _renumber_tree(self, parent: QtCore.QModelIndex, prefix=0, level=0):
        """
        Renumbers the tree (with pseudo positions to avoid constraints) so the database is in sync
        with the model. Note: After the renumbering another pass is necessary to change the negative
        pseudo position into real one

        Args:
            parent (): The parent index
            prefix (): The decimal prefix (for example 9900000 for the global group)
            level (): The level of the tree

        Returns:

        """

        model_rows = self.rowCount(parent)

        # The offset for the child entries:
        # The first (if present, that is) groups has 00000000 as position. It's first element therefore
        # 00010000 (offset = 1)
        offset = 1
        for model_row in range(0, model_rows):

            ingredient_index = self.index(model_row, self.IngredientColumns.INGREDIENT, parent)
            ingredient = self.itemFromIndex(ingredient_index)

            position_index = self.index(model_row, self.IngredientColumns.POSITION, parent)
            position = self.itemFromIndex(position_index)

            ingredient_list_row_index = self.index(model_row, self.IngredientColumns.INGREDIENTLISTROW, parent)

            # Some special considerations for the root level
            if level == self.IngredientLevels.ROOT:
                #  groups start at 0 (the first group, 98 would be the last possible one)
                offset = 0

                if not data.IngredientListEntry.is_group(int(ingredient_index.data(QtCore.Qt.UserRole))):
                    # A root-level ingredient. These have the (pseudo) group 99.
                    prefix = data.IngredientListEntry.GROUP_GLOBAL * data.IngredientListEntry.GROUP_FACTOR

                    # Although the items are on the model's root level, they are in fact children of the
                    # invisible group 99, so they have to treated accordingly
                    level = self.IngredientLevels.INGREDIENT

                    # The groups have ended and a new counting begins - otherwise they would start with 99<modelrow>
                    offset = - model_row + 1

            # Some wild calculations - this is basically a kind of shift right in decimal:
            # 99000000 <-- prefix
            # 6 <-- model_row
            # offset = -5
            # level =1
            # model_row + offset becomes the internal row, now matter on what level
            # result: 99010000
            # level 2 would result in 99000100
            new_position = prefix + (model_row + offset) * 10 ** (6 - (level * 2))

            # Similar to the image list: Due to the unique constraint it's necessary to set up temp positions
            ingredient_list_position = int(ingredient_list_row_index.data(role=QtCore.Qt.DisplayRole))
            self._recipe.ingredientlist[ingredient_list_position].position = (-1) * new_position - 1
            position.setData(new_position, role=QtCore.Qt.DisplayRole)
            ingredient.setData(new_position, role=QtCore.Qt.UserRole)

            if self.hasChildren(ingredient_index):
                self._renumber_tree(parent=ingredient_index, prefix=new_position, level=level + 1)

    def _set_alternatives_text(self, parent: QtCore.QModelIndex, level=0):
        """
        Sets the "alternative" field after a drag & drop-operation on all items.

        Args:
            parent (): The parent index
            level (): the level of the tree which the method traverses recursively

        Returns:

        """

        new_level = level
        for row in range(0, self.rowCount(parent)):
            ingredient_index = self.index(row, self.IngredientColumns.INGREDIENT, parent)

            # For root level ingredients increase the level (0 is the invisible root item) so there wont' be a
            # difference between grouped and ungrouped (root level) ingredients
            if level == self.IngredientLevels.ROOT and not data.IngredientListEntry.is_group(
                    int(ingredient_index.data(QtCore.Qt.UserRole))):
                new_level = self.IngredientLevels.INGREDIENT
            alternative_index = self.index(row, self.IngredientColumns.ALTERNATIVE, parent)
            alternative_text = None

            if new_level == self.IngredientLevels.ALTERNATIVE:
                alternative_text = self.alternative_or
            elif new_level == self.IngredientLevels.ALTERNATIVEGROUP:
                alternative_text = self.alternative_and

            self.setData(alternative_index, alternative_text, QtCore.Qt.DisplayRole)
            if self.hasChildren(ingredient_index):
                self._set_alternatives_text(parent=ingredient_index, level=new_level + 1)

    def _set_items_editable(self, editable: bool, parent: QtCore.QModelIndex):
        """
        Recursively sets all items belonging to the parent editable

        Args:
            editable (): editable
            parent (): the parent item

        Returns:

        """

        rows = self.rowCount(parent)
        for row in range(0, rows):
            ingredient_index = self.index(row, self.IngredientColumns.INGREDIENT, parent)
            amount_index = self.index(row, IngredientTreeViewModel.IngredientColumns.AMOUNT, parent)
            optional_index = self.index(row, IngredientTreeViewModel.IngredientColumns.OPTIONAL, parent)

            if ingredient_index.isValid():
                self.itemFromIndex(ingredient_index).setEditable(editable)
            if amount_index.isValid():
                # If the amounts are scaled, editing them would be quite confusing for the user
                self.itemFromIndex(amount_index).setEditable(math.isclose(self.factor, 1.0))
            if ingredient_index.isValid():
                self.itemFromIndex(ingredient_index).setEditable(editable)
            if optional_index.isValid():
                self.itemFromIndex(optional_index).setCheckable(editable)

            # Only the ingredient column can have children
            if self.hasChildren(ingredient_index):
                self._set_items_editable(editable, ingredient_index)

    def add_new_group(self, group_entry: data.IngredientListEntry):
        """
        Adds a new group to the model at the correct position, creating the row in the process

        Args:
            group_entry (): The group entry

        Returns:

        """
        new_row = self.setup_row(group_entry)

        # Depending on the position either a insert (between rows) or an append (after the last row) is the way to go
        insert = False
        row = 0

        for row in range(0, self.rowCount()):
            position = int(self.index(row, self.IngredientColumns.POSITION, self.invisibleRootItem().index()).data(
                QtCore.Qt.DisplayRole))

            # The first root-level item is where we can stop the search. Since the root level group has no group entry
            # it's safe to test if the item belongs to the global group
            if data.IngredientListEntry.item_group(
                    position) == data.IngredientListEntry.GROUP_GLOBAL * data.IngredientListEntry.GROUP_FACTOR:
                # Reached the first real ingredient
                insert = True
                break

        if insert:
            self.insertRow(row, new_row)
        else:
            # Reached the end of the list without finding a real ingredient -> only groups on the root level
            # (or an empty tree)
            self.appendRow(new_row)
            row += 1

        self.firstColumnSpanned.emit(row, self.invisibleRootItem().index())

    def canDropMimeData(self, mime_data: QtCore.QMimeData, action: QtCore.Qt.DropAction, target_row: int,
                        target_column: int, target_parent: QtCore.QModelIndex) -> bool:

        # Some tests if drop is possible at the given location.

        # Only a drop - flags non withstanding - on the ingredient column is possible
        if target_column != self.IngredientColumns.INGREDIENT and target_column != -1:
            return False

        # A drop on the root column
        if target_parent.isValid() and target_parent.column() != self.IngredientColumns.INGREDIENT:
            return False

        drop_on_item = target_row == -1 and target_column == -1

        # Test all dragged item - if one of those fails, a drop doesn't make sense

        # Unfortunately we cannot rely on item's position - because the user might have dragged the items before
        # and position might not reflect the position inside the tree anymore. This is trade off: Either renumber
        # the tree's content each time a drag has occurred - and causing database load - or renumber the tree only
        # when the user saves the changes, making it more difficult to determine the item's status
        # (group, alternative..)
        index_list = pickle.loads(mime_data.data(self.mime_type))
        for index in index_list:
            parent_item = index.parent()

            # -------------------- Groups ---------------------
            # This is the only case where item_position can be safely used: A group can only be moved within the
            # root level, so even if the position doesn't reflect the model's position, it's OK to use the
            # information to determine if it's a group or a root level ingredient
            if data.IngredientListEntry.is_group(int(index.data(QtCore.Qt.UserRole))):
                # A group cannot be dropped on another group or item
                if drop_on_item:
                    # Attempted drop on an item, no matter on which level
                    return False
                else:
                    # A move before/after target_parent's item
                    if target_parent.isValid():
                        # There's a parent (i.e. a level below root)
                        return False

                    if index.row() == target_row:
                        # Drag in front of itself. Makes no sense
                        return False

                    # A group can only be moved inside the "group window", i.e. between the tree's very first row
                    # and before the first root-level ingredient
                    if target_row > 0:
                        previous_index = self.index(target_row - 1, self.IngredientColumns.INGREDIENT,
                                                    QtCore.QModelIndex())
                        if previous_index == index:
                            # Drag behind itself. Makes no sense
                            return False
                        if not data.IngredientListEntry.is_group(int(previous_index.data(QtCore.Qt.UserRole))):
                            # No group - trying to move the group into the root level ingredients
                            return False

            # -------------------- Ingredients --------------------
            else:
                # Two case: Either a move or a drop on an item (i.e. attach it to parent)
                # First, drop on an item
                if drop_on_item:
                    if not target_parent.isValid():
                        return False

                    # Drop on a group
                    if data.IngredientListEntry.is_group(int(target_parent.data(QtCore.Qt.UserRole))):
                        # The item is allowed to have children, but only if it's an ingredient
                        # (and not alternative ingredients, otherwise the level would change: and becomes or and or
                        # becomes the ingredient. This isn't what the user really wants)
                        if self.hasChildren(index):
                            if self.depth(index) != self.IngredientLevels.INGREDIENT:
                                return False

                        if self.rowCount(index) >= data.IngredientListEntry.MAX_ENTRIES:
                            return False

                        if parent_item is not None and parent_item == target_parent:
                            return False
                    else:
                        # Only accept items that haven't got children. Otherwise this would lead to odd results:
                        # Ingredient B which has an alternative C (B OR C) dropped on Ingredient A would lead to:
                        # Ingredient A OR Ingredient B AND Ingredient C, which is clearly not right. Alternatively
                        # do some major internal rewriting
                        if self.hasChildren(index):
                            return False

                        # Only a certain level can be accepted
                        if self.depth(target_parent) >= self.IngredientLevels.ALTERNATIVEGROUP:
                            return False

                        if self.rowCount(target_parent) >= data.IngredientListEntry.MAX_ENTRIES:
                            return False
                else:
                    # Move
                    parent_level = self.IngredientLevels.ROOT
                    if target_parent.isValid():
                        parent_level = self.depth(target_parent)
                        if self.rowCount(target_parent) >= data.IngredientListEntry.MAX_ENTRIES:
                            return False

                    # The root-level ingredients have to be beneath the grouped items
                    if parent_level == self.IngredientLevels.ROOT:
                        number_of_root_items = self.invisibleRootItem().rowCount()

                        # target_row == number_of_root_items would mean an append at the end of the list,
                        # which would be perfectly acceptable
                        if target_row < number_of_root_items:
                            next_index = self.index(target_row, self.IngredientColumns.INGREDIENT, QtCore.QModelIndex())
                            if data.IngredientListEntry.is_group(int(next_index.data(QtCore.Qt.UserRole))):
                                # trying to move an ingredient item before a group
                                return False

                    # Contrary to drop, moving an item with children is allowed.. but only if its moved on the
                    # same level. Otherwise the tree would either increase it's depth to a invalid value or
                    # something similar confusing like dropping an item with children on an item would occur.
                    if self.hasChildren(index):
                        # Since parent is always one level higher than the item
                        if parent_level != self.depth(index) - 1:
                            return False

        return super().canDropMimeData(mime_data, action, target_row, target_column, target_parent)

    def delete_ids(self, session: orm.Session, ids: typing.List[int]):
        """
        Deletes all rows with the ingredient list ids

        Args:
            session (): The db session
            ids (): The ids to delete

        Returns:

        """

        # This is a little bit awkward: When the user deletes a row which has got children the model will silently
        # delete all the children (which is fine) but only one call of removeRows and friends ist made - the
        # parent row. So the easiest workaround (apart from intercepting those removeRows calls and deleting the
        # children at the database): After deleting is complete take a look which ids remained and compare them to
        # the ids stored in the database

        # First delete all rows containing the ids
        for id_to_delete in ids:
            items = self.findItems(str(id_to_delete), QtCore.Qt.MatchRecursive,
                                   IngredientTreeViewModel.IngredientColumns.INGREDIENTLISTROW)
            if len(items) > 0:
                # Found: hasn't been deleted by parent (yet)
                ingredient_list_row_item = items[0]
                parent = ingredient_list_row_item.parent()
                if parent is None:
                    parent = self.invisibleRootItem()
                self.removeRow(ingredient_list_row_item.row(), parent.index())

        # Will contain all remaining ids
        remaining_indexes_set = set()
        self._get_ingredient_list_indexes(self.invisibleRootItem().index(), remaining_indexes_set)

        # The indexes stored in the database
        ingredient_list_set = set()
        for index in range(0, len(self._recipe.ingredientlist)):
            ingredient_list_set.add(index)

        # The difference between the ids in the database and the remaining id is the set of actually deleted ids
        indexes_deleted = ingredient_list_set.difference(remaining_indexes_set)
        for index in indexes_deleted:
            session.delete(self._recipe.ingredientlist[index])

        session.refresh(self._recipe)
        self.set_ingredient_list_row()
        self.save_tree(session)

    def depth(self, index: QtCore.QModelIndex, level: int = 0):
        """
        Calculate the depth of the index in the tree (root = 0, AND = 3)

        Args:
            index ():
            level ():
        Returns:

        """
        parent = index.parent()
        if parent.isValid():
            level = self.depth(parent, level + 1)
        else:
            # Allow corrections for ingredients at root level
            if not data.IngredientListEntry.is_group(int(index.data(QtCore.Qt.UserRole))):
                level += 1
        return level

    def dropMimeData(self, mime_data: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                     parent: QtCore.QModelIndex) -> bool:

        self.dataToBeChanged.emit()

        dropped = super().dropMimeData(mime_data, action, row, column, parent)

        if dropped:
            self._set_alternatives_text(self.invisibleRootItem().index())
            current_row = row
            index_list = pickle.loads(mime_data.data(self.mime_type))
            # If a group has been moved, restore the column spanning
            for index in index_list:
                if data.IngredientListEntry.is_group(int(index.data(QtCore.Qt.UserRole))):
                    self.firstColumnSpanned.emit(current_row, self.invisibleRootItem().index())
                current_row += 1
        return dropped

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        """ The headers - translated """

        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            _translate = self._translate
            # Like recipe_table_model, maybe use a dictionary?

            if section == self.IngredientColumns.INGREDIENT:
                return _translate("RecipeWindow", "Ingredient")
            elif section == self.IngredientColumns.AMOUNT:
                return _translate("RecipeWindow", "Amount")
            elif section == self.IngredientColumns.ALTERNATIVE:
                return _translate("RecipeWindow", "Alternative")
            elif section == self.IngredientColumns.OPTIONAL:
                return _translate("RecipeWindow", "Optional")
            elif section == self.IngredientColumns.POSITION:
                # Invisible, therefore no translation needed
                return "Position"
            elif section == self.IngredientColumns.INGREDIENTLISTROW:
                # same here
                return "Ingredient list row"

    def load_model(self):
        """
        Creates the model for the TreeView

        Returns:

        """

        self.clear()
        # Convert the internal representation to an actual tree
        ingredientlist_index = 0

        for ingredientlist_entry in self._recipe.ingredientlist:

            new_row = self.setup_row(ingredientlist_entry)
            new_row[self.IngredientColumns.INGREDIENTLISTROW].setData(ingredientlist_index, QtCore.Qt.DisplayRole)

            if ingredientlist_entry.is_group(ingredientlist_entry.position):
                # Append it and tell the view that this row should span it's first column
                self.invisibleRootItem().appendRow(new_row)
                current_row = self.rowCount() - 1
                self.firstColumnSpanned.emit(current_row, self.invisibleRootItem().index())
            else:
                # A standard ingredient entry. Attach it to a parent
                parent_position = data.IngredientListEntry.item_parent(ingredientlist_entry.position)
                if parent_position == data.IngredientListEntry.GROUP_GLOBAL * data.IngredientListEntry.GROUP_FACTOR:
                    # The item in question is on the root level
                    self.invisibleRootItem().appendRow(new_row)
                else:
                    # Find the appropriate parent
                    position_item = self.findItems(str(parent_position), QtCore.Qt.MatchRecursive,
                                                   IngredientTreeViewModel.IngredientColumns.POSITION)[0]
                    ingredientparent_index = position_item.index().sibling(position_item.row(),
                                                                           IngredientTreeViewModel.IngredientColumns.INGREDIENT)
                    ingredientparent_item = self.itemFromIndex(ingredientparent_index)
                    ingredientparent_item.appendRow(new_row)

                # Optional icon
                ingredient = ingredientlist_entry.ingredient
                if ingredient.icon is not None:
                    pixmap = QtGui.QPixmap()
                    if pixmap.loadFromData(ingredient.icon):
                        new_row[self.IngredientColumns.INGREDIENT].setData(pixmap, QtCore.Qt.DecorationRole)

            ingredientlist_index += 1

    def mimeData(self, indexes: typing.Iterable[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """

        Args:
            indexes ():

        Returns:

        """

        index_list = [(index.row(), index.column()) for index in indexes if index.column() == self.IngredientColumns.INGREDIENT]

        mime_data = QtCore.QMimeData()
        mime_data.setData(self.mime_type, pickle.dumps(index_list))
        return mime_data

    def save_tree(self, session: orm.Session):
        """
        Saves the tree's content to the database

        Args:
            session ():

        Returns:

        """

        # First renumber the tree's content for temporary  positions
        self._renumber_tree(self.invisibleRootItem().index())
        session.merge(self._recipe)
        session.refresh(self._recipe)

        # Now the final positions
        for item in self._recipe.ingredientlist:
            item.position = -1 * (item.position + 1)
        session.merge(self._recipe)
        session.refresh(self._recipe)

        # Finally set the relationship between items and database right again
        self.set_ingredient_list_row()

    def scale_amounts(self, factor: float):
        """
        Scales the amounts

        Args:
            factor (): The scale factor

        Returns:

        """
        self.factor = factor
        root = self.invisibleRootItem().index()
        self._recalculate_amount_items(root)
        self._set_items_editable(self.editable, root)

    def set_ingredient_list_row(self):
        """
        Sets the ingredient list index row correctly so it reflects recipe's ingredient_list again (after a
        deletion or insert or a renumbering of the tree, the ingredient_list will be changed thoroughly.

        Returns:

        """

        for ingredientlist_index in range(0, len(self._recipe.ingredientlist)):
            ingredientlist_item = self._recipe.ingredientlist[ingredientlist_index]
            position_item = self.findItems(str(ingredientlist_item.position), QtCore.Qt.MatchRecursive,
                                           IngredientTreeViewModel.IngredientColumns.POSITION)[0]
            ingredientlist_rowitem_index = position_item.index() \
                .sibling(position_item.row(), IngredientTreeViewModel.IngredientColumns.INGREDIENTLISTROW)
            self.setData(ingredientlist_rowitem_index, ingredientlist_index, role=QtCore.Qt.DisplayRole)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if index.isValid():
            if role in (QtCore.Qt.EditRole, QtCore.Qt.CheckStateRole, QtCore.Qt.UserRole):

                # For the optional column. Otherwise ingredient and amount have told the controller that something
                # is going to change
                self.dataToBeChanged.emit()

                column = index.column()

                # The item to manipulate
                ingredient_list_item = self._recipe.ingredientlist[int(
                    index.siblingAtColumn(self.IngredientColumns.INGREDIENTLISTROW).data(role=QtCore.Qt.DisplayRole))]
                if column == self.IngredientColumns.OPTIONAL and role == QtCore.Qt.CheckStateRole:
                    ingredient_list_item.optional = (value == QtCore.Qt.Checked)

                if column == self.IngredientColumns.INGREDIENT and role == QtCore.Qt.EditRole:
                    new_name = nullify(value)

                    # There's no point in having a empty name - well, in that case we could
                    # display/use the ingredient's generic name, but this might be quite confusing
                    # for the user
                    if new_name is not None:
                        old_name = ingredient_list_item.name

                        # This means that a change in the group's name will be visible to all
                        # recipes having this pseudo ingredient. Not exactly sure if it's the
                        # right thing to to do, on the other hand it's more consistent
                        if old_name is None and ingredient_list_item.ingredient.is_group:
                            ingredient_list_item.ingredient.name = new_name
                        else:
                            ingredient_list_item.name = new_name

                if column == self.IngredientColumns.AMOUNT and role == QtCore.Qt.UserRole:
                    (amount, range_amount), unit_string = value
                    ingredient_list_item.amount = amount
                    ingredient_list_item.range_amount = range_amount
                    ingredient_list_item.unit = data.IngredientUnit.unit_dict[unit_string]

                    self.setData(index, QtCore.QVariant(ingredient_list_item.amount_string()), QtCore.Qt.DisplayRole)

            return super().setData(index, value, role)
        return False

    def setup_row(self, ingredientlist_entry: data.IngredientListEntry) -> typing.List[QtGui.QStandardItem]:
        """
        Sets up a new row ready to be added to a parent

        Args:
            ingredientlist_entry (): The entry

        Returns:
            A row of QStandardItems, suitable for adding to the tree
        """

        new_row = [QtGui.QStandardItem() for column in self.IngredientColumns]

        # It's possible that - instead of a individual ingredient name - the "generic" name is being used. This
        # is always the case when the "ingredient" is in fact a group name.
        name = ingredientlist_entry.name
        if name is None:
            name = ingredientlist_entry.ingredient.name

        # Default item flags. Only the ingredient column allows drops
        itemflags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled

        #  -------------------- Ingredient --------------------
        new_row[self.IngredientColumns.INGREDIENT].setData(QtCore.QVariant(name), role=QtCore.Qt.DisplayRole)
        new_row[self.IngredientColumns.INGREDIENT].setData(QtCore.QVariant(ingredientlist_entry.position),
                                                           role=QtCore.Qt.UserRole)
        if self.editable:
            new_row[self.IngredientColumns.INGREDIENT].setFlags(
                itemflags | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEditable)
        else:
            new_row[self.IngredientColumns.INGREDIENT].setFlags(itemflags | QtCore.Qt.ItemIsDropEnabled)

        # -------------------- Position --------------------
        # This is needed to find the parent of a a given item. Otherwise the data in ingredient's UserRole would do
        new_row[self.IngredientColumns.POSITION].setData(QtCore.QVariant(ingredientlist_entry.position),
                                                         role=QtCore.Qt.DisplayRole)

        if ingredientlist_entry.is_group(ingredientlist_entry.position):
            # Not much to do if it's a group
            new_row[self.IngredientColumns.INGREDIENT].setData(self._bold_font, role=QtCore.Qt.FontRole)
        else:
            # A real ingredient
            # -------------------- Amount --------------------
            amount = ingredientlist_entry.amount_string()
            unit = ingredientlist_entry.unit.unit_string()

            new_row[self.IngredientColumns.AMOUNT].setData(QtCore.QVariant(amount), QtCore.Qt.DisplayRole)
            new_row[self.IngredientColumns.AMOUNT].setData(
                ((ingredientlist_entry.amount, ingredientlist_entry.range_amount), unit), QtCore.Qt.UserRole)

            if self.editable:
                new_row[self.IngredientColumns.AMOUNT].setFlags(itemflags | QtCore.Qt.ItemIsEditable)
            else:
                new_row[self.IngredientColumns.AMOUNT].setFlags(itemflags)

            # -------------------- Alternatives (or, and) --------------------
            new_row[self.IngredientColumns.ALTERNATIVE].setFlags(itemflags)
            if data.IngredientListEntry.is_alternative(ingredientlist_entry.position):
                new_row[self.IngredientColumns.ALTERNATIVE].setData(self.alternative_or, QtCore.Qt.DisplayRole)
            elif data.IngredientListEntry.is_alternative_grouped(ingredientlist_entry.position):
                new_row[self.IngredientColumns.ALTERNATIVE].setData(self.alternative_and, QtCore.Qt.DisplayRole)
            else:
                new_row[self.IngredientColumns.ALTERNATIVE].setData(None, QtCore.Qt.DisplayRole)

            # -------------------- Optional --------------------
            if self.editable:
                new_row[self.IngredientColumns.OPTIONAL].setFlags(itemflags | QtCore.Qt.ItemIsUserCheckable)
            else:
                new_row[self.IngredientColumns.OPTIONAL].setFlags(itemflags)
            if ingredientlist_entry.optional:
                new_row[self.IngredientColumns.OPTIONAL].setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
            else:
                new_row[self.IngredientColumns.OPTIONAL].setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

        return new_row
