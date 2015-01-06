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
				errors = validate_loc_files(os.path.join(TEST_DATA_DIR, d), parse_manifests=False)
				self.assertFalse(errors)
				i += 1
			elif d.startswith(INVALID_DATA_NAME):
				print "-------\n[{0}.] Checking invalid data in '{1}'; should find an error...".format(i, d)
				errors = validate_loc_files(os.path.join(TEST_DATA_DIR, d), parse_manifests=False)
				self.assertTrue(errors)
				i += 1
			# ignore other directories

	def test_nonexistent_directories_raise_an_error(self):
		non_existent_dir = os.path.join(TEST_DATA_DIR, 'null_empty')
		self.assertFalse(os.path.exists(non_existent_dir), "Test setup: directory {0} should not exist".format(non_existent_dir))
		errors = validate_loc_files(non_existent_dir, parse_manifests=False)
		self.assertTrue(errors)

	def test_passing_non_directory_raises_an_error(self):
		file_name = os.path.join(TEST_DATA_DIR, 'test_file.txt')
		self.assertTrue(os.path.exists(file_name), "Test setup: file {0} exists".format(file_name))
		self.assertFalse(os.path.isdir(file_name), "Test setup: file {0} is not a directory".format(file_name))
		errors = validate_loc_files(file_name, parse_manifests=False)
		self.assertTrue(errors)

	def test_finding_no_language_folders_raises_an_error(self):
		empty_dir = os.path.join(TEST_DATA_DIR, 'other_no_lang_folders')
		self.assertTrue(os.path.exists(empty_dir), "Test setup: directory {0} should exist".format(empty_dir))
		self.assertTrue(os.path.isdir(empty_dir), "Test setup: {0} is a directory".format(empty_dir))
		errors = validate_loc_files(empty_dir, parse_manifests=False)
		self.assertTrue(errors)

	def test_finding_no_baseline_folder_raises_an_error(self):
		base_dir = os.path.join(TEST_DATA_DIR, 'other_no_baseline')
		self.assertTrue(os.path.exists(base_dir), "Test setup: directory {0} should exist".format(base_dir))
		self.assertTrue(os.path.isdir(base_dir), "Test setup: {0} is a directory".format(base_dir))
		errors = validate_loc_files(base_dir, parse_manifests=False)
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
