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

# list of many Mozilla locale codes
# kept in a separate file so it doesn't take up space in the main module.
# https://wiki.mozilla.org/L10n:Localization_Teams

MOZILLA_LOCALE_CODES = {
	'ach': True,
	'af': True,
	'ak': True,
	'am': True,
	'an': True,
	'anp': True,
	'ar': True,
	'arq': True,
	'as': True,
	'ast': True,
	'aym': True,
	'az': True,
	'bal': True,
	'bcl': True,
	'be': True,
	'bg': True,
	'bg-IV': True,
	'bho': True,
	'bm': True,
	'bn-BD': True,
	'bn-IN': True,
	'bo': True,
	'bpy': True,
	'br': True,
	'brx': True,
	'bs': True,
	'bzj-BZ': True,
	'ca': True,
	'ca-valencia': True,
	'cak-GT': True,
	'cax-BO': True,
	'cbk': True,
	'chf-MX': True,
	'ckb': True,
	'cly-MX': True,
	'co': True,
	'crh': True,
	'crn-MX': True,
	'cs': True,
	'ctu-MX': True,
	'cy': True,
	'da': True,
	'de': True,
	'doi': True,
	'dsb': True,
	'dz': True,
	'el': True,
	'en-ARRR': True,
	'en-CA': True,
	'en-GB': True,
	'en-Shaw': True,
	'en-US': True,
	'en-ZA': True,
	'eo': True,
	'es': True,
	'es-AR': True,
	'es-ES': True,
	'es-CL': True,
	'es-MX': True,
	'et': True,
	'eu': True,
	'fa': True,
	'ff': True,
	'fi': True,
	'fj': True,
	'fo': True,
	'fr': True,
	'fur': True,
	'fy-NL': True,
	'ga-IE': True,
	'gd': True,
	'gl': True,
	'gn-BO': True,
	'gn-PY': True,
	'gu-IN': True,
	'ha': True,
	'haw': True,
	'hch-MX': True,
	'he': True,
	'hi-IN': True,
	'hr': True,
	'hsb': True,
	'ht': True,
	'hu': True,
	'hus-MX': True,
	'hy-AM': True,
	'id': True,
	'ig': True,
	'ilo': True,
	'is': True,
	'it': True,
	'ixl-GT': True,
	'ja': True,
	'jam-JM': True,
	'jbo': True,
	'jv': True,
	'ka': True,
	'kab': True,
	'kea': True,
	'kek-GT': True,
	'ky': True,
	'ky-cyrl': True,
	'ki': True,
	'kj': True,
	'kk': True,
	'km': True,
	'kn': True,
	'ko': True,
	'kok': True,
	'ks': True,
	'ks-deva': True,
	'ku': True,
	'kw': True,
	'la': True,
	'laj': True,
	'lb': True,
	'lg': True,
	'lgg': True,
	'lij': True,
	'lmo': True,
	'lo': True,
	'lt': True,
	'lv': True,
	'mai': True,
	'mam-GT': True,
	'man': True,
	'mni': True,
	'mag': True,
	'mau-MX': True,
	'meh-MX': True,
	'mg': True,
	'mi': True,
	'min': True,
	'mit-MX': True,
	'mix-MX': True,
	'mk': True,
	'ml': True,
	'mn': True,
	'mqh-MX': True,
	'mr': True,
	'ms': True,
	'mxp-MX': True,
	'my': True,
	'myv': True,
	'nb-NO': True,
	'nch-MX': True,
	'nci-MX': True,
	'ncj-MX': True,
	'nd': True,
	'ne-NP': True,
	'nl': True,
	'nn-NO': True,
	'nso': True,
	'nv': True,
	'ny': True,
	'oc': True,
	'oc-ES-aranese': True,
	'om': True,
	'or': True,
	'os': True,
	'ote-MX': True,
	'oto-MX': True,
	'pa': True,
	'prs': True,
	'pl': True,
	'pms': True,
	'ppl-SV': True,
	'ps': True,
	'pt-BR': True,
	'pt-PT': True,
	'quh': True,
	'quy': True,
	'quz': True,
	'qvi-EC': True,
	'rm': True,
	'rn': True,
	'ro': True,
	'ru': True,
	'rue': True,
	'rw': True,
	'sa': True,
	'sah': True,
	'sc': True,
	'scn': True,
	'shn': True,
	'si': True,
	'sio-US-lkt': True,
	'sk': True,
	'sl': True,
	'sm': True,
	'sn': True,
	'sna-zw': True,
	'son': True,
	'sq': True,
	'sr': True,
	'szl': True,
	'srd': True,
	'st': True,
	'su': True,
	'sv-SE': True,
	'sw': True,
	'ta': True,
	'ta-LK': True,
	'te': True,
	'tg': True,
	'th': True,
	'ti': True,
	'tl': True,
	'tn': True,
	'to': True,
	'toj-MX': True,
	'tr': True,
	'trs-MX': True,
	'teo': True,
	'tsz-MX': True,
	'tt': True,
	'tzh-MX': True,
	'tzj-GT': True,
	'tzo-MX': True,
	'ug': True,
	'uk': True,
	'ur': True,
	'uz': True,
	'vi': True,
	'vmz-MX': True,
	'wa': True,
	'wo': True,
	'xh': True,
	'xog': True,
	'yaq-MX': True,
	'yo': True,
	'yo-NG': True,
	'yua-MX': True,
	'yue': True,
	'zai': True,
	'zam-MX': True,
	'zar-MX': True,
	'zh-CN': True,
	'zh-TW': True,
	'zty-MX': True,
	'zu': True
}