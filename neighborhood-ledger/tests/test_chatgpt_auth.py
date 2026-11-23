import base64, hashlib, io, json, tempfile, time, unittest, urllib.parse, urllib.request
from unittest.mock import patch, Mock
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import chatgpt_auth as auth
import ledger_ai

META={'issuer':auth.ISSUER,'authorization_endpoint':auth.ISSUER+'/api/accounts/authorize','token_endpoint':auth.ISSUER+'/api/accounts/oauth/token','jwks_uri':auth.ISSUER+'/.well-known/jwks.json','revocation_endpoint':auth.ISSUER+'/oauth/revoke'}
PRIVATE=rsa.generate_private_key(public_exponent=65537,key_size=2048)
JWK=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(PRIVATE.public_key()));JWK['kid']='test'

def identity(client='issued-client',nonce='nonce',sub='test-user',**changes):
    claims={'iss':auth.ISSUER,'aud':client,'sub':sub,'nonce':nonce,'iat':int(time.time()),'exp':int(time.time())+3600,'email':'test@example.org',**changes}
    return jwt.encode(claims,PRIVATE,algorithm='RS256',headers={'kid':'test'})

def tokens(nonce='nonce',**changes):
    return {'access_token':'TEST_ACCESS_SECRET','refresh_token':'TEST_REFRESH_SECRET','id_token':identity(nonce=nonce),'expires_in':3600,'scope':auth.SCOPES,**changes}

