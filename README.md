Checkloc
========

Validate a set of Mozilla-style localization files to make sure all localizations have the same keys in the same places. This script can be run before deploying your Firefox extension to test that localization data is valid.

The script works by selecing one localization language as the 'baseline' and comparing other languages against it. The syntax of every file and localization entry is also tested.


Current test cases:

* Localization has no extra files (compared to the baseline)
* Localization has no missing files (compared to the baseline)
* Localization has at least one key
* Localization has no extra keys
* Localization has no missing keys
* Localization has no duplicate keys defined in the same .properties file
	(the same key name defined in different files is okay - presumably they will be loaded and used in different stringbundles)
* Key values are not empty
* Key names contain no invalid characters, including "!@#$%^&*<>[](){} ?
* DTD values contain no invalid characters, including "%<
* DTD comments contain no double hyphens '--'
* .properties values are valid, meaning either:
		1. no % on a line
		2. double %% to escape and print a regular %
		3. %S or %n$S , where n is a number, for formatted string replacement.
* .properties values use the same count and type of string substitutions across languages
* No files contain the Byte Order Marker (BOM)


Unimplemented:

* Test that the localization has no duplicate DTD entities defined in the same file
(currently an lxml limitation; lxml removes duplicate entities when parsing. but so does firefox, so the built plugin will still be valid. this test would simply be a warning for builders, as it's probably not what	they intended).


Requirements
------------
* python
* the lxml python library


Usage
-----
See the python script docstrings for up-to-date usage information
(e.g. call it with 'python checkloc.py -h')
