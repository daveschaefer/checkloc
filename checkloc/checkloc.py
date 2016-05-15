#!/usr/bin/env python
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
Validate Mozilla-style localization files (XUL and string bundle)
to make sure all localizations have the same strings in the same places.
"""

from __future__ import print_function

import argparse
import json
import logging
import os
import sys
import warnings

import loc_language
import localecodes
import manifest_set

# Attempt to version meaningfully, following semver.org:
# Given a version number MAJOR.MINOR.PATCH, increment the:
# MAJOR version when you make backwards-incompatible changes,
# MINOR version when you add functionality in a backwards-compatible manner
# PATCH version when you make backwards-compatible bug fixes.
VERSION = "2.1.3"

class CheckLoc(object):
    """
    Validate Mozilla-style localization files (XUL and string bundle)
    to make sure all localizations have the same strings in the same places.
    """

    # the en-US translation will have all files and strings created. Use it as the base.
    BASE_LOC = 'en-US'

    def __init__(self, group_by_language=False, output_json=False, locales_only=False,
                 manifest_dir=None):
        self.any_errors = False
        self.messages_by_language = {}

        self.group_by_language = group_by_language
        self.locales_only = locales_only
        self.manifest_dir = manifest_dir
        self.output_json = output_json

        if output_json:
            self.group_by_language = True

    def _log_error(self, msg, lang=None):
        """
        Log an error message.
        If 'lang' is specified, the error was found inside the data for that language.
        """
        self._log_message(msg, lang, logging.error)

    def _log_warning(self, msg, lang=None):
        """
        Log a warning message.
        If 'lang' is specified, the warning was found inside the data for that language.
        """
        self._log_message(msg, lang, warnings.warn)

    def _log_normal(self, msg, lang=None):
        """
        Log a normal print message.
        If 'lang' is specified, the message was generated inside the data for that language.
        """
        if not self.output_json:
            log_func = lambda m: print(m)
            self._log_message(msg, lang, log_func)

    def _log_message(self, msg, lang, log_func):
        """
        Log a message to the appropriate place via log_func().
        """
        # this function wraps setting the error flag
        # to keep all error code in one place

        if log_func == logging.error:
            self.any_errors = True

        if not lang:
            lang = "Main"

        msg_out = "({0}) {1}".format(lang, msg)

        if self.group_by_language:
            if lang not in self.messages_by_language:
                self.messages_by_language[lang] = []

            if self.output_json:
                if log_func == logging.error:
                    msg_out = "ERROR: " + msg_out
                elif log_func == warnings.warn:
                    msg_out = "WARNING: " + msg_out
                self.messages_by_language[lang].append(msg_out)
            else:
                # appending as lambda functionss allows us to combine error and warning messages
                # and not have to re-calculate what to do with them
                # or where they should be sent.
                self.messages_by_language[lang].append(
                    lambda: log_func(msg_out))
        else:
            log_func(msg_out)

    def validate_loc_files(self):
        """
        Validate localization contents inside the given base directory.
        Return True if there were any errors and False otherwise.
        """
        self.any_errors = False

        langs = {}

        self._log_normal("Starting Localization tests...")

        manifest_dir = os.path.abspath(self.manifest_dir)
        if not os.path.exists(manifest_dir):
            self._log_error("The localization directory {0} does not exist!".format(manifest_dir))
            return True
        logging.info("Loc directory %s exists.", manifest_dir)

        if not os.path.isdir(manifest_dir):
            # if the user invokes with the exact path to the chrome.manifest file
            # still attempt to run using the given directory
            manifest_dir = os.path.dirname(manifest_dir)

        ms = manifest_set.ManifestSet(manifest_dir, self._log_error, self._log_warning)

        loc_dirs = []
        if self.locales_only:
            loc_dirs.append(manifest_dir) # script should be pointed to main locale folder instead
        else:
            ms.validate_manifests()
            loc_dirs.extend(ms.get_loc_base_dirs())

        if not loc_dirs:
            self._log_error("No localization directories found in {0}".format(manifest_dir))
            return True

        for ld in loc_dirs:
            for (_, dirs, _) in os.walk(ld):
                for d in dirs:
                    langs[d] = os.path.join(ld, d)

        if len(langs) < 1:
            self._log_error("Did not find any language folders inside {0}!".format(loc_dirs))
            return True
        self._log_normal("Found {0} languages: {1}.".format(len(langs), langs.keys()))

        if self.BASE_LOC not in langs:
            self._log_error("Base language folder '{0}' was not found in {1}".format(\
                self.BASE_LOC, loc_dirs))
            return True


        baseline = loc_language.LocalizationLanguage(
            langs[self.BASE_LOC], self.BASE_LOC, self._log_warning, self._log_error)
        parse_errors = baseline.get_loc_keys()
        self.any_errors = self.any_errors or parse_errors

        if len(baseline.keys) < 1:
            self._log_error("Did not find any keys in '{0}'!".format(baseline.name))
            return True

        if self.any_errors:
            return True # error message has already been printed above

        self._log_normal(
            "{0} keys found in baseline '{1}'."
            .format(len(baseline.keys), baseline.name))

        del langs[self.BASE_LOC] # don't test the baseline localization against itself

        for lang in langs:
            loc = loc_language.LocalizationLanguage(
                langs[lang], lang, self._log_warning, self._log_error)
            parse_errors = loc.get_loc_keys()
            self.any_errors = self.any_errors or parse_errors

            for key in loc.keys:
                if key not in baseline.keys:
                    self._log_error(
                        "Key '{0}' in '{1}' but not in '{2}'"
                        .format(key, loc.name, baseline.name), lang)

            for key in baseline.keys:
                if key not in loc.keys:
                    self._log_error(
                        "Key '{0}' in '{1}' but not in '{2}'"
                        .format(key, baseline.name, loc.name), lang)

            # make sure .properties string substitutions match
            # keys that don't exist in one loc will already have been caught above
            for key in loc.subs:
                if key not in baseline.subs:
                    self._log_error(
                        "String substitution for key '{0}' found in '{1}' but not in baseline {2}!"
                        .format(key, loc.name, baseline.name), lang)
                elif loc.subs[key] != baseline.subs[key]:
                    self._log_error(
                        "String substitution for key '{0}' in '{1}' "
                        "is not the same as baseline '{2}'. "
                        "Substitution count and type must match.\n{1}:{3}\n{2}:{4}"
                        .format(key, loc.name, baseline.name, loc.subs[key], baseline.subs[key]),
                        lang)

            for key in baseline.subs:
                if key not in loc.subs:
                    self._log_error(
                        "String substitution for key '{0}' found in baseline {1} but not in '{2}'!"
                        .format(key, baseline.name, loc.name), lang)
                elif loc.subs[key] != baseline.subs[key]:
                    self._log_error(
                        "String substitution for key '{0}' in baseline '{1}' "
                        "is not the same as '{2}'. "
                        "Substitution count and type must match.\n{1}:{4}\n{2}:{3}"
                        .format(key, baseline.name, loc.name, loc.subs[key], baseline.subs[key]),
                        lang)

        self._log_normal("Done!")
        return self.any_errors

def cb_format_warning(message, category, filename, lineno, line=None):
    """
    Format a warning message and return it as a string.

    Overrides the warnings module's built-in formatwarning() function
    so we can format warnings using this module's log formatting.
    """
    return message

def _get_parser():
    """
    Return a CheckLoc argument parser
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'manifest_dir',
        help="Directory where chrome.manifest file is located.")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--verbose', '-v',
        default=False,
        action='store_true',
        help="Verbose mode. Print more info about files and tests.")
    verbosity_group.add_argument(
        '--quiet', '-q',
        default=False,
        action='store_true',
        help="Quiet mode. Don't print much, not even error info.")

    parser.add_argument(
        '--locales-only', '-l',
        default=False,
        action='store_true',
        help="Do not attempt to parse or validate chrome.manifest or install.rdf. "
        "Instead, point the script directly to your locale folder: "
        "it will treat all subfolders as locales and parse them individually. "
        "Mainly intended to allow easier unit-testing of checkloc itself; "
        "you should usually *NOT* use this flag.")

    parser.add_argument(
        '--group-by-language',
        default=False,
        action='store_true',
        help="Save output until the end and group messages by language, "
        "rather than as they are encountered.")

    parser.add_argument(
        '--json',
        default=False,
        action='store_true',
        help="Output messages as JSON rather than standard messages. "
        "Enabling this implies also enabling --group-by-language.")

    return parser

def _parse_args():
    """
    Parse the args and set everything up.
    """
    args = _get_parser().parse_args()

    loglevel = logging.WARNING
    if args.verbose:
        loglevel = logging.INFO
    elif args.quiet:
        loglevel = logging.CRITICAL

    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)
    # send warning messages through our logging system
    # with the desired formatting
    logging.captureWarnings(True)
    warnings.formatwarning = cb_format_warning

    return args

def main():
    """
    Parse args and run the program.
    """
    args = _parse_args()
    checkloc = CheckLoc(args.group_by_language, args.json, args.locales_only, args.manifest_dir)
    errors = checkloc.validate_loc_files()

    if args.group_by_language:
        if args.json:
            print(json.dumps(checkloc.messages_by_language, sort_keys=True, indent=4))
        else:
            for lang in sorted(checkloc.messages_by_language):
                for log_call in checkloc.messages_by_language[lang]:
                    log_call()

    if errors:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
