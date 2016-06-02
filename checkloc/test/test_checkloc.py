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

from __future__ import print_function

from abc import ABCMeta
import argparse
import logging
import os
import unittest
import warnings

# allow importing and running both as a package and from the command line
if __package__ is None:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import checkloc
else:
    from .. import checkloc

# relative directory that contains test data
TEST_DATA_SUBDIR = 'test_data'

class IChecklocDataTester(object):
    """
    The interface for testing checkloc behaviour
    using sets of valid and invalid localization test data.
    """
    __metaclass__ = ABCMeta

    LOCALES_ONLY = False

    # start a directory with this name
    # to signify it contains only valid data and should parse without error
    VALID_DATA_NAME = 'valid'

    # start a directory with this name
    # to signify it contains invalid data that should be caught when parsed
    INVALID_DATA_NAME = 'invalid'

    # start a directory with this name
    # to check that warnings are generated
    WARNING_NAME = 'warn'

    def __init__(self, tester):
        self.tester = tester

    def has_test_data_in_dir(self, full_path):
        """
        Return True if the given directory name would contain test data
        for this class, and False otherwise.
        """
        top_dir = os.path.basename(full_path)
        if (top_dir.startswith(self.VALID_DATA_NAME) or
                top_dir.startswith(self.INVALID_DATA_NAME) or
                top_dir.startswith(self.WARNING_NAME)):
            return True

        return False

    def validate(self, full_path, i=0):
        """
        Run validation tests against the data in the given directory.
        """
        top_dir = os.path.basename(full_path)
        if top_dir.startswith(self.VALID_DATA_NAME):
            print("-------\n[{0}.] Checking data in '{1}'; should be valid...".format(i, full_path))
            checker = checkloc.CheckLoc(manifest_dir=full_path, locales_only=self.LOCALES_ONLY)
            errors = checker.validate_loc_files()
            self.tester.assertFalse(errors)
        elif top_dir.startswith(self.INVALID_DATA_NAME):
            print(
                "-------\n[{0}.] Checking invalid data in '{1}'; should find an error..."
                .format(i, full_path))
            checker = checkloc.CheckLoc(manifest_dir=full_path, locales_only=self.LOCALES_ONLY)
            errors = checker.validate_loc_files()
            self.tester.assertTrue(errors)
        elif top_dir.startswith(self.WARNING_NAME):
            print(
                "-------\n[{0}.] Checking warning data in '{1}'; should generate a warning..."
                .format(i, full_path))
            # capture all warnings so we can verify that they happen
            with warnings.catch_warnings(record=True) as warn_list:
                checker = checkloc.CheckLoc(manifest_dir=full_path, locales_only=self.LOCALES_ONLY)
                errors = checker.validate_loc_files()
                self.tester.assertFalse(
                    errors,
                    "Warning test '{0}' should not generate any errors.".format(full_path))
                self.tester.assertTrue(
                    len(warn_list) > 0,
                    "Warning test '{0}' should generate at least one warning.".format(full_path))
                self.tester.assertTrue(
                    issubclass(warn_list[-1].category, Warning),
                    "Warning test '{0}' should generate a warning of type Warning."
                    .format(full_path))
                # with catch_warnings() the behaviour changes so warnings
                # are no longer printed to stdout.
                # print them to stdout so users can still see what is going on.
                for warn in warn_list:
                    logging.warning(warn.message)
        else:
            raise Exception(
                "validate() called with '{0}' - this is not a valid type of data!"
                .format(full_path))

class LocaleDataTester(IChecklocDataTester):
    """
    Test localization data contained only in stand-alone locale folders.
    """
    LOCALES_ONLY = True

class ManifestDataTester(IChecklocDataTester):
    """
    Test localization data that uses a full set of manifest files.
    """
    LOCALES_ONLY = False

    MANIFEST_NAME = 'manifest_'

    VALID_DATA_NAME = MANIFEST_NAME + IChecklocDataTester.VALID_DATA_NAME
    INVALID_DATA_NAME = MANIFEST_NAME + IChecklocDataTester.INVALID_DATA_NAME
    WARNING_NAME = MANIFEST_NAME + IChecklocDataTester.WARNING_NAME