class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.connection=auth.ChatGPTConnection(self.temp.name);self.addCleanup(self.connection.cancel)
    def begin(self):
        with patch.object(auth,'discovery',return_value=META),patch.object(auth.webbrowser,'open') as browser:
            result=self.connection.start()
        params=urllib.parse.parse_qs(urllib.parse.urlsplit(result['authorizationUrl']).query)
        self.assertEqual(browser.call_count,1)
        return params
    def provider(self,url,form=None,token=None):
        if url==META['token_endpoint']:return tokens(nonce=self.nonce)
        if url==META['jwks_uri']:return {'keys':[JWK]}
        if url==auth.RESOURCE+'/models':return {'models':[{'slug':'hidden','visibility':'hide'},{'slug':'account-model','display_name':'Account model','visibility':'list'}]}
        return {}
    def connect(self):
        params=self.begin();self.nonce=params['nonce'][0]
        with patch.object(auth,'remote_json',side_effect=self.provider):
            ok,message=self.connection.finish({'state':params['state'],'code':['one-time-code'],'client_id':['issued-client']})
        self.assertTrue(ok,message)
        return params
    def test_pkce_host_and_listener(self):
        params=self.begin();p=self.connection.pending
        self.assertEqual(params['client_id'],['dynamic_agent_client'])
        self.assertEqual(params['code_challenge'],[base64.urlsafe_b64encode(hashlib.sha256(p['verifier'].encode()).digest()).decode().rstrip('=')])
        self.assertEqual(params['redirect_uri'],[p['redirect']]);self.assertTrue(params['ext_agent_host_id'][0].startswith('urn:uuid:'))
        host=params['ext_agent_host_id'];self.connection.cancel();self.assertEqual(self.begin()['ext_agent_host_id'],host)
    def test_wrong_state_and_duplicate_params_do_not_exchange(self):
        p=self.begin()
        with patch.object(auth,'remote_json') as remote:
            self.assertFalse(self.connection.finish({'state':['wrong'],'code':['code']})[0])
            self.assertFalse(self.connection.finish({'state':p['state']*2,'code':['code']})[0]);remote.assert_not_called()
        self.assertIsNotNone(self.connection.pending)
    def test_callback_scope_catalog_encryption_and_replay(self):
        params=self.connect();status=self.connection.status()
        self.assertTrue(status['ready']);self.assertEqual(status['models'],[{'slug':'account-model','name':'Account model'}])
        self.assertNotIn('SECRET',json.dumps(status));self.assertNotIn(b'SECRET',self.connection.path.read_bytes())
        self.assertEqual(self.connection.credentials(),('TEST_ACCESS_SECRET','account-model'))
        self.assertFalse(self.connection.finish({'state':params['state'],'code':['replay'],'client_id':['issued-client']})[0])
    def test_denied_and_missing_issued_id(self):
        p=self.begin()
        with patch.object(auth,'remote_json') as remote:
            self.assertFalse(self.connection.finish({'state':p['state'],'error':['access_denied']})[0]);remote.assert_not_called()
        p=self.begin()
        with patch.object(auth,'remote_json') as remote:
            self.assertFalse(self.connection.finish({'state':p['state'],'code':['code']})[0]);remote.assert_not_called()
    def test_identity_rejects_nonce_issuer_audience_expiry_and_subject(self):
        with patch.object(auth,'remote_json',return_value={'keys':[JWK]}):
            self.assertEqual(auth.verify_identity(identity(),'issued-client','nonce',metadata=META)['sub'],'test-user')
            for changes in ({'nonce':'wrong'},{'iss':'https://example.org'},{'aud':'wrong'},{'exp':time.time()-60},{'iat':time.time()+60}):
                with self.subTest(changes=changes),self.assertRaises(ValueError):auth.verify_identity(identity(**changes),'issued-client','nonce',metadata=META)
            with self.assertRaises(ValueError):auth.verify_identity(identity(),'issued-client','nonce','another-user',META)
    def test_scope_requires_token_response_grant(self):
        for scope in ('','openid profile email resource.invoke'):
            with self.assertRaisesRegex(ValueError,'plan sharing'):self.connection.merge_tokens({},tokens(scope=scope),True)
    def test_returning_registration_and_account_mismatch(self):
        self.connect();params=self.begin();self.assertEqual(params['client_id'],['issued-client']);self.assertNotIn('agent_name_hint',params)
        with patch.object(auth,'remote_json') as remote:
            self.assertFalse(self.connection.finish({'state':params['state'],'code':['code'],'client_id':['different-client']})[0]);remote.assert_not_called()
        self.assertTrue(self.connection.status()['connected'])
    def test_refresh_rotates_once_and_preserves_scope(self):
        self.connect();c=self.connection.read();c['expires_at']=0;self.connection.write(c)
        with patch.object(auth,'discovery',return_value=META),patch.object(auth,'remote_json',return_value={'access_token':'NEW_ACCESS','refresh_token':'NEW_REFRESH','expires_in':3600}) as remote:
            self.assertEqual(self.connection.credentials()[0],'NEW_ACCESS');self.connection.credentials()
            self.assertEqual(remote.call_count,1);form=remote.call_args.args[1];self.assertEqual(form['client_id'],'issued-client');self.assertNotIn('scope',form)
        self.assertEqual(self.connection.read()['refresh_token'],'NEW_REFRESH')
    def test_signout_revokes_clears_tokens_and_preserves_welcome(self):
        self.connect();self.connection.welcome()
        with patch.object(auth,'discovery',return_value=META),patch.object(auth,'remote_json') as remote:
            self.connection.signout();self.assertEqual(remote.call_args.args[1]['token'],'TEST_REFRESH_SECRET')
        self.assertFalse(self.connection.status()['connected']);self.assertNotIn('access_token',self.connection.read());self.assertIn('test-user',self.connection.read()['welcomed_subjects'])
    def test_signout_network_failure_still_clears_local(self):
        self.connect()
        with patch.object(auth,'discovery',side_effect=ValueError('offline')):status=self.connection.signout()
        self.assertFalse(status['connected']);self.assertIn('could not be confirmed',status['message'])
    def stream(self,events,payload=None):
        response=io.BytesIO(b''.join(('data: '+json.dumps(e)+'\n\n').encode() for e in events));opener=Mock();opener.open.return_value=response
        with patch.object(auth,'opener',return_value=opener):
            result=auth.request_chatgpt('secret',payload or {'model':'account-model','input':'hello','max_output_tokens':32})
        return result,json.loads(opener.open.call_args.args[0].data)
    def test_stream_requires_completed_and_correct_oauth_contract(self):
        completed={'type':'response.completed','response':{'status':'completed','output':[{'content':[{'type':'output_text','text':'Connected'}]}],'usage':{'total_tokens':5}}}
        result,payload=self.stream([{'type':'response.output_text.delta','delta':'Connected'},completed])
        self.assertEqual(result[0],'Connected');self.assertTrue(payload['stream']);self.assertFalse(payload['store']);self.assertIsInstance(payload['input'],list);self.assertNotIn('max_output_tokens',payload)
        with self.assertRaisesRegex(ValueError,'before the answer finished'):self.stream([{'type':'response.output_text.delta','delta':'Partial'}])
    def test_stream_with_items_delivered_before_empty_completed_output(self):
        done={'type':'response.output_item.done','output_index':0,'item':{'type':'message','content':[{'type':'output_text','text':'Connected'}]}}
        completed={'type':'response.completed','response':{'status':'completed','output':[]}}
        result,_=self.stream([done,completed])
        self.assertEqual(result[0],'Connected')
        with self.assertRaisesRegex(ValueError,'before the answer finished'):
            self.stream([done])
    def test_stream_usage_error_after_partial_is_failure(self):
        with self.assertRaisesRegex(ValueError,'Manage usage'):self.stream([{'type':'response.output_text.delta','delta':'Partial'},{'type':'response.failed','response':{'error':{'code':'subscription_sharing_usage_limit_exceeded'}}}])
    def test_discovery_rejects_foreign_token_endpoint(self):
        with patch.object(auth,'remote_json',return_value={**META,'token_endpoint':'https://example.org/steal'}),self.assertRaises(ValueError):auth.discovery()
    def test_oauth_mode_never_falls_back_to_api_key(self):
        a=ledger_ai.Assistant(self.temp.name);a.save({'apiKey':'sk-'+('x'*30)});a.set_mode('chatgpt')
        with patch.object(ledger_ai,'request_openai') as api,self.assertRaisesRegex(ValueError,'Continue with ChatGPT'):a.test()
        api.assert_not_called()
    def test_settings_poll_reads_mode_after_completed_signin(self):
        a=ledger_ai.Assistant(self.temp.name)
        def completed():
            a.set_mode('chatgpt')
            return {'ready':True,'model':'account-model'}
        with patch.object(a.chatgpt,'status',side_effect=completed):
            status=a.status()
        self.assertTrue(status['configured']);self.assertEqual(status['authMode'],'chatgpt');self.assertEqual(status['model'],'account-model')
