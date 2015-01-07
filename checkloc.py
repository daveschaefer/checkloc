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

import argparse
import codecs
import linecache
import logging
import os
import re
import sys
import warnings

try:
	from lxml import etree
except ImportError:
	warnings.warn("python lxml library not found; localization tests cannot be run. Please install the python 'lxml' library to run localization tests.")
	sys.exit(0)

import localecodes


# Attempt to version meaningfully, following semver.org:
# Given a version number MAJOR.MINOR.PATCH, increment the:
# MAJOR version when you make backwards-incompatible changes,
# MINOR version when you add functionality in a backwards-compatible manner
# PATCH version when you make backwards-compatible bug fixes.
VERSION = "1.2"

# the en-US translation will have all files and strings created. Use it as the base.
BASE_LOC = 'en-US'

MANIFEST_LOCALE_LINE = re.compile('^\s*locale\s+\S+\s+(\S+)')

any_errors = False

def _log_error(msg):
	"""Log an error message."""
	# this function wraps setting the global error flag
	# to keep all error code in one place
	global any_errors

	any_errors = True
	logging.error(msg)

def _format_warning(message, category, filename, lineno, line=None):
	"""
	Format a warning message and return it as a string.

	Overrides the warnings module's built-in formatwarning() function
	so we can format warnings using this module's log formatting.
	"""
	return message


