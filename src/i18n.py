"""UI languages. Each lang/<code>.json has the interface strings, the thousands separator and the
translations of the Spanish messages raised by tracker.py. Adding a language = adding one JSON file."""
import re,json
from resources import BASE
LANGS={}
for path in sorted((BASE/'lang').glob('*.json')):
 try:LANGS[path.stem]=json.loads(path.read_text('utf-8'))
 except ValueError:pass
DEFAULT_LANG='en' if 'en' in LANGS else next(iter(LANGS))
def text(lang,key,**kw):
 value=LANGS.get(lang,{}).get('strings',{}).get(key) or LANGS[DEFAULT_LANG]['strings'].get(key,key)
 return value.format(**kw)
def label(lang):return LANGS[lang].get('label',lang.upper())
def number(lang,value):
 return f'{value:,}'.replace(',',LANGS.get(lang,{}).get('thousands',','))
def tracker_text(message,lang):
 data=LANGS.get(lang,{})
 if message in data.get('tracker',{}):return data['tracker'][message]
 for rule in data.get('tracker_patterns',[]):
  match=re.match(rule['pattern'],message,re.S)
  if match:return rule['text'].format(*match.groups())
 return message
