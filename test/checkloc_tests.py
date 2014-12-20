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

TEST_DATA_DIR = 'test/test_data'
# start a directory with this name
# to signify it contains only valid data and should parse without error
VALID_DATA_NAME = 'valid'
# start a directory with this name
# to signify it contains invalid data that should be caught when parsed
INVALID_DATA_NAME = 'invalid'


class TestChecklocModule(unittest.TestCase):
	"""
	Run test cases against the checkloc module to make sure it is functioning correctly.
	"""

	def test_valid_data_is_parsed_and_invalid_data_is_caught(self):
		dirs = os.listdir(TEST_DATA_DIR)
		i = 1
		for d in dirs:
			if d.startswith(VALID_DATA_NAME):
				print "-------\n[{0}.] Checking data in '{1}'; should be valid...".format(i, d)
				errors = validate_loc_files(os.path.join(TEST_DATA_DIR, d))
				self.assertFalse(errors)
				i += 1
			elif d.startswith(INVALID_DATA_NAME):
				print "-------\n[{0}.] Checking invalid data in '{1}'; should find an error...".format(i, d)
				errors = validate_loc_files(os.path.join(TEST_DATA_DIR, d))
				self.assertTrue(errors)
				i += 1
			# ignore other directories

	def test_nonexistent_directories_raise_an_error(self):
		non_existent_dir = os.path.join(TEST_DATA_DIR, 'null_empty')
		self.assertFalse(os.path.exists(non_existent_dir), "Test setup: directory {0} should not exist".format(non_existent_dir))
		errors = validate_loc_files(non_existent_dir)
		self.assertTrue(errors)


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
