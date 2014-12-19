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

1. No localization has extra files
2. No localization is missing files
3. Each localization has at least one key
4. No localization has extra keys
5. No localization is missing keys
6. No key is blank
7. DTD keys contain no invalid characters, including ```"!@#$%^&*<>[](){} ?```
8. DTD values contain no invalid characters, including ```"%<```
9. DTD comments contain no double hyphens ```--```
10. No localization has duplicate keys defined in the same ```.properties``` file  
	(the same key defined in different ```.properties``` files is okay - presumably they will be loaded and used in different string bundles)
11. ```.properties``` values are valid, meaning either:
  1. no ```%``` on a line
  2. double ```%%``` to escape and print a regular ```%```
  3. ```%S``` or ```%n$S``` , where ```n``` is a number, for formatted string replacement.
12. ```.properties``` values use the same count and type of string substitutions across languages. e.g.:
  1. If one language uses ```%1$S```, ```%2$S```, and ```%3$S```, they all should  
  (order of substitutions may of course differ between languages)
  2. If one language uses four ```%S``` they all should
13. **Mozilla-specific:** No ```.properties``` value contains more than 10 unique string substitutions - either ```%S``` style, numbered ```%1$S``` style, or combined. [See References](#max10subs).  
  (It is of course valid to re-use any ```%1$S``` style numbered substitution as many times as you want)
14. No files contain the [Byte Order Marker (BOM)](https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Property_Files#Escape_non-ASCII_Characters)


### Possible future test cases

* Test that the localization has no duplicate DTD entities defined in the same file  
(currently both lxml and Firefox remove duplicate entities when parsing. This test would simply provide a warning for builders, as it's probably not what they intended).

## References

1. [Java ```.properties``` file specification](http://docs.oracle.com/javase/8/docs/api/java/util/Properties.html)
2. [Wikipedia - ```.properties```](https://en.wikipedia.org/wiki/.properties)
3. <a name="max10subs"></a>[nsStringBundle.cpp](https://mxr.mozilla.org/mozilla-central/source/intl/strres/nsStringBundle.cpp) - ```FormatString()``` only supports at most 10 string substitution parameters:  
	```// this function supports at most 10 parameters.. see below for why```  
	```// ...```  
	```NS_ENSURE_ARG(aLength <= 10); // enforce 10-parameter limit```
