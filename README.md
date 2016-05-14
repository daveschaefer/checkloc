# Checkloc

Validate [localizations](https://en.wikipedia.org/wiki/Language_localization) for your Firefox or SeaMonkey extension.

Checkloc is a localization [linter](https://en.wikipedia.org/wiki/Lint_%28software%29). It scans a set of [Mozilla-style localization files](https://developer.mozilla.org/en-US/docs/Mozilla/Localization/Localizing_an_extension) (`.dtd`, `.rdf`, and `.properties` string bundles) to make sure all languages have the same strings with the right syntax. It compares the string names and locations, and checks the syntax of every file and localization entry.


## Requirements

* [python](https://www.python.org/downloads/) 2.7 or higher
* the [lxml python library](http://lxml.de/)

### Installation

```
>git clone https://github.com/daveschaefer/checkloc.git
>pip install lxml
```


## Usage

```>python checkloc/checkloc.py path/to/your/extension```

Point the script at the directory that contains your extension's ```chrome.manifest``` file.

Or run ```>python checkloc/checkloc.py --help```


## Examples

**Normal output** - displays warnings and errors

```
>python checkloc/checkloc.py /your/amazing/extension
(Main) Starting Localization tests...
WARNING: (hr-HR) Locale folder 'hr-HR' exists in /your/amazing/extension/locale,
 but no corresponding entry exists in install.rdf.
WARNING: (ru) Locale folder 'ru' exists in /your/amazing/extension/locale, but n
o corresponding entry exists in install.rdf.
WARNING: (nl) Locale folder 'nl' exists in /your/amazing/extension/locale, but n
o corresponding entry exists in install.rdf.
(Main) Found 36 languages: ['el', 'zh-TW', 'vi', 'is', 'it', 'ar', 'uk-UA', 'cs'
, 'sv-SE', 'es-ES', 'ru', 'sl-SI', 'sr', 'lv-LV', 'tr', 'lt', 'en-US', 'ro', 'pl
', 'fr', 'bg', 'ms-MY', 'de', 'da', 'pt-BR', 'fi', 'hu', 'ja', 'he', 'hr-HR', 'p
t-PT', 'es-AR', 'ko', 'zh-CN', 'hy-AM', 'nl'].
(Main) 406 keys found in baseline 'en-US'.
ERROR: (hr-HR) Key 'amazing.properties/FF' in 'en-US' but not in 'hr-HR'
ERROR: (hr-HR) Key 'otherfile.properties/title.string' in 'en-US' but not in '
hr-HR'
(Main) Done!
```

**Group output by language** with ```--group-by-language```

```
>python checkloc/checkloc.py --group /your/amazing/extension
(Main) Starting Localization tests...
(Main) Found 36 languages: ['el', 'zh-TW', 'vi', 'is', 'it', 'ar', 'uk-UA', 'cs'
, 'sv-SE', 'es-ES', 'ru', 'sl-SI', 'sr', 'lv-LV', 'tr', 'lt', 'en-US', 'ro', 'pl
', 'fr', 'bg', 'ms-MY', 'de', 'da', 'pt-BR', 'fi', 'hu', 'ja', 'he', 'hr-HR', 'p
t-PT', 'es-AR', 'ko', 'zh-CN', 'hy-AM', 'nl'].
(Main) 406 keys found in baseline 'en-US'.
(Main) Done!
WARNING: (hr-HR) Locale folder 'hr-HR' exists in /your/amazing/extension/locale,
 but no corresponding entry exists in install.rdf.
ERROR: (hr-HR) Key 'amazing.properties/FF' in 'en-US' but not in 'hr-HR'
ERROR: (hr-HR) Key 'otherfile.properties/title.string' in 'en-US' but not in '
hr-HR'
WARNING: (nl) Locale folder 'nl' exists in /your/amazing/extension/locale, but n
o corresponding entry exists in install.rdf.
WARNING: (ru) Locale folder 'ru' exists in /your/amazing/extension/locale, but n
o corresponding entry exists in install.rdf.
```

**Output as JSON** with ```--json``` (also automatically groups by language)

```
>python checkloc/checkloc.py --json /your/amazing/extension
{
    "hr-HR": [
        "WARNING: (hr-HR) Locale folder 'hr-HR' exists in your\\amazing\\extensi
        on\\locale, but no corresponding entry exists in install.rdf.",

        "ERROR: (hr-HR) Key 'amazing.properties/FF' in 'en-US' but not in '
hr-HR'",
        "ERROR: (hr-HR) Key 'otherfile.properties/title.string' in 'en-US' but
 not in 'hr-HR'"
    ],
    "nl": [
        "WARNING: (nl) Locale folder 'nl' exists in your\\amazing\\extension\\lo
        cale, but no corresponding entry exists in install.rdf."
    ],
    "ru": [
        "WARNING: (ru) Locale folder 'ru' exists in your\\amazing\\extension\\lo
        cale, but no corresponding entry exists in install.rdf."
    ],
}
```


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
  (It is of course valid to re-use any one ```%1$S```-style numbered substitution as many times as you want)

### Manifest files

1. All ```locale``` lines in ```chrome.manifest``` are valid registration entries (i.e. syntax is valid)
2. All ```locale``` entries in ```chrome.manifest``` have a locale folder in the correct location on disk
3. All locale folders on disk have an entry in ```chrome.manifest```
4. No ```locale``` in ```chrome.manifest``` is defined more than once
5. *[w]* All ```locale``` entries in ```chrome.manifest``` exist in the list of known Mozilla locale codes
6. ```install.rdf``` contains only valid XML
7. *[w]* All ```<em:locale>``` entries in ```install.rdf``` have an entry in ```chrome.manifest```
8. *[w]* All ```<em:locale>``` entries in ```install.rdf``` have a locale folder in the correct location on disk
9. *[w]* All locale folders on disk have an entry in ```install.rdf```
10. No ```<em:locale>``` in ```install.rdf``` is defined more than once
11. *[w]* All ```<em:locale>``` entries in ```install.rdf``` exist in the list of known Mozilla locale codes


## Possible future test cases

* Test that the localization has no duplicate DTD entities defined in the same file  
(currently both lxml and Firefox remove duplicate entities when parsing. This test would simply provide a warning for builders, as it's probably not what they intended).

## References

1. [Java ```.properties``` file specification](http://docs.oracle.com/javase/8/docs/api/java/util/Properties.html)
2. [Wikipedia - ```.properties```](https://en.wikipedia.org/wiki/.properties)
3. Firefox <a name="max10subs"></a>[nsStringBundle.cpp](https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp) - ```FormatString()``` only supports at most 10 string substitution parameters:  
	```// this function supports at most 10 parameters.. see below for why```  
	```// ...```  
	```NS_ENSURE_ARG(aLength <= 10); // enforce 10-parameter limit```
4. [Extensible Markup Language (XML) 1.1](http://www.w3.org/TR/xml11/#sec-entity-decl])
5. [```chrome.manifest``` file format](https://developer.mozilla.org/en-US/docs/Chrome_Registration)
6. [```install.rdf``` - Add-on Install Manifests](https://developer.mozilla.org/en-US/Add-ons/Install_Manifests)
7. [Mozilla Localization ("L10n") Teams](https://wiki.mozilla.org/L10n:Localization_Teams)
8. [Mozilla Locale Codes](https://wiki.mozilla.org/L10n:Locale_Codes)
9. [Firefox iOS locales](https://github.com/mozilla/firefox-ios/blob/v3.x/shipping_locales.txt)
