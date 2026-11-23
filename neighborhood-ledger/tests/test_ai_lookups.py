import json,tempfile,unittest
from unittest.mock import Mock,patch
import ai_lookups as lookup
import ledger_ai

class Store:
 def findings(self):return []
 def workspace(self):return {'state':{'issues':[{'caseNo':'SR-12345','notes':'private concern'}],'office':{'records':[]}}}

def found():return {'caseNumber':'SR-12345','status':'found','checkedAt':'2026-11-02T18:00:00Z','sourceUrl':'https://houston311.powerappsportals.us/en-US/checkcasestatus/','record':{'caseNumber':'SR-12345','cityStatus':'Closed','serviceType':'Street repair','address':'100 Test Street','url':'https://houston311.powerappsportals.us/en-US/checkcasestatus/casedetail/?id=test'}}
def plan(name='check_311_case',args=None):return {'status':'completed','output':[{'type':'function_call','name':name,'namespace':'ledger','call_id':'call_1','arguments':json.dumps(args or {'case_number':'SR-12345'})}]}
def answer():return {'findings':[{'text':'The City reports the case closed, which does not independently confirm repair.','source_ids':['L1']}],'next_steps':['Confirm the condition on site.'],'missing_information':[],'follow_ups':[{'title':'Follow up case SR-12345','next_action':'Confirm whether the issue remains.','notes':'City status was checked; verify the condition.','source_ids':['L1']}]}

