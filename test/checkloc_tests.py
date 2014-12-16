#
#   Copyright (C) 2014 Dave Schaefer
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, version 3 of the License.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Run unit tests for the checkloc module.
"""

import logging
import os
import sys
import unittest

# prepend parent directory so we can import the checkloc module
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from checkloc import validate_loc_files


class TestChecklocModule(unittest.TestCase):
	"""
	Run test cases against the checkloc module to make sure it is functioning correctly.
	"""

	def test_valid_data_is_parsed(self):
		errors = validate_loc_files('test/test_data/valid_characters')
		self.assertFalse(errors)



if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)
	unittest.main()