class LocalizationLanguage:
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
	LSEP = '/'

	# .properties files look like:
	#   # comments are ignored
	#   ! this is also a comment
	#   name=string
	#   name:string
	# Assumptions: both comments and entries exist only on a single line.
	PROP_COMMENT = re.compile('^\s*[#!]+[^\n\r\f]*[\n\r\f]+', re.MULTILINE)
	PROP_SEP = re.compile('[\n\r\f]')
	# almost any character is a valid .properties key
	# except : and = , which note the transition to a value,
	# and spaces.
	# note that \\\\ is used in the regex to specify a single \ .
	# Because we parse and remove PROP_COMMENTs first, that regex will catch any
	# '#' or '!' characters that are found as the first non-whitespace part of a line.
	# This means we can allow # and ! inside this regex and it's not as complex.
	PROP_LINE = re.compile('^\s*([A-Za-z0-9_.\-+\\\\{}\[\]!@#$%^&*()/<>,?;\'"`~|]+)\s*[=:]\s*([^\n\r\f]*)')

	DTD_PARSE_ERROR = re.compile('([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):(.*)', re.DOTALL)

	# Firefox does not allow more than ten string substitution parameters, for performance reasons.
	# For details see nsStringBundle.cpp
	# https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp
	# The error actually happens if you pass more than 10 parameters inside javascript code;
	# specifying more than 10 substitutions in a .properties file
	# will simply cause the browser to use '(null)' or random/garbage data
	# for unprovided substitutions greater than ten.
	# However, we should still flag this as an error,
	# as it probably won't do what the author intended.
	MOZILLA_MAX_PROPERTIES_STRING_SUBS = 10

	def __init__(self, localization_base_dir, language):
		"""
		Create a new LocalizationLanguage.
		"""
		# all localization keys, in the form filename/keyname
		self.keys = {}
		# all string substitutions found in .properties files
		self.subs = {}

		self.loc_dir = os.path.join(localization_base_dir, language)
		self.name = language

		self.parsing_errors = False

	def _log_error(self, msg):
		"""
		Log an error.
		"""
		# this function wraps setting the parsing error flag
		# to keep all error code in one place
		self.parsing_errors = True
		logging.error(msg)


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
		match = re.match(self.DTD_PARSE_ERROR, line)
		if (match):
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
		for (root, dirs, files) in os.walk(self.loc_dir):
			loc_files.extend(files)

		logging.info("Checking files in {0}".format(self.loc_dir))
		for file_name in loc_files:
			file_path = os.path.normpath(os.path.join(self.loc_dir, file_name))
			file_name = file_name.replace(self.LSEP, '')

			# check each file for the Byte Order Marker;
			# according to the MDN spec, localization files should *not* contain BOM
			# https://developer.mozilla.org/en/XUL_Tutorial/Localization
			bytes = min(32, os.path.getsize(file_path))
			with open(file_path, 'rb') as rawfile:
				if rawfile.read(bytes).startswith(codecs.BOM_UTF8):
					self._log_error("File '{0}' contains Byte Order Marker; localization files should not contain BOM."\
						.format(file_path))

			if (file_path.endswith('.dtd')):
				with open(file_path, 'r') as openfile:
					try:
						dtd = etree.DTD(openfile)
						for entity in dtd.entities():
							# note: lxml actually removes duplicate entities when parsing;
							# it always takes the first entry.
							key = file_name + self.LSEP + entity.name
							if key in self.keys:
								self._log_error("Duplicate dtd key '{0}' found in {1}".format(\
									key, file_path))
							elif len(entity.content) < 1:
								warnings.warn("Key '{0}' in {1} has a blank value. Is this desired?".format(\
									key, file_path))
							# check for invalid content
							# lxml will already check for '%' in values when it parses the file
							elif '<' in entity.content:
								self._log_error("The value for '{0}' in {1} contains the invalid character '<'. This is not allowed; please remove this character.".format(\
									key, file_path))
							else:
								self.keys[key] = entity.content

					except (etree.DTDParseError) as ex:
						(string, line, column, errlevel, place, errname, message) = self._extract_first_dtd_parse_error_info(ex)

						# get the error line so we can show the user where the problem may be
						error_line = linecache.getline(file_path, int(line)).strip()
						linecache.clearcache()
						highlight_string = (" " * (int(column) - 1)) + "^"

						error_message = "DTD syntax error starting at Line {0}, Col {1}: {2}\n{3}\n{4}\n{5}\n{6}\n{7}".format(\
							line, column, message,
							"Error line shown below, problem marked with ^:",
							error_line, highlight_string,
							"Full error details:",
							ex.error_log)
						self._log_error("Could not parse {0}: {1}".format(\
							file_path, error_message))

			elif (file_path.endswith('.properties')):
				self._parse_properties_file(file_path)
			else:
				# not neccesarily a failure - there may just be extra files lying around.
				warnings.warn("File {0} is not a .dtd or .properties file. Ignoring.".format(file_path))

		return self.parsing_errors

	def _parse_properties_file(self, file_path):
		"""
		Extract localization string keys and values from a mozilla-style ".properties" file
		and add the results to the 'keys' and 'subs' dictionaries.

		https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files
		"""
		file_name = os.path.basename(file_path).replace(self.LSEP, '')
		lang = os.path.basename(os.path.dirname(file_path))

		with open(file_path, 'r') as openfile:
			data = openfile.read()

			if (len(data) < 1):
				warnings.warn("{0} does not contain any lines".format(file_path))
				return

			data = re.sub(self.PROP_COMMENT, '', data)
			data = re.split(self.PROP_SEP, data)
			for line in data:
				if not line.strip():
					continue # skip blank lines
				logging.info(".prop line: '{0}'".format(line))
				numeric_subs_list = [] # list of numbered string substitutions, like %1$S.
				regular_subs = 0
				match = self.PROP_LINE.match(line)
				if (match):
					key = file_name + self.LSEP + match.group(1)
					value = match.group(2)
					if key in self.keys:
						self._log_error("Duplicate property key '{0}' found in {1}".format(\
							key, file_path))
					elif len(value) < 1:
						self._log_error("Key '{0}' in {1} has a blank value".format(\
							key, file_path))
					# the only special character for .properties files is %
					# used to substitute values when calling strbundle.getFormattedString().
					# https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files#Text_Formatting
					# there are three valid options:
					# 1. no % on a line
					# 2. %% to escape and print a regular %
					# 3. %S or %n$S , where n is a number
					elif '%' in value:
						valid = True
						x = value.find('%')
						while x < len(value) and x != -1:
							# we don't save the (n$) group for anything;
							# we simply specify a group so we can make the entire group optional
							# with a trailing ?
							pmatch = re.match('%([0-9]+\$)?S', value[x:])

							if (x + 1 < len(value)) and value[x+1] == '%':
								x += 1 # double %% for escape sequence; print actual %
							elif pmatch:
								# advance 1 char for the trailing S
								# plus however many chars make up the numerical reference (if any)
								x += 1
								if pmatch.group(1):
									numeric_subs_list.append(int(pmatch.group(1).replace('$', '')))
									logging.info("String substitution found. {0}".format(numeric_subs_list))
									x += len(pmatch.group(1))
								else:
									regular_subs += 1
							else:
								self._log_error("key '{0}' contains improper use of % in {1}. Position marked by ^ below:\n{2}\n{3}".format(\
									key, file_path, value, "{0}^".format(" " * x)))
								valid = False
								break

							x = value.find('%', x+1)

						if valid:
							self.keys[key] = value
							# different languages can of course use substitutions in different orders
							# but sort so we can ensure the count and type are the same
							numeric_subs_list.sort()
							if (numeric_subs_list and numeric_subs_list[-1] > self.MOZILLA_MAX_PROPERTIES_STRING_SUBS) or \
								regular_subs > self.MOZILLA_MAX_PROPERTIES_STRING_SUBS or \
								(numeric_subs_list and \
									((numeric_subs_list[-1] + regular_subs) > self.MOZILLA_MAX_PROPERTIES_STRING_SUBS)):
								self._log_error("More than {0} string substitutions found for key '{1}' "
								"in '{2}'. Mozilla does not allow this for performance reasons. "
								"See https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp "
								"".format(self.MOZILLA_MAX_PROPERTIES_STRING_SUBS, key, lang))

							self.subs[key] = ''.join(str(numeric_subs_list))

					else:
						self.keys[key] = value
				elif len(line) > 0: # not an empty string
					self._log_error("line '{0}' does not match any .properties file patterns for {1}".format(\
						line, file_path))

		return


