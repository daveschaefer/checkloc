# Checkloc

Validate a set of [Mozilla-style localization files](https://developer.mozilla.org/en-US/docs/Mozilla/Localization/Localizing_an_extension) (XUL and string bundle) to make sure all languages have the same keys with the right syntax.

This script can be run before deploying your Firefox or SeaMonkey extension to test that localization data is valid. It compares the localization keys and location and checks the syntax of every file and localization entry.


## Requirements

* [python](https://www.python.org/downloads/) 2.7 or higher
* the [lxml python library](http://lxml.de/)

### Installation

```
>git clone https://github.com/daveschaefer/checkloc.git
>pip install lxml
```


## Usage

```>python checkloc/checkloc.py path/to/your/plugin/chrome/locale```

Or run ```>python checkloc/checkloc.py --help```



## Current test cases

1. No localization has extra files
2. No localization is missing files
3. Each localization has at least one key
4. No localization has extra keys
5. No localization is missing keys
6. No localization has duplicate keys defined in the same ```.properties``` file  
	(the same key name defined in different files is okay - presumably they will be loaded and used in different string bundles)
7. No key is blank
8. DTD keys contain no invalid characters, including ```"!@#$%^&*<>[](){} ?```
9. DTD values contain no invalid characters, including ```"%<```
10. DTD comments contain no double hyphens ```--```
11. ```.properties``` values are valid, meaning either:
  1. no ```%``` on a line
  2. double ```%%``` to escape and print a regular ```%```
  3. ```%S``` or ```%n$S``` , where ```n``` is a number, for formatted string replacement.
12. ```.properties``` values use the same count and type of string substitutions across languages (i.e. if one language uses ```%1$S``` and ```%2$S```, they all should)
13. No files contain the [Byte Order Marker (BOM)](https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files#Escape_non-ASCII_Characters)


### Possible future test cases

* Test that the localization has no duplicate DTD entities defined in the same file  
(currently both lxml and Firefox remove duplicate entities when parsing. This test would simply provide a warning for builders, as it's probably not what they intended).
