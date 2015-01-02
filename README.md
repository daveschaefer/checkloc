# Checkloc

Validate a set of [Mozilla-style localization files](https://developer.mozilla.org/en-US/docs/Mozilla/Localization/Localizing_an_extension) (DTD and string bundle) to make sure all languages have the same keys with the right syntax.

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

Test cases marked with *[w]* generate a warning; all other cases generate errors.

### Basic validation and syntax

1. No localization has extra files
2. No localization is missing files
3. Each localization has at least one key
4. No localization has extra keys
5. No localization is missing keys
6. No key is blank
7. DTD keys contain no invalid characters, including ```"!@#$%^&*<>[](){} ?'```
8. DTD values contain no invalid characters, including ```"%<&```  
	(you can use the [HTML character entity codes](https://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references) ```&quot;```, ```&#37;```, ```&lt;```, and ```&amp;``` if you need to use those characters inside a DTD value)
9. *[w]* DTD values are not empty: ```""``` or ```''```  
  (using empty DTD values is valid, and your extension will build and run normally. No string will be displayed, however, so this may not be what you want)
10. DTD comments contain no double hyphens ```--```
11. ```.properties``` values are valid, meaning either:
  1. no ```%``` on a line
  2. double ```%%``` to escape and print a regular ```%```
  3. ```%S``` or ```%n$S``` , where ```n``` is a number, for formatted string replacement.
12. No files contain the [Byte Order Marker (BOM)](https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files#Escape_non-ASCII_Characters)

### Language consistency

1. No localization has duplicate keys defined in the same ```.properties``` file  
	(the same key defined in different ```.properties``` files is okay - presumably they will be loaded and used in different string bundles)
2. ```.properties``` values use the same count and type of string substitutions across languages. e.g.:
  1. If one language uses four ```%S``` they all should
  2. If one language uses ```%1$S```, ```%2$S```, and ```%3$S```, they all should  
  (order of substitutions may of course differ between languages)

### Mozilla-specific

1. ```.properties``` keys contain no spaces
2. No ```.properties``` value contains more than 10 unique string substitutions - either ```%S```-style, numbered ```%1$S```-style, or combined. [See References](#max10subs).  
  (It is of course valid to re-use any ```%1$S```-style numbered substitution as many times as you want)

### Manifest files

1. All ```locale``` entries in ```chrome.manifest``` have a locale folder in the correct location on disk
2. All locale folders on disk have an entry in ```chrome.manifest```
3. No ```locale``` in ```chrome.manifest``` is defined more than once
4. *[w]* All ```locale``` entries in ```chrome.manifest``` exist in the list of known Mozilla locale codes
5. ```install.rdf``` contains only valid XML
6. *[w]* All ```<em:locale>``` entries in ```install.rdf``` have a locale folder in the correct location on disk
7. *[w]* All locale folders on disk have an entry in ```install.rdf```
8. No ```<em:locale>``` in ```install.rdf``` is defined more than once
9. *[w]* All ```<em:locale>``` entries in ```install.rdf``` exist in the list of known Mozilla locale codes


## Possible future test cases

* Test that the localization has no duplicate DTD entities defined in the same file  
(currently both lxml and Firefox remove duplicate entities when parsing. This test would simply provide a warning for builders, as it's probably not what they intended).

## References

1. [Java ```.properties``` file specification](http://docs.oracle.com/javase/8/docs/api/java/util/Properties.html)
2. [Wikipedia - ```.properties```](https://en.wikipedia.org/wiki/.properties)
3. <a name="max10subs"></a>[nsStringBundle.cpp](https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp) - ```FormatString()``` only supports at most 10 string substitution parameters:  
	```// this function supports at most 10 parameters.. see below for why```  
	```// ...```  
	```NS_ENSURE_ARG(aLength <= 10); // enforce 10-parameter limit```
4. [Extensible Markup Language (XML) 1.1](http://www.w3.org/TR/xml11/#sec-entity-decl])
5. [```chrome.manifest``` file format](https://developer.mozilla.org/en-US/docs/Chrome_Registration)
6. [Add-on Install Manifests](https://developer.mozilla.org/en-US/Add-ons/Install_Manifests)
7. [Mozilla Localization ("L10n") Teams](https://wiki.mozilla.org/L10n:Localization_Teams)
8. [Mozilla Locale Codes](https://wiki.mozilla.org/L10n:Locale_Codes)