def _validate_manifests(loc_dir, langs):
	"""
	Validate localization contents of the Mozilla extension information files:
	chrome.manifest and install.rdf.
	"""

	plugin_dir = os.path.abspath(os.path.join(loc_dir, '../..'))
	if not (os.path.exists(plugin_dir) and os.path.isdir(plugin_dir)):
		_log_error("Main plugin directory {0} does not exist; cannot validate chrome.manifest. "
			"If you wish to skip validation of chrome.manifest please specify the "
			"--no-manifest switch when running tests.".format(plugin_dir))
		return

	manifest = os.path.join(plugin_dir, 'chrome.manifest')
	if not (os.path.exists(manifest)):
		_log_error("File chrome.manifest does not exist in {0} ; cannot validate chrome.manifest. "
			"If you wish to skip validation of chrome.manifest please specify the "
			"--no-manifest switch when running tests.".format(plugin_dir))
		return

	manifest_locales = {}
	rdf_locales = {}

	# parse the chrome.manfiest file and save locale data.
	# manifest files use a simple line-based format:
	# https://developer.mozilla.org/en-US/docs/Chrome_Registration#The_Chrome_Registry
	#
	# we're only worried about 'locale' lines. They look like:
	#   locale packagename localename uri/to/files/ [flags]
	# e.g.
	#   locale extension-name pl chrome/locale/pl/
	#
	# TODO: We could ad a test to check that the file location exists
	with open(manifest, 'r') as m:
		lines = m.readlines()
		i = 1 # save the line number to help users troubleshoot any problems
		for line in lines:
			match = MANIFEST_LOCALE_LINE.match(line)
			if match:
				locale = match.groups(1)[0]
				if locale not in manifest_locales:
					manifest_locales[locale] = i
				else:
					_log_error("Locale '{0}' is defined more than once inside chrome.manifest. "
						"Each locale should only be defined once.".format(locale))
			i += 1


	# also parse install.rdf
	install_rdf = os.path.abspath(os.path.join(plugin_dir, 'install.rdf'))
	if not (os.path.exists(install_rdf)):
		_log_error("File install.rdf does not exist in {0} ; cannot validate. "
			"If you wish to skip validation please specify the "
			"--no-manifest switch when running tests.".format(plugin_dir))
		return

	try:
		xml = etree.parse(install_rdf)
		root = xml.getroot()
		for locale in root.findall('.//em:locale', root.nsmap):
			loc = locale.text
			if loc not in rdf_locales:
				rdf_locales[loc] = True
			else:
				_log_error("Locale '{0}' is defined more than once inside install.rdf. "
					"Each locale should only be defined once.".format(loc))
	except etree.XMLSyntaxError as ex:
		_log_error("Could not parse {0}: {1}".format(install_rdf, ex))


	# check every chrome.manifest entry to make sure a locale folder exists
	for locale in manifest_locales:
		locale_path = os.path.join(loc_dir, locale)
		if not (os.path.exists(locale_path)):
			_log_error("Locale folder '{0}' is specified in chrome.manifest "
				"line {1}, but {2} does not exist!".format(
					locale, manifest_locales[locale], locale_path))
		elif not (os.path.isdir(locale_path)):
			_log_error("Locale folder '{0}' is specified in chrome.manifest "
				"line {1}, but {2} is not a folder!".format(
					locale, manifest_locales[locale], locale_path))

		if locale not in localecodes.MOZILLA_LOCALE_CODES:
			warnings.warn("chrome.manifest locale '{0}' does not exist in the list of Mozilla locale codes.".format(
				locale))

	# check every install.rdf entry to make sure a locale folder exists
	for locale in rdf_locales:
		locale_path = os.path.join(loc_dir, locale)
		if not (os.path.exists(locale_path)):
			warnings.warn("Locale folder '{0}' is specified in install.rdf "
				"but {1} does not exist!".format(
					locale, locale_path))
		elif not (os.path.isdir(locale_path)):
			warnings.warn("Locale folder '{0}' is specified in install.rdf "
				"but {1} is not a folder!".format(
					locale, locale_path))

		if locale not in localecodes.MOZILLA_LOCALE_CODES:
			warnings.warn("install.rdf locale '{0}' does not exist in the list of Mozilla locale codes.".format(
				locale))

	# check every locale folder to ensure both
	# a manifest entry and an install.rdf entry exist
	for lang in langs:
		if (lang not in manifest_locales):
			_log_error("Locale folder '{0}' exists in {1}, but no corresponding entry "
				"exists in the chrome.manifest.".format(lang, loc_dir))
		if (lang not in rdf_locales):
			warnings.warn("Locale folder '{0}' exists in {1}, but no corresponding entry "
				"exists in install.rdf.".format(lang, loc_dir))



