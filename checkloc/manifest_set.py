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
Encapsulate all of the parsing, storage, and logic necessary
to create, hold, and work with one particular set of Mozilla extension
manifest files (chrome.manifest and install.rdf).
"""

import os
import re
import sys

try:
    from lxml import etree
except ImportError:
    print(
        "ERROR: python lxml library not found; localization tests cannot be run. "
        "Please install the python 'lxml' library to run localization tests.")
    sys.exit(1)

import localecodes

class ManifestSet(object):
    """
    Encapsulate all of the parsing, storage, and logic necessary
    to create, hold, and work with one particular set of Mozilla extension
    manifest files (chrome.manifest and install.rdf).
    """

    # start of string used to register locale packages - see
    # https://developer.mozilla.org/en-US/docs/Chrome_Registration#locale
    _MANIFEST_LOCALE_START = 'locale'
    _MANIFEST_LOCALE_LINE = re.compile(r'^\s*locale\s+\S+\s+(\S+)\s+(\S+)')

    def __init__(self, manifest_dir, log_error, log_warning):
        """
        Create a new ManifestSet.
        Argument: path to the directory that contains chrome.manifest
        """
        self.loc_base_dirs = {}
        self.manifest_lines = {}
        self.manifest_paths = {}
        self.manifests_parsed = False
        self.rdf_locs = {}

        self.manifest_dir = manifest_dir
        self._log_error = log_error
        self._log_warning = log_warning

    def validate_manifests(self):
        """
        Validate localization contents of the Mozilla extension information files:
        chrome.manifest and install.rdf.
        """
        self.loc_base_dirs = {}
        self.manifest_paths = {}
        self.manifest_lines = {}
        self.rdf_locs = {}

        if not (os.path.exists(self.manifest_dir) and os.path.isdir(self.manifest_dir)):
            self._log_error(
                "Main plugin directory {0} does not exist; cannot validate chrome.manifest. "
                "If you wish to skip validation of chrome.manifest please specify the "
                "--locales-only switch when running tests."
                .format(self.manifest_dir))
            return

        manifest = os.path.join(self.manifest_dir, 'chrome.manifest')
        if not os.path.exists(manifest):
            self._log_error(
                "File chrome.manifest does not exist in {0} ; cannot validate chrome.manifest. "
                "If you wish to skip validation of chrome.manifest please specify the "
                "--locales-only switch when running tests."
                .format(self.manifest_dir))
            return

        # parse the chrome.manfiest file and save locale data.
        # manifest files use a simple line-based format:
        # https://developer.mozilla.org/en-US/docs/Chrome_Registration#The_Chrome_Registry
        #
        # we're only worried about 'locale' lines. They look like:
        #   locale packagename localename uri/to/files/ [flags]
        # e.g.
        #   locale extension-name pl chrome/locale/pl/
        #
        with open(manifest, 'r') as m:
            lines = m.readlines()
            i = 1 # save the line number to help users troubleshoot any problems
            for line in lines:
                if line.startswith(self._MANIFEST_LOCALE_START):
                    match = self._MANIFEST_LOCALE_LINE.match(line)
                    if match:
                        locale = match.groups(1)[0]
                        locale_subdir = match.group(2)
                        # go one dir up to get the main locale directory
                        base_dir = os.path.abspath(os.path.join(
                            self.manifest_dir, locale_subdir, '..'))
                        locale_absdir = os.path.abspath(os.path.join(
                            self.manifest_dir, locale_subdir))

                        self.loc_base_dirs[base_dir] = True

                        if locale not in self.manifest_paths:
                            self.manifest_paths[locale] = locale_absdir
                        if locale not in self.manifest_lines:
                            self.manifest_lines[locale] = i
                        else:
                            self._log_error(
                                "Locale '{0}' is defined more than once inside chrome.manifest. "
                                "Each locale should only be defined once."
                                .format(locale))
                    else:
                        self._log_error(
                            "Invalid locale line found in chrome.manifest on line {0}:\n  {1}"
                            .format(i, line))
                i += 1


        # also parse install.rdf
        install_rdf = os.path.abspath(os.path.join(self.manifest_dir, 'install.rdf'))
        if not os.path.exists(install_rdf):
            self._log_error(
                "File install.rdf does not exist in {0} ; cannot validate. "
                "If you wish to skip validation please specify the "
                "--locales-only switch when running tests."
                .format(self.manifest_dir))
            return

        try:
            xml = etree.parse(install_rdf)
            root = xml.getroot()
            # lxml 3.5.0 raises a ValueError if the namespace map
            # contains a 'None' entry, even if it also contains
            # other valid mappings.
            # Therefore explicitly add only the namespaces we need
            namespace = {'em': 'http://www.mozilla.org/2004/em-rdf#'}
            for locale in root.findall('.//em:locale', namespace):
                loc = locale.text
                if loc not in self.rdf_locs:
                    self.rdf_locs[loc] = True
                else:
                    self._log_error(
                        "Locale '{0}' is defined more than once inside install.rdf. "
                        "Each locale should only be defined once."
                        .format(loc))
        except etree.XMLSyntaxError as ex:
            self._log_error("Could not parse {0}: {1}".format(install_rdf, ex))


        # check every chrome.manifest entry to make sure a locale folder exists
        for locale in self.manifest_paths:
            locale_path = self.manifest_paths[locale]
            if not os.path.exists(locale_path):
                self._log_error(
                    "Locale folder '{0}' is specified in chrome.manifest "
                    "line {1}, but {2} does not exist!"
                    .format(locale, self.manifest_lines[locale], locale_path), locale)
            elif not os.path.isdir(locale_path):
                self._log_error(
                    "Locale folder '{0}' is specified in chrome.manifest "
                    "line {1}, but {2} is not a folder!"
                    .format(locale, self.manifest_lines[locale], locale_path), locale)

            # if an entry exists in chrome.manifest then it must exist on disk
            # or we will raise an error.
            # if it exists on disk but isn't inside install.rdf we'll catch that below
            # when we compare existing folders to the contents of manifest files.
            # thus we do *not* need to check here whether locales in chrome.manifest
            # also exist inside install.rdf.

            if locale not in localecodes.MOZILLA_LOCALE_CODES:
                self._log_warning(
                    "chrome.manifest locale '{0}' does not exist "
                    "in the list of Mozilla locale codes."
                    .format(locale), locale)

        # check every install.rdf entry to make sure a locale folder exists
        for locale in self.rdf_locs:
            if locale not in self.manifest_paths:
                self._log_warning(
                    "Locale '{0}' is specified in install.rdf "
                    "but is not specified in chrome.manifest."
                    .format(locale), locale)
            else:
                locale_path = self.manifest_paths[locale]
                if not os.path.exists(locale_path):
                    self._log_warning(
                        "Locale folder '{0}' is specified in install.rdf "
                        "line {1}, but {2} does not exist!"
                        .format(locale, self.manifest_lines[locale], locale_path), locale)
                elif not os.path.isdir(locale_path):
                    self._log_warning(
                        "Locale folder '{0}' is specified in install.rdf "
                        "line {1}, but {2} is not a folder!"
                        .format(locale, self.manifest_lines[locale], locale_path), locale)

            if locale not in localecodes.MOZILLA_LOCALE_CODES:
                self._log_warning(
                    "install.rdf locale '{0}' does not exist in the list of Mozilla locale codes."
                    .format(locale), locale)


        # now calculate the locale subdirectories
        langs = {}
        for ld in self.loc_base_dirs:
            for (_, dirs, _) in os.walk(ld):
                for d in dirs:
                    langs[d] = os.path.join(ld, d)

        # check every locale folder to ensure both
        # a manifest entry and an install.rdf entry exist.
        for lang in langs:
            # give a more accurate sub-folder location, if we are able
            dir_path = self.manifest_dir
            if lang in self.manifest_paths:
                dir_path = os.path.abspath(os.path.join(self.manifest_paths[lang], '..'))

            if lang not in self.manifest_paths:
                self._log_error(
                    "Locale folder '{0}' exists in {1}, but no corresponding entry "
                    "exists in the chrome.manifest."
                    .format(lang, dir_path), lang)
            if lang not in self.rdf_locs:
                self._log_warning(
                    "Locale folder '{0}' exists in {1}, but no corresponding entry "
                    "exists in install.rdf."
                    .format(lang, dir_path), lang)

        self.manifests_parsed = True

    def get_loc_base_dirs(self):
        """
        Return a list of localization base directories
        found in the manifest files.
        """
        if not self.manifests_parsed:
            self.validate_manifests()

        return self.loc_base_dirs.keys()

if __name__ == '__main__':
    pass
