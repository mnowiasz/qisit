""" Backup defaults if no translations/locales are available """

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

# Name, Factor, Description
DATA_QUANTITY = (
    ("", 1.0, "Piece (base unit)"),
    ("pc", 1.0, "Piece"),
    ("piece", 1.0, "Piece"),
    ("dz", 12.0, "Dozen"),
    ("dozen", 12.0, "Dozen"),
)

# No use in having factors
DATA_UNSPECIFIC = (
    ("some", "Some (unspecific quantity)"),
)
