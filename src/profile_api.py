"""Capability gate for the known NameCard profile service. No transport or account access.
A generic kill statistic is never converted into per-weapon Foundry counters.
"""
import ast
import json
from pathlib import Path
FIELDS=json.loads(Path(__file__).with_name('namecard_fields.json').read_text('utf-8'))
REQUIRED=('weaponKillData','listenAchiData','finishAchiData')
class UnsupportedProfile(ValueError):pass

def _resolve_fields(record):
 if not isinstance(record,dict) or len(record)>1000:raise ValueError('Expected one decoded NameCard record.')
 resolved={}
 for key,value in record.items():
  if not isinstance(key,str):raise ValueError('Expected JSON string keys.')
  name=FIELDS.get(key,key)
  if name in resolved:raise ValueError('Ambiguous NameCard field names.')
  resolved[name]=value
 return resolved


def inspect_profile(record):
 keys=set(_resolve_fields(record))
 missing=[key for key in REQUIRED if key not in keys]
 # Even a caller-supplied object with those names is not proof of a supported endpoint.
 return dict(source='NameCard',field_count=len(keys),recognized_fields=sorted(keys & set(FIELDS.values())),missing_foundry_fields=missing,
             has_completion_projection='AchiFinishTime' in keys,
             foundry_supported=False,reason='NameCard has a static completed-achievement projection; weapon kill counts and in-progress Foundry counters remain unverified.')


def _read_completion_map(value):
 """Read only a bounded dictionary of numeric IDs and integer timestamps.

 The game uses literal parsing for some serialized values. Accept only this
 narrow dictionary shape; never evaluate expressions or instantiate objects.
 """
 if isinstance(value,str):
  if len(value)>262144:raise ValueError('Completion literal exceeds the size limit.')
  try:node=ast.parse(value,mode='eval').body
  except (SyntaxError,ValueError,RecursionError,MemoryError) as exc:
   raise ValueError('Invalid completion literal.') from exc
  if not isinstance(node,ast.Dict) or len(node.keys)>10000:
   raise ValueError('Expected a numeric dictionary literal.')
  pairs=[]
  for key,ts in zip(node.keys,node.values):
   if (not isinstance(key,ast.Constant) or type(key.value) not in (str,int)
       or not isinstance(ts,ast.Constant) or type(ts.value) is not int):
    raise ValueError('Only numeric ID/timestamp literals are accepted.')
   pairs.append((key.value,ts.value))
 elif isinstance(value,dict) and len(value)<=10000:pairs=value.items()
 else:raise ValueError('Expected a completion map with at most 10,000 entries.')
 result={}
 for aid,timestamp in pairs:
  if type(aid) is int:aid=str(aid)
  if (not isinstance(aid,str) or not aid.isascii() or not aid.isdecimal()
      or not 1<=len(aid)<=10 or aid.startswith('0')
      or not 0<int(aid)<=2147483647):
   raise ValueError('Invalid achievement identifier.')
  if aid in result:raise ValueError('Duplicate achievement identifier.')
  if type(timestamp) is not int or not 0<timestamp<=9223372036854775807:
   raise ValueError('Invalid achievement completion timestamp.')
  result[aid]=timestamp
 return result


def inspect_completed_foundry(record):
 """Inspect a caller-provided AchiFinishTime map or bounded numeric literal.

 This research importer does not connect to an API or authenticate a response.
 Absence means unknown: privacy, filtering and stale data can hide records.
 No weapon kills, in-progress counts or individual weapon completion is inferred.
 """
 fields=_resolve_fields(record)
 if 'AchiFinishTime' not in fields:
  raise UnsupportedProfile('Missing the decoded AchiFinishTime projection.')
 completed=_read_completion_map(fields['AchiFinishTime'])
 collections=json.loads(Path(__file__).with_name('catalog.json').read_text('utf-8'))['collections']
 return dict(source='caller_provided_NameCard_projection',network_response_verified=False,
             foundry_supported=False,weapon_kills_available=False,in_progress_counts_available=False,
             collections=[dict(id=g['id'],name=g['name'],
                 state='reported_complete' if str(g['id']) in completed else 'unknown',
                 reported_finished_at=completed.get(str(g['id'])),kills=None,progress=None)
                 for g in collections])

def to_foundry_snapshot(record):
 inspect_profile(record)
 raise UnsupportedProfile('NameCard is not a verified source for weapon kills and Foundry achievement progress. Import a Foundry Tracker JSON export instead.')
