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

from PyQt5 import QtWidgets
from babel.numbers import parse_decimal

from qisit.core.db import data
from qisit.core.util import nullify
from qisit.core import default_locale
from qisit.qt.misc.lstrip_validator import LStripValidator
from qisit.qt.recipewindow.ui import amount_editor


class AmountEditor(QtWidgets.QWidget, amount_editor.Ui_amountEditor):
    """
    A LineEdit (amount) and ComboBox (unit) combined into one widget. Used as an editor both in the TreeView and
    in the RecipeWindow
    """

    @classmethod
    def parse_amount(cls, amount: str, locale=default_locale):
        """
        Parses an amount string

        Args:
            amount (): The amount string to parse
            locale: The user's locale for parsing

        Returns:
            (float, float): amount and range amount

            Both values can be none (although a amount of none and a range amount with a value isn't legal) with a
            valid amount_string - for example "some" wouldn't have any amount

        Raises:
            ValueError: The amount string is invalid
        """

        # An amount can have the following valid formats
        # 1.) None/Empty string ("Some")
        # 2.) A single amount (the usual case): "5 kg")
        # 3.) A range amount: "5 - 7"

        # 1.) - empty string
        if nullify(amount) is None:
            return None, None

        # 2.) and 3.)
        values = amount.split("-")
        if (len(values)) == 1:
            # Only one value (amount)
            return float(parse_decimal(amount, locale)), None

        if len(values) > 2:
            # More than one -
            raise ValueError()

        amount_value = None
        range_value = None

        if nullify(values[0]) is not None:
            amount_value = float(parse_decimal(values[0], locale))
        if nullify(values[1]) is not None:
            range_value = float(parse_decimal(values[1], locale))

        # Something on the line of "- 5"
        if amount_value is None and range_value is not None:
            raise ValueError()

        # Just a convenience - sort both values
        if amount_value is not None and range_value is not None:
            if amount_value > range_value:
                amount_value, range_value = range_value, amount_value

        return amount_value, range_value

    def __init__(self, parent=None):
        super().__init__()
        super(QtWidgets.QWidget, self).__init__(parent)
        self.setupUi(self)
        self._lstrip_validator = LStripValidator()
        self.amountLineEdit.setValidator(self._lstrip_validator)
        self.unitComboBox.setValidator(self._lstrip_validator)

    def amount(self) -> ((float, float), bool):
        """
        Gets the amount entered in the amount text field

        Returns:
            A tuple consisting of a float tuple (amount, range_amount) and a bool if the amount string is valid

        """

        amount = None
        range_amount = None
        valid = True
        try:
            amount, range_amount = self.parse_amount(self.amountLineEdit.text())
        except ValueError:
            valid = False

        return (amount, range_amount), valid

    def seteditable(self, editable: bool):
        """
        Sets both widgets editable (or not)
        Args:
            editable ():

        Returns:

        """
        self.amountLineEdit.setReadOnly(not editable)
        self.unitComboBox.setEnabled(editable)

    def unit(self) -> data.IngredientUnit:
        """
        Gets the unit selected in the combobox, creating it if necessery

        Returns:

        """
        unit_text = self.unitComboBox.currentText().strip()
        if unit_text not in data.IngredientUnit.unit_dict:
            # This will also create the new unit and update the dictionary
            self.unitComboBox.addItem(unit_text)
            self.unitComboBox.model().reload_model()
            index = self.unitComboBox.findText(unit_text)
            self.unitComboBox.setCurrentIndex(index)
        return data.IngredientUnit.unit_dict[unit_text]
