import copy,json,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch,Mock
import ledger_ai as ai

class FakeStore:
    def workspace(self):return {'state':{'intelligence':[{'title':'Cleanup Saturday','summary':'Meet at the park.','url':'https://example.org/event','date':'2026-10-01'}], 'issues':[{'type':'Dumping','location':'100 Sample Street','notes':'Repeated report','status':'Open','contact':'PRIVATE CONTACT'}],'office':{'records':[{'kind':'Contact','title':'PRIVATE PERSON','notes':'PRIVATE CONTACT'},{'kind':'Assignment','title':'Follow up cleanup','notes':'Check site','contact':'PRIVATE CONTACT'}]}}}
    def findings(self):return []

class AssistantTests(unittest.TestCase):
    def test_recurring_public_events_keep_dates_in_evidence(self):
        s=FakeStore();s.workspace=lambda:{'state':{'events':[{'title':'Monthly neighborhood meeting','description':'Meet at the library','url':'https://example.org/events','eventDate':day,'sourceMode':'public_calendar'} for day in ['2026-11-02','2026-12-02']]}}
        self.assertEqual(len(ai.evidence(s,'meeting')['sources']),2)
    def test_private_work_excluded_by_default(self):
        d=ai.evidence(FakeStore(),'dumping');self.assertEqual(len(d['sources']),1);self.assertNotIn('Sample Street',json.dumps(d));self.assertNotIn('PRIVATE',json.dumps(d))
    def test_work_opt_in_excludes_contact_records_and_fields(self):
        d=ai.evidence(FakeStore(),'dumping',True);self.assertEqual(len(d['sources']),3);self.assertIn('100 Sample Street',json.dumps(d));self.assertNotIn('PRIVATE',json.dumps(d));self.assertEqual(d['sources'][0]['kind'],'Saved concern')
    def test_preview_is_subset_and_caps_text(self):
        s=FakeStore();s.findings=lambda:[{'title':str(i),'summary':'x'*10000,'url':'https://example.org/'+str(i)} for i in range(90)]
        d=ai.evidence(s,'brief');self.assertTrue(d['subset']);self.assertLessEqual(len(d['sources']),18);self.assertLess(len(json.dumps(d['sources'])),18000)
    def test_links_reject_credentials_and_active_content(self):
        for url in ['javascript:alert(1)','file:///etc/passwd','https://user:password@example.org','http://example.org']:self.assertEqual(ai.safe_url(url),'')
    def test_dpapi_key_round_trip_and_never_exposed(self):
        with tempfile.TemporaryDirectory() as root:
            a=ai.Assistant(root);key='sk-proj-'+('secret'*12);a.save({'apiKey':key,'model':ai.MODEL})
            self.assertNotIn(key,a.path.read_text());self.assertNotIn('key',a.status());self.assertEqual(a.credentials(),(key,ai.MODEL))
            a.save({'model':ai.MODEL});self.assertTrue(a.status()['configured']);a.save({'clearKey':True});self.assertFalse(a.status()['configured'])
    def test_missing_key_never_calls_provider(self):
        with tempfile.TemporaryDirectory() as root,patch.object(ai,'request_openai') as request:
            with self.assertRaisesRegex(ValueError,'Connect OpenAI'):ai.Assistant(root).test()
            request.assert_not_called()
    def test_grounded_request_and_output(self):
        output={'findings':[{'text':'A cleanup is listed.','source_ids':['S1']}],'next_steps':['Confirm the date.'],'missing_information':['The current schedule is not verified.']}
        with tempfile.TemporaryDirectory() as root,patch.object(ai,'request_openai',return_value=(json.dumps(output),{'total_tokens':10})) as request:
            a=ai.Assistant(root)
            with patch.object(a,'credentials',return_value=('test-key',ai.MODEL)):
                result=a.ask(FakeStore(),{'question':'Summarize the updates'},'Fifth Ward')
            payload=request.call_args.args[1];self.assertIs(payload['store'],False);self.assertNotIn('tools',payload);self.assertNotIn('PRIVATE',payload['input']);self.assertEqual(json.loads(payload['input'])['community'],'Fifth Ward');self.assertEqual(result['findings'],output['findings'])
    def test_unknown_citation_rejects_answer(self):
        with self.assertRaisesRegex(ValueError,'not given'):ai.validate_answer({'findings':[{'text':'Invented','source_ids':['S999']}],'next_steps':[],'missing_information':[]},['S1'])
    def test_no_source_finding_rejected(self):
        with self.assertRaises(ValueError):ai.validate_answer({'findings':[{'text':'Invented','source_ids':[]}],'next_steps':[],'missing_information':[]},['S1'])
    def test_no_records_does_not_send_question(self):
        s=FakeStore();s.workspace=lambda:{'state':None}
        with tempfile.TemporaryDirectory() as root,patch.object(ai,'request_openai') as request:
            with self.assertRaisesRegex(ValueError,'No saved records'):ai.Assistant(root).ask(s,{'question':'What is happening?'},'Test')
            request.assert_not_called()
    def test_test_connection_sends_no_records(self):
        with tempfile.TemporaryDirectory() as root,patch.object(ai,'request_openai',return_value=('Connected',{})) as request:
            a=ai.Assistant(root)
            with patch.object(a,'credentials',return_value=('test-key',ai.MODEL)):a.test()
            self.assertEqual(request.call_args.args[1]['max_output_tokens'],32);self.assertNotIn('community',request.call_args.args[1])
    def test_provider_error_hides_response_and_key(self):
        opener=Mock();opener.open.side_effect=urllib.error.HTTPError(ai.ENDPOINT,401,'secret-response',{},None)
        with patch.object(ai.urllib.request,'build_opener',return_value=opener):
            with self.assertRaisesRegex(ValueError,'did not accept') as err:ai.request_openai('secret-key',{})
            self.assertNotIn('secret',str(err.exception))
    def test_unfinished_provider_response_rejected(self):
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=b'{"status":"incomplete","output":[]}'
        opener=Mock();opener.open.return_value=response
        with patch.object(ai.urllib.request,'build_opener',return_value=opener):
            with self.assertRaisesRegex(ValueError,'did not finish'):ai.request_openai('test',{})
    def test_rate_limit_and_concurrency(self):
        with tempfile.TemporaryDirectory() as root,patch.object(ai,'request_openai',return_value=('Connected',{})) as request:
            a=ai.Assistant(root)
            with patch.object(a,'credentials',return_value=('test-key',ai.MODEL)):
                for _ in range(10):a.test()
                with self.assertRaisesRegex(ValueError,'wait a minute'):a.test()
                a.busy.acquire()
                try:
                    with self.assertRaisesRegex(ValueError,'already running'):a.test()
                finally:a.busy.release()
            self.assertEqual(request.call_count,10)