class TestChecklocModule(unittest.TestCase):
    """
    Run test cases against the checkloc module to make sure it is functioning correctly.
    """
    def setUp(self):
        """
        Set up tests to run.
        """
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            TEST_DATA_SUBDIR)

    def test_valid_data_is_parsed_and_invalid_data_is_caught(self):
        dirs = os.listdir(self.test_data_dir)
        locale_tester = LocaleDataTester(self)
        manifest_tester = ManifestDataTester(self)
        i = 1

        for directory in dirs:
            target_dir = os.path.join(self.test_data_dir, directory)
            if locale_tester.has_test_data_in_dir(target_dir):
                i += 1 # only increment if we actually tried to validate
                locale_tester.validate(target_dir, i)
            elif manifest_tester.has_test_data_in_dir(target_dir):
                i += 1
                manifest_tester.validate(target_dir, i)
            # ignore other directories

        self.assertTrue(
            i > 1,
            "No validation tests were run! Is there localization test data in '{0}'?"
            .format(self.test_data_dir))

    def test_nonexistent_directories_raise_an_error(self):
        non_existent_dir = os.path.join(self.test_data_dir, 'null_empty')
        self.assertFalse(
            os.path.exists(non_existent_dir),
            "Test setup: directory {0} should not exist".format(non_existent_dir))
        checker = checkloc.CheckLoc(locales_only=True, manifest_dir=non_existent_dir)
        errors = checker.validate_loc_files()
        self.assertTrue(errors)

    def test_passing_manifest_file_rather_than_manifest_directory_succeeds(self):
        manifest_file = os.path.join(
            self.test_data_dir,
            'manifest_valid_data',
            'chrome.manifest')
        self.assertTrue(
            os.path.exists(manifest_file),
            "Test setup: manifest file '{0}' should exist".format(manifest_file))
        self.assertFalse(
            os.path.isdir(manifest_file),
            "Test setup: file '{0}' is a directory".format(manifest_file))
        checker = checkloc.CheckLoc(manifest_dir=manifest_file)
        errors = checker.validate_loc_files()
        self.assertFalse(errors)

    def test_passing_non_manifest_file_raises_an_error(self):
        file_name = os.path.join(self.test_data_dir, 'test_file.txt')
        self.assertTrue(
            os.path.exists(file_name),
            "Test setup: file {0} should exist".format(file_name))
        self.assertFalse(
            os.path.isdir(file_name),
            "Test setup: file {0} is a directory".format(file_name))
        checker = checkloc.CheckLoc(locales_only=True, manifest_dir=file_name)
        errors = checker.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_language_folders_raises_an_error(self):
        empty_dir = os.path.join(self.test_data_dir, 'other_no_lang_folders')
        self.assertTrue(
            os.path.exists(empty_dir),
            "Test setup: directory {0} should exist".format(empty_dir))
        self.assertTrue(
            os.path.isdir(empty_dir),
            "Test setup: {0} is not a directory".format(empty_dir))
        checker = checkloc.CheckLoc(locales_only=True, manifest_dir=empty_dir)
        errors = checker.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_baseline_folder_raises_an_error(self):
        base_dir = os.path.join(self.test_data_dir, 'other_no_baseline')
        self.assertTrue(
            os.path.exists(base_dir),
            "Test setup: directory {0} should exist".format(base_dir))
        self.assertTrue(
            os.path.isdir(base_dir),
            "Test setup: {0} is not a directory".format(base_dir))
        checker = checkloc.CheckLoc(locales_only=True, manifest_dir=base_dir)
        errors = checker.validate_loc_files()
        self.assertTrue(errors)

    def test_finding_no_loc_data_raises_an_error(self):
        # by this we mean: no Mozilla-style localization data of any kind.
        # the folder could contain anything, but it's not in the format we're expecting.
        # the script should still fail gracefully in this case.
        base_dir = self.test_data_dir
        self.assertTrue(
            os.path.exists(base_dir),
            "Test setup: directory {0} should exist".format(base_dir))
        self.assertTrue(
            os.path.isdir(base_dir),
            "Test setup: {0} is not a directory".format(base_dir))
        checker = checkloc.CheckLoc(manifest_dir=base_dir)
        errors = checker.validate_loc_files()
        self.assertTrue(errors)

def main():
    """
    Parse arguments and run the tests.
    """
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

if __name__ == '__main__':
    main()
