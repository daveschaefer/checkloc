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
import warnings

from .. import checkloc

# relative directory that contains test data
TEST_DATA_SUBDIR = 'test_data'

# start a directory with this name
# to signify it contains only valid data and should parse without error
VALID_DATA_NAME = 'valid'

# start a directory with this name
# to signify it contains invalid data that should be caught when parsed
INVALID_DATA_NAME = 'invalid'

# check that warnings are generated
WARNING_NAME = 'warn'

# to run tests that include parsing the manifest files
# chrome.manifest and install.rdf
# start the folder with these prefixes
MANIFEST_NAME = 'manifest_'
MANIFEST_INVALID_NAME = MANIFEST_NAME + INVALID_DATA_NAME
MANIFEST_VALID_NAME = MANIFEST_NAME + VALID_DATA_NAME
MANIFEST_WARNING_NAME = MANIFEST_NAME + WARNING_NAME


class TestChecklocModule(unittest.TestCase):
    """
    Run test cases against the checkloc module to make sure it is functioning correctly.
    """

    def setUp(self):
        """
        Set up tests to run.
        """
        self.test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            TEST_DATA_SUBDIR)

    def test_valid_data_is_parsed_and_invalid_data_is_caught(self):
        dirs = os.listdir(self.test_data_dir)
        i = 1
        for d in dirs:
            target_dir = os.path.join(self.test_data_dir, d)

            if d.startswith(VALID_DATA_NAME):
                print "-------\n[{0}.] Checking data in '{1}'; should be valid...".format(i, d)
                ch = checkloc.CheckLoc(locales_only=True, manifest_dir=target_dir)
                errors = ch.validate_loc_files()
                self.assertFalse(errors)
                i += 1
            elif d.startswith(INVALID_DATA_NAME):
                print "-------\n[{0}.] Checking invalid data in '{1}'; should find an error...".format(i, d)
                ch = checkloc.CheckLoc(locales_only=True, manifest_dir=target_dir)
                errors = ch.validate_loc_files()
                self.assertTrue(errors)
                i += 1
            elif d.startswith(WARNING_NAME):
                print "-------\n[{0}.] Checking warning data in '{1}'; should generate a warning...".format(i, d)
                # capture all warnings so we can verify that they happen
                with warnings.catch_warnings(record=True) as w:
                    ch = checkloc.CheckLoc(locales_only=True, manifest_dir=target_dir)
                    errors = ch.validate_loc_files()
                    self.assertFalse(
                        errors,
                        "Warning test '{0}' should not generate any errors.".format(d))
                    self.assertTrue(
                        len(w) > 0,
                        "Warning test '{0}' should generate at least one warning.".format(d))
                    self.assertTrue(
                        issubclass(w[-1].category, Warning),
                        "Warning test '{0}' should generate a warning of type Warning.".format(d))
                    # with catch_warnings() the behaviour changes so warnings
                    # are no longer printed to stdout.
                    # print them to stdout so users can still see what is going on.
                    for warning in w:
                        logging.warning(warning.message)
                i += 1
            elif d.startswith(MANIFEST_VALID_NAME):
                print "-------\n[{0}.] Checking manifest data in '{1}'; should be valid...".format(i, d)
                ch = checkloc.CheckLoc(manifest_dir=target_dir)
                errors = ch.validate_loc_files()
                self.assertFalse(
                    errors,
                    "Valid manifest test '{0}' should not generate any errors.".format(d))
                i += 1
            elif d.startswith(MANIFEST_INVALID_NAME):
                print "-------\n[{0}.] Checking invalid manifest data in '{1}'; should find an error...".format(i, d)
                ch = checkloc.CheckLoc(manifest_dir=target_dir)
                errors = ch.validate_loc_files()
                self.assertTrue(
                    errors,
                    "Invalid manifest test '{0}' should generate at least one error.".format(d))
                i += 1
            elif d.startswith(MANIFEST_WARNING_NAME):
                print "-------\n[{0}.] Checking manifest data in '{1}'; should generate a warning...".format(i, d)
                # capture all warnings so we can verify that they happen
                with warnings.catch_warnings(record=True) as w:
                    ch = checkloc.CheckLoc(manifest_dir=target_dir)
                    errors = ch.validate_loc_files()
                    self.assertFalse(
                        errors,
                        "Warning test '{0}' should not generate any errors.".format(d))
                    self.assertTrue(
                        len(w) > 0,
                        "Warning test '{0}' should generate at least one warning.".format(d))
                    self.assertTrue(
                        issubclass(w[-1].category, Warning),
                        "Warning test '{0}' should generate a warning of type Warning.".format(d))
                    # with catch_warnings() the behaviour changes so warnings
                    # are no longer printed to stdout.
                    # print them to stdout so users can still see what is going on.
                    for warning in w:
                        logging.warning(warning.message)
                i += 1
            # ignore other directories

    def test_nonexistent_directories_raise_an_error(self):
        non_existent_dir = os.path.join(self.test_data_dir, 'null_empty')
        self.assertFalse(os.path.exists(non_existent_dir), "Test setup: directory {0} should not exist".format(non_existent_dir))
        ch = checkloc.CheckLoc(locales_only=True, manifest_dir=non_existent_dir)
        errors = ch.validate_loc_files()
        self.assertTrue(errors)

    def test_passing_non_directory_raises_an_error(self):
        file_name = os.path.join(self.test_data_dir, 'test_file.txt')
        self.assertTrue(os.path.exists(file_name), "Test setup: file {0} exists".format(file_name))
        self.assertFalse(os.path.isdir(file_name), "Test setup: file {0} is not a directory".format(file_name))
        ch = checkloc.CheckLoc(locales_only=True, manifest_dir=file_name)
        errors = ch.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_language_folders_raises_an_error(self):
        empty_dir = os.path.join(self.test_data_dir, 'other_no_lang_folders')
        self.assertTrue(os.path.exists(empty_dir), "Test setup: directory {0} should exist".format(empty_dir))
        self.assertTrue(os.path.isdir(empty_dir), "Test setup: {0} is a directory".format(empty_dir))
        ch = checkloc.CheckLoc(locales_only=True, manifest_dir=empty_dir)
        errors = ch.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_baseline_folder_raises_an_error(self):
        base_dir = os.path.join(self.test_data_dir, 'other_no_baseline')
        self.assertTrue(os.path.exists(base_dir), "Test setup: directory {0} should exist".format(base_dir))
        self.assertTrue(os.path.isdir(base_dir), "Test setup: {0} is a directory".format(base_dir))
        ch = checkloc.CheckLoc(locales_only=True, manifest_dir=base_dir)
        errors = ch.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_loc_data_raises_an_error(self):
        # by this we mean: no Mozilla-style localization data of any kind.
        # the folder could contain anything, but it's not in the format we're expecting.
        # the script should still fail gracefully in this case.
        base_dir = self.test_data_dir
        self.assertTrue(os.path.exists(base_dir), "Test setup: directory {0} should exist".format(base_dir))
        self.assertTrue(os.path.isdir(base_dir), "Test setup: {0} is a directory".format(base_dir))
        ch = checkloc.CheckLoc(manifest_dir=base_dir)
        errors = ch.validate_loc_files()
        self.assertTrue(errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--verbose', '-v',
        default=False,
        action='store_true',
        help="Verbose mode. Print more info while testing.")
    verbosity_group.add_argument(
        '--quiet', '-q',
        default=False,
        action='store_true',
        help="Quiet mode. Don't print much, not even error info.")

    args = parser.parse_args()

    loglevel = logging.WARNING
    if args.verbose:
        loglevel = logging.INFO
    elif args.quiet:
        loglevel = logging.CRITICAL

    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)
    # make sure all warnings are always raised; never suppress any.
    # this ensures we can always detect correct warning behaviour.
    warnings.simplefilter('always', UserWarning)
    unittest.main()
