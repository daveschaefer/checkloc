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

import argparse
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
	parser = argparse.ArgumentParser(description=__doc__)
	verbosity_group = parser.add_mutually_exclusive_group()
	verbosity_group.add_argument('--verbose', '-v', default=False, action='store_true',
			help="Verbose mode. Print more info while testing.")
	verbosity_group.add_argument('--quiet', '-q', default=False, action='store_true',
			help="Quiet mode. Don't print much, not even error info.")

	args = parser.parse_args()

	loglevel = logging.WARNING
	if (args.verbose):
		loglevel = logging.INFO
	elif (args.quiet):
		loglevel = logging.CRITICAL

	logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)
	unittest.main()
