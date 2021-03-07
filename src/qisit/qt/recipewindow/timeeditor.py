""" A time editor for the three time values (preparation, cooking and total) """

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

from PyQt5 import QtWidgets, Qt
from babel.units import get_unit_name
from qisit.core import default_locale

from qisit.qt.recipewindow.ui import time_editor


class TimeEditor(QtWidgets.QWidget, time_editor.Ui_timeEditor):
    valueChanged = Qt.pyqtSignal(int)
    """ Emitted when the value has changed """

    def __init__(self, parent=None):
        super().__init__()
        super(QtWidgets.QWidget, self).__init__(parent)
        self.setupUi(self)
        self.init_ui()
        self.__spinboxes = (self.minutesSpinBox, self.hoursSpinBox, self.daysSpinBox)

        for spinbox in self.__spinboxes:
            spinbox.valueChanged.connect(self.spinBox_valueChanged)
        self.clearButton.clicked.connect(self.clearButton_clicked)

    @property
    def value(self) -> int:
        """
        The value entered by the user

        Returns:
             seconds

        """
        return (self.daysSpinBox.value() * 60 * 24 + self.hoursSpinBox.value() * 60 + self.minutesSpinBox.value()) * 60

    @value.setter
    def value(self, new_value: int):
        """
        Sets the value

        Args:
            new_value ():  seconds

        Returns:

        """

        if new_value == 0:
            self.clear_values()
        else:
            # Dont' care about seconds
            new_value //= 60
            days = new_value // (60 * 24)
            remainder_hours = new_value - days * 60 * 24
            hours = remainder_hours // 60
            minutes = remainder_hours - hours * 60

            self.minutesSpinBox.setValue(minutes)
            self.hoursSpinBox.setValue(hours)
            self.daysSpinBox.setValue(days)

    def clear_values(self):
        for spinbox in (self.__spinboxes):
            spinbox.setValue(0)
            spinbox.clear()

    def init_ui(self):
        self.daysSpinBox.setSuffix(f" {get_unit_name('duration-day', 'short', locale=default_locale)}")
        self.hoursSpinBox.setSuffix(f" {get_unit_name('duration-hour', 'short', locale=default_locale)}")
        self.minutesSpinBox.setSuffix(f" {get_unit_name('duration-minute', 'short', locale=default_locale)}")

    def clearButton_clicked(self):
        self.clear_values()

    def spinBox_valueChanged(self, new_value: int):
        self.valueChanged.emit(new_value)