def validate_loc_files(loc_dir, parse_manifests=True):
	"""
	Validate localization contents inside the given base directory.
	Return True if there were any errors and False otherwise.
	"""
	global any_errors
	any_errors = False

	langs = {}

	print "Starting Localization tests..."

	loc_dir = os.path.abspath(loc_dir)
	if not (os.path.exists(loc_dir)):
		_log_error("The localization directory {0} does not exist!".format(loc_dir))
		return True
	logging.info("Loc directory {0} exists.".format(loc_dir))

	if not (os.path.isdir(loc_dir)):
		_log_error("{0} is not a directory!".format(loc_dir))
		return True
	logging.info("{0} is a directory.".format(loc_dir))

	for (root, dirs, files) in os.walk(loc_dir):
		for dir in dirs:
			langs[dir] = True

	if (len(langs) < 1):
		_log_error("Did not find any language folders inside {0}!".format(loc_dir))
		return True
	print "Found {0} languages: {1}.".format(len(langs), langs.keys())

	if BASE_LOC not in langs:
		_log_error("Base language folder '{0}' was not found in {1}".format(\
			BASE_LOC, loc_dir))
		return True

	if (parse_manifests):
		_validate_manifests(loc_dir, langs)

	baseline = LocalizationLanguage(loc_dir, BASE_LOC)
	parse_errors = baseline.get_loc_keys()
	any_errors = any_errors or parse_errors

	if (len(baseline.keys) < 1):
		_log_error("Did not find any keys in '{0}'!".format(baseline.name))
		return True

	if (any_errors):
		return True # error message has already been printed above

	print "{0} keys found in baseline '{1}'.".format(\
		len(baseline.keys), baseline.name)

	del langs[BASE_LOC] # don't test the baseline localization against itself

	for lang in langs:
		loc = LocalizationLanguage(loc_dir, lang)
		parse_errors = loc.get_loc_keys()
		any_errors = any_errors or parse_errors

		for key in loc.keys:
			if (key not in baseline.keys):
				_log_error("Key '{0}' in '{1}' but not in '{2}'".format(\
					key, loc.name, baseline.name))

		for key in baseline.keys:
			if (key not in loc.keys):
				_log_error("Key '{0}' in '{1}' but not in '{2}'".format(\
					key, baseline.name, loc.name))

		# make sure .properties string substitutions match
		# keys that don't exist in one loc will already have been caught above
		for key in loc.subs:
			if key not in baseline.subs:
				_log_error("String substitution for key '{0}' found in '{1}' but not in baseline {2}!".format(\
					key, loc.name, baseline.name))
			elif loc.subs[key] != baseline.subs[key]:
				_log_error("String substitution for key '{0}' in '{1}' "
					"is not the same as baseline '{2}'. "
					"Substitution count and type must match.\n{1}:{3}\n{2}:{4}".format(\
					key, loc.name, baseline.name, loc.subs[key], baseline.subs[key]))

		for key in baseline.subs:
			if key not in loc.subs:
				_log_error("String substitution for key '{0}' found in baseline {1} but not in '{2}'!".format(\
					key, baseline.name, loc.name))
			elif loc.subs[key] != baseline.subs[key]:
				_log_error("String substitution for key '{0}' in baseline '{1}' "
					"is not the same as '{2}'. "
					"Substitution count and type must match.\n{1}:{4}\n{2}:{3}".format(\
					key, baseline.name, loc.name, loc.subs[key], baseline.subs[key]))

	print "Done!"
	return any_errors


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('loc_dir',
			help="Directory where Mozilla-style localization files are located.")
	verbosity_group = parser.add_mutually_exclusive_group()
	verbosity_group.add_argument('--verbose', '-v', default=False, action='store_true',
			help="Verbose mode. Print more info about files and tests.")
	verbosity_group.add_argument('--quiet', '-q', default=False, action='store_true',
			help="Quiet mode. Don't print much, not even error info.")

	parser.add_argument('--no-manifest', '--nm', default=False, action='store_true',
			help="Do not attempt to parse or validate chrome.manifest or install.rdf. "
				"Mainly intended to allow easier unit-testing of checkloc itself; "
				"you should usually *NOT* use this flag.")

	args = parser.parse_args()

	loglevel = logging.WARNING
	if (args.verbose):
		loglevel = logging.INFO
	elif (args.quiet):
		loglevel = logging.CRITICAL

	logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)
	# send warning messages through our logging system
	# with the desired formatting
	logging.captureWarnings(True)
	warnings.formatwarning=_format_warning

	parse_manifests = True
	if (args.no_manifest):
		parse_manifests = False

	errors = validate_loc_files(args.loc_dir, parse_manifests=parse_manifests)
	if (errors):
		sys.exit(1)
	else:
		sys.exit(0)
