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
to create, hold, and work with one particular localization language.
"""

import codecs
import linecache
import logging
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

class LocalizationLanguage(object):
    """
    Encapsulate all of the parsing, storage, and logic necessary
    to create, hold, and work with one particular localization language.
    """
    # When storing localization strings,
    # use 'filename/keyname' as the hash key, as that's the value
    # we want to ensure is unique for each localization.
    # We want to make sure there are no instances of the separator character inside the filename,
    # so we don't have trouble parsing or splitting the hash key later, if necessary
    # (e.g. for printing error info)
    # Thus, use a separator character that is *not*
    # a legal filename character on most systems (including windows, linux, and osx).
    # This makes it easier to ensure we won't encounter it in file names
    # or have difficulty printing error info.
    _LSEP = '/'

    # .properties files look like:
    #   # comments are ignored
    #   ! this is also a comment
    #   name=string
    #   name:string
    # Assumptions: both comments and entries exist only on a single line.
    _PROP_COMMENT = re.compile(r'^\s*[#!]+[^\n\r\f]*[\n\r\f]+', re.MULTILINE)
    _PROP_SEP = re.compile(r'[\n\r\f]')
    # almost any character is a valid .properties key
    # except : and = , which note the transition to a value,
    # and spaces.
    # Because we parse and remove PROP_COMMENTs first, that regex will catch any
    # '#' or '!' characters that are found as the first non-whitespace part of a line.
    # This means we can allow # and ! inside this regex and it's not as complex.
    _PROP_LINE = re.compile(r'^\s*([A-Za-z0-9_.\-+\\{}\[\]!@#$%^&*()/<>,?;\'"`~|]+)\s*[=:]\s*([^\n\r\f]*)')

    _DTD_PARSE_ERROR = re.compile(r'([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):(.*)', re.DOTALL)

    # Firefox does not allow more than ten string substitution parameters, for performance reasons.
    # For details see nsStringBundle.cpp
    # https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp
    # The error actually happens if you pass more than 10 parameters inside javascript code;
    # specifying more than 10 substitutions in a .properties file
    # will simply cause the browser to use '(null)' or random/garbage data
    # for unprovided substitutions greater than ten.
    # However, we should still flag this as an error,
    # as it probably won't do what the author intended.
    _MOZILLA_MAX_PROPERTIES_STRING_SUBS = 10

    def __init__(self, localization_base_dir, language, log_warning, log_error):
        """
        Create a new LocalizationLanguage.
        """
        # all localization keys, in the form filename/keyname
        self.keys = {}
        # all string substitutions found in .properties files
        self.subs = {}

        self.loc_dir = localization_base_dir
        self.name = language
        self._log_warning = log_warning
        self._parent_log_error = log_error

        self.parsing_errors = False

    def _log_error(self, msg):
        """
        Log an error.
        """
        # this function wraps setting the parsing error flag
        # to keep all error code in one place
        self.parsing_errors = True
        self._parent_log_error(msg, self.name)


    def _extract_first_dtd_parse_error_info(self, err):
        """
        Extract the line and column numbers from a DTDParseError,
        so the user knows where to look for the problem
        without having to understand the built-in error format.
        If there is more than one error only the first is used.
        Return a list of extracted data.
        """
        # error_log lines are formatted like:
        # <string>:10:17:FATAL:PARSER:ERR_VALUE_REQUIRED: Entity value required
        line = str(err.error_log[0]).strip()
        match = re.match(self._DTD_PARSE_ERROR, line)
        if match:
            (string, line, column, errlevel, place, errname, message) = match.groups()
            return [string, line, column, errlevel, place, errname, message.strip()]

    def get_loc_keys(self):
        """
        Read the localization string keys and values from all files in
        this localization's directory.

        This function only reads data from Mozilla-style localization files:
        XML DTD and .properties files.

        Returns True if there were any parsing errors,
        and False otherwise.
        """
        loc_files = []

        # we assume that loc directries do not have sub-directories
        for (_, _, files) in os.walk(self.loc_dir):
            loc_files.extend(files)

        logging.info("Checking files in %s", self.loc_dir)
        for file_name in loc_files:
            file_path = os.path.normpath(os.path.join(self.loc_dir, file_name))
            file_name = file_name.replace(self._LSEP, '')

            # check each file for the Byte Order Marker;
            # according to the MDN spec, localization files should *not* contain BOM
            # https://developer.mozilla.org/en/XUL_Tutorial/Localization
            bytes_to_read = min(32, os.path.getsize(file_path))
            with open(file_path, 'rb') as rawfile:
                if rawfile.read(bytes_to_read).startswith(codecs.BOM_UTF8):
                    self._log_error(
                        "File '{0}' contains Byte Order Marker; "
                        "localization files should not contain BOM."
                        .format(file_path))

            if file_path.endswith('.dtd'):
                with open(file_path, 'r') as openfile:
                    try:
                        dtd = etree.DTD(openfile)
                        for entity in dtd.entities():
                            # note: lxml actually removes duplicate entities when parsing;
                            # it always takes the first entry.
                            key = file_name + self._LSEP + entity.name
                            if key in self.keys:
                                self._log_error(
                                    "Duplicate dtd key '{0}' found in {1}"
                                    .format(key, file_path))
                            # check for invalid content
                            # lxml will already check for '%' in values when it parses the file
                            elif '<' in entity.content:
                                self._log_error(
                                    "The value for '{0}' in {1} contains the invalid character "
                                    "'<'. This is not allowed; please remove this character."
                                    .format(key, file_path))
                            else:
                                if len(entity.content) < 1:
                                    self._log_warning(
                                        "Key '{0}' in {1} has a blank value. "
                                        "Is this desired?"
                                        .format(key, file_path), self.name)
                                self.keys[key] = entity.content

                    except (etree.DTDParseError) as ex:
                        (_, line, column, _, _, _, message) =\
                            self._extract_first_dtd_parse_error_info(ex)

                        # get the error line so we can show the user where the problem may be
                        error_line = linecache.getline(file_path, int(line)).strip()
                        linecache.clearcache()
                        highlight_string = (" " * (int(column) - 1)) + "^"

                        error_message = "DTD syntax error starting at "\
                            "Line {0}, Col {1}: {2}\n{3}\n{4}\n{5}\n{6}\n{7}".format(
                                line,
                                column,
                                message,
                                "Error line shown below, problem marked with ^:",
                                error_line,
                                highlight_string,
                                "Full error details:",
                                ex.error_log)
                        self._log_error(
                            "Could not parse {0}: {1}"
                            .format(file_path, error_message))

            elif file_path.endswith('.properties'):
                self._parse_properties_file(file_path)
            else:
                # not neccesarily a failure - there may just be extra files lying around.
                self._log_warning(
                    "File {0} is not a .dtd or .properties file. Ignoring."
                    .format(file_path), self.name)

        return self.parsing_errors

    def _parse_properties_file(self, file_path):
        """
        Extract localization string keys and values from a mozilla-style ".properties" file
        and add the results to the 'keys' and 'subs' dictionaries.

        https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files
        """
        file_name = os.path.basename(file_path).replace(self._LSEP, '')
        lang = os.path.basename(os.path.dirname(file_path))

        with open(file_path, 'r') as openfile:
            data = openfile.read()

            if len(data) < 1:
                self._log_warning("{0} does not contain any lines".format(file_path), self.name)
                return

            data = re.sub(self._PROP_COMMENT, '', data)
            data = re.split(self._PROP_SEP, data)
            for line in data:
                if not line.strip():
                    continue # skip blank lines
                logging.info(".prop line: '%s'", line)
                numeric_subs_list = [] # list of numbered string substitutions, like %1$S.
                regular_subs = 0
                match = self._PROP_LINE.match(line)
                if match:
                    key = file_name + self._LSEP + match.group(1)
                    value = match.group(2)
                    if key in self.keys:
                        self._log_error(
                            "Duplicate property key '{0}' found in {1}"
                            .format(key, file_path))
                    elif len(value) < 1:
                        self._log_error(
                            "Key '{0}' in {1} has a blank value"
                            .format(key, file_path))
                    # the only special character for .properties files is %
                    # used to substitute values when calling strbundle.getFormattedString().
                    # https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files#Text_Formatting
                    # there are three valid options:
                    # 1. no % on a line
                    # 2. %% to escape and print a regular %
                    # 3. %S or %n$S , where n is a number
                    elif '%' in value:
                        valid = True
                        pos = value.find('%')
                        while pos < len(value) and pos != -1:
                            # we don't save the (n$) group for anything;
                            # we simply specify a group so we can make the entire group optional
                            # with a trailing ?
                            pmatch = re.match(r'%([0-9]+\$)?S', value[pos:])

                            if (pos + 1 < len(value)) and value[pos + 1] == '%':
                                pos += 1 # double %% for escape sequence; print actual %
                            elif pmatch:
                                # advance 1 char for the trailing S
                                # plus however many chars make up the numerical reference (if any)
                                pos += 1
                                if pmatch.group(1):
                                    numeric_subs_list.append(int(pmatch.group(1).replace('$', '')))
                                    logging.info(
                                        "String substitution found. %s", numeric_subs_list)
                                    pos += len(pmatch.group(1))
                                else:
                                    regular_subs += 1
                            else:
                                self._log_error(
                                    "key '{0}' contains improper use of % in {1}. "
                                    "Position marked by ^ below:\n{2}\n{3}"
                                    .format(key, file_path, value, "{0}^".format(" " * pos)))
                                valid = False
                                break

                            pos = value.find('%', pos + 1)

                        if valid:
                            self.keys[key] = value
                            # different languages can use substitutions in different orders
                            # sort to ensure the count and type are the same
                            numeric_subs_list.sort()
                            if (numeric_subs_list and numeric_subs_list[-1] > self._MOZILLA_MAX_PROPERTIES_STRING_SUBS) or \
                                regular_subs > self._MOZILLA_MAX_PROPERTIES_STRING_SUBS or \
                                (numeric_subs_list and \
                                    ((numeric_subs_list[-1] + regular_subs) > self._MOZILLA_MAX_PROPERTIES_STRING_SUBS)):
                                self._log_error(
                                    "More than {0} string substitutions found for key '{1}' in '{2}'. "
                                    "Mozilla does not allow this for performance reasons. "
                                    "See https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp "
                                    "".format(self._MOZILLA_MAX_PROPERTIES_STRING_SUBS, key, lang))

                            self.subs[key] = ''.join(str(numeric_subs_list))

                    else:
                        self.keys[key] = value
                elif len(line) > 0: # not an empty string
                    self._log_error(
                        "line '{0}' does not match any .properties file patterns for {1}"
                        .format(line, file_path))

        return

if __name__ == '__main__':
    pass