class LookupTests(unittest.TestCase):
 def test_case_requires_user_or_opted_in_saved_reference(self):
  with patch.object(lookup.case_status,'lookup',return_value=found()) as service:
   self.assertEqual(lookup.execute('check_311_case',{'case_number':'SR-12345'},'Summarize news',[])['status'],'needs_information');service.assert_not_called()
   self.assertEqual(lookup.execute('check_311_case',{'case_number':'SR-12345'},'Check SR-12345',[])['status'],'found')
   self.assertEqual(lookup.execute('check_311_case',{'case_number':'SR-12345'},'Check my saved cases',['SR-12345'])['status'],'found')
 def test_case_refs_are_opt_in(self):
  self.assertEqual(lookup.authorized_cases(Store(),False),[]);self.assertEqual(lookup.authorized_cases(Store(),True),['SR-12345'])
 def test_dispatch_rejects_unknown_tool_arguments_and_url(self):
  for name,args in [('send_email',{}),('check_311_case',{'case_number':'SR-12345','url':'https://example.org'}),('check_311_case',{'case_number':'https://example.org'})]:
   with patch.object(lookup.case_status,'lookup') as service:self.assertEqual(lookup.execute(name,args,'Check SR-12345',[])['status'],'needs_information');service.assert_not_called()
 def test_not_found_is_not_closed_or_cached(self):
  with patch.object(lookup.case_status,'lookup',return_value={'caseNumber':'SR-12345','status':'not_found','checkedAt':'now','sourceUrl':lookup.case_status.PAGE,'message':'No exact public match'}):
   result=lookup.execute('check_311_case',{'case_number':'SR-12345'},'Check SR-12345',[])
  self.assertEqual(result['status'],'not_found');self.assertNotIn('record',result)
 def test_full_orchestration_returns_reviewable_draft_without_writing(self):
  store=Store();store.save=Mock();assistant=Mock();assistant.call.side_effect=[((plan(),{}),'test-model'),((json.dumps(answer()),{}),'test-model')]
  with patch.object(lookup.case_status,'lookup',return_value=found()):result=lookup.ask_with_tools(assistant,store,{'question':'Check SR-12345 and prepare a follow-up'},'Test community')
  store.save.assert_not_called();self.assertEqual(result['followUps'][0]['caseNo'],'SR-12345');self.assertEqual(result['followUps'][0]['agency'],'Houston 311')
  payload=assistant.call.call_args.args[0];self.assertEqual(payload['tool_choice'],'none');self.assertTrue(any(i.get('type')=='function_call_output' for i in payload['input']));self.assertNotIn('private concern',json.dumps(payload))
  self.assertEqual(result['sources'][-1]['lookupStatus'],'found')
 def test_failed_summary_retains_lookup_results(self):
  assistant=Mock();assistant.call.side_effect=[((plan(),{}),'test-model'),ValueError('provider unavailable')]
  with patch.object(lookup.case_status,'lookup',return_value=found()):result=lookup.ask_with_tools(assistant,Store(),{'question':'Check SR-12345'},'Test')
  self.assertTrue(result['warning']);self.assertEqual(result['lookups'][0]['status'],'found');self.assertEqual(result['followUps'],[])
 def test_invalid_draft_citation_never_reaches_review(self):
  invalid=answer();invalid['follow_ups'][0]['source_ids']=['invented'];assistant=Mock();assistant.call.side_effect=[((plan(),{}),'test-model'),((json.dumps(invalid),{}),'test-model')]
  with patch.object(lookup.case_status,'lookup',return_value=found()):result=lookup.ask_with_tools(assistant,Store(),{'question':'Check SR-12345'},'Test')
  self.assertEqual(result['followUps'],[]);self.assertTrue(result['warning'])
 def test_duplicate_calls_execute_once(self):
  p=plan();p['output'].append({**p['output'][0],'call_id':'call_2'});assistant=Mock();assistant.call.side_effect=[((p,{}),'test-model'),((json.dumps(answer()),{}),'test-model')]
  with patch.object(lookup.case_status,'lookup',return_value=found()) as service:result=lookup.ask_with_tools(assistant,Store(),{'question':'Check SR-12345'},'Test')
  self.assertEqual(service.call_count,1);self.assertEqual(len(result['lookups']),1)
 def test_too_many_calls_execute_none(self):
  p=plan();p['output']=[{**p['output'][0],'call_id':str(i)} for i in range(4)];assistant=Mock();assistant.call.return_value=((p,{}),'test-model')
  with patch.object(lookup.case_status,'lookup') as service,self.assertRaises(ValueError):lookup.ask_with_tools(assistant,Store(),{'question':'Check SR-12345'},'Test')
  service.assert_not_called()
 def test_ambiguous_address_never_selects_a_parcel(self):
  with patch.object(lookup.deed_search,'find_properties_fields',return_value={'candidates':[{'address':'1042 Sampleoak Street'},{'address':'1042 Sampleoak Street unit 2'}]}),patch.object(lookup.deed_search,'search_restrictions') as records:
   result=lookup.execute('lookup_deed_address',{'street_number':'1042','street_name':'Sampleoak Street','zip_code':''},'Find restrictions for 1042 Sampleoak Street',[])
  self.assertEqual(result['status'],'ambiguous');records.assert_not_called()
 def test_address_and_subdivision_cannot_be_invented(self):
  with patch.object(lookup.deed_search,'find_properties_fields') as service:
   result=lookup.execute('lookup_deed_address',{'street_number':'1042','street_name':'Sampleoak Street','zip_code':''},'Find restrictions for 100 Main Street',[])
   self.assertEqual(result['status'],'needs_information');service.assert_not_called()
  with patch.object(lookup.deed_search,'search_subdivision') as service:
   self.assertEqual(lookup.execute('lookup_deed_subdivision',{'subdivision':'Oak Forest','section':'1'},'Look up Sunnyside',[])['status'],'needs_information');service.assert_not_called()
 def test_restriction_results_exclude_owners_and_preserve_partial(self):
  result=lookup.restriction_result({'records':[{'fileNumber':'123','grantees':['PRIVATE NAME']}],'errors':[{'message':'failed'}]})
  self.assertEqual(result['status'],'partial');self.assertNotIn('PRIVATE',json.dumps(result));self.assertIn('no legal determination',result['message'])
 def test_no_sources_can_explain_capabilities(self):
  a=Mock();a.call.side_effect=[(({'status':'completed','output':[]},{}),'test-model'),((json.dumps({'findings':[],'next_steps':['Supply a 311 case number for a live check.'],'missing_information':[],'follow_ups':[]}),{}),'test-model')]
  result=lookup.ask_with_tools(a,Store(),{'question':'What can you do?'},'Test');self.assertEqual(result['lookups'],[]);self.assertTrue(result['next_steps'])
