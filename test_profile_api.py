import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
import profile_api as p
class ProfileTests(unittest.TestCase):
 def test_profile_kill_statistics_are_not_foundry_kills(self):
  r=p.inspect_profile({'96':12000,'127':15000,'93':[]})
  self.assertFalse(r['foundry_supported']);self.assertEqual(set(r['missing_foundry_fields']),set(p.REQUIRED))
 def test_field_codes_are_resolved_without_values_or_ids_in_report(self):
  r=p.inspect_profile({'96':'PRIVATE_VALUE','id':'PRIVATE_UID'})
  self.assertIn('kill',r['recognized_fields']);self.assertNotIn('PRIVATE',str(r))
 def test_ambiguous_names_rejected(self):
  with self.assertRaises(ValueError):p.inspect_profile({'96':1,'kill':2})
 def test_lookalike_maps_never_enable_unverified_transport(self):
  with self.assertRaises(p.UnsupportedProfile):p.to_foundry_snapshot(dict.fromkeys(p.REQUIRED,{}))
 def test_no_counters_in_known_profile_schema(self):self.assertFalse(set(p.REQUIRED)&set(p.FIELDS.values()))
 def test_completed_collection_does_not_invent_weapon_kills(self):
  # Synthetic profile; it is not a captured response from NetEase.
  r=p.inspect_completed_foundry({'191':{'16034':1793300000}})
  self.assertFalse(r['network_response_verified']);self.assertFalse(r['foundry_supported'])
  self.assertFalse(r['weapon_kills_available']);self.assertFalse(r['in_progress_counts_available'])
  g=next(x for x in r['collections'] if x['id']==16034)
  self.assertEqual(g['state'],'reported_complete');self.assertIsNone(g['kills']);self.assertIsNone(g['progress'])
 def test_absent_achievement_is_unknown_not_zero_or_incomplete(self):
  r=p.inspect_completed_foundry({'AchiFinishTime':{}})
  self.assertTrue(all(g['state']=='unknown' and g['progress'] is None for g in r['collections']))
 def test_completion_map_requires_dictionary_data(self):
  for value in ('[]',None,[],True):
   with self.subTest(value=value),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':value})
 def test_malformed_completion_values_are_rejected(self):
  for aid,ts in [('016034',1),('١٦٠٣٤',1),('16034',True),('16034',0),('16034',-1),('16034',2**63)]:
   with self.subTest(aid=aid,ts=ts),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':{aid:ts}})
 def test_completion_projection_collision_rejected(self):
  with self.assertRaises(ValueError):p.inspect_completed_foundry({'191':{},'AchiFinishTime':{}})
 def test_unrelated_kill_total_does_not_create_completion_projection(self):
  with self.assertRaises(p.UnsupportedProfile):p.inspect_completed_foundry({'96':99999999})
 def test_partial_completion_projection_cannot_become_full_snapshot(self):
  with self.assertRaises(p.UnsupportedProfile):p.to_foundry_snapshot({'191':{'16034':1793300000}})
 def test_numeric_literal_from_sdk_is_read_without_evaluation(self):
  r=p.inspect_completed_foundry({'191':'{16034: 1793300000}'})
  self.assertEqual(next(x for x in r['collections'] if x['id']==16034)['state'],'reported_complete')
 def test_expressions_calls_and_unpacking_are_rejected(self):
  for value in ('{16034: 1+2}',"{16034: __import__('os').getpid()}",'{**{16034: 1}}',
                '{16034: x for x in [1]}','dict(16034=1)'):
   with self.subTest(value=value),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':value})
 def test_duplicate_aliases_in_literal_or_decoded_map_are_rejected(self):
  for value in ("{16034: 1, '16034': 2}",'{16034: 1, 16034: 2}',{16034:1,'16034':2}):
   with self.subTest(value=value),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':value})
 def test_literal_size_and_nesting_are_bounded(self):
  for value in (' '*262145,'['*1000+'0'+']'*1000):
   with self.subTest(length=len(value)),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':value})
 def test_booleans_and_float_literals_do_not_become_timestamps(self):
  for value in ('{16034: True}','{True: 1}','{16034: 1.5}'):
   with self.subTest(value=value),self.assertRaises(ValueError):p.inspect_completed_foundry({'191':value})
if __name__=='__main__':unittest.main()
