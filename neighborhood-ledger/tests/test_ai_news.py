import datetime as dt,json,unittest
from unittest.mock import patch,Mock
import ai_news,ai_lookups
from communities import profile

NOW=dt.datetime(2026,11,2,18,tzinfo=dt.timezone.utc)
SOURCE={'id':'local-news','name':'Local news','url':'https://news.google.com/rss/search','host':'news.google.com','scope':'neighborhood','official':False}
def article(title='A new community park will open in Sunnyside this week',date='2026-11-02'):
 return {'title':title,'summary':'Publisher excerpt.','url':'https://news.google.com/rss/articles/one','publishedAt':date}

class NewsTests(unittest.TestCase):
 def test_city_incidents_elsewhere_excluded_but_local_match_retained(self):
  rows=[article('Investigation into fatal crash at Other Street'),{**article('Investigation into fatal crash in Sunnyside'),'matchedTerms':['Sunnyside']}]
  with patch.object(ai_news.collectors,'fetch_feed',return_value=b'feed'),patch.object(ai_news.collectors,'parse_feed',return_value={'status':'success','results':rows}):
   result=ai_news.check_source({**SOURCE,'scope':'citywide'},'71',NOW)
  self.assertEqual(result['count'],1);self.assertIn('Sunnyside',result['articles'][0]['title'])
 def test_live_check_rejects_old_undated_future_and_unsafe_links(self):
  rows=[article(),article(date='2020-01-01'),article(date=''),article(date='2026-12-02'),{**article(),'url':'javascript:alert(1)'}]
  with patch.object(ai_news.collectors,'fetch_feed',return_value=b'feed'),patch.object(ai_news.collectors,'parse_feed',return_value={'status':'success','results':rows}):
   result=ai_news.check_source(SOURCE,'71',NOW)
  self.assertEqual(result['count'],1)
 def test_failure_has_no_saved_fallback(self):
  with patch.object(ai_news.collectors,'fetch_feed',side_effect=OSError('offline')):
   result=ai_news.check_source(SOURCE,'71',NOW)
  self.assertEqual(result['status'],'failed');self.assertEqual(result['articles'],[])
 def test_stale_report_cannot_supply_current_articles(self):
  with patch.object(ai_news.collectors,'fetch_feed',return_value=b'feed'),patch.object(ai_news.collectors,'parse_feed',return_value={'status':'stale','results':[article()]}):
   self.assertEqual(ai_news.check_source(SOURCE,'71',NOW)['articles'],[])
 def test_worker_uses_selected_community(self):
  seen=[]
  def parse(*args,**kw):seen.append(profile()['id']);return {'status':'success','results':[article()]}
  with patch.object(ai_news.collectors,'fetch_feed',return_value=b'feed'),patch.object(ai_news.collectors,'parse_feed',side_effect=parse):ai_news.check_source(SOURCE,'71',NOW)
  self.assertEqual(seen,['71']);self.assertEqual(profile()['id'],'55')
 def test_no_model_selected_community_or_url(self):
  self.assertEqual(ai_lookups.validate('search_current_news',{},'Latest news',[]),{})
  with self.assertRaises(ValueError):ai_lookups.validate('search_current_news',{'community_id':'55'},'Latest news',[])
 def test_orchestration_cites_live_articles(self):
  store=Mock();store.community_id='71';store.workspace.return_value={'state':{}};store.findings.return_value=[]
  p={'status':'completed','output':[{'type':'function_call','name':'search_current_news','namespace':'ledger','call_id':'n1','arguments':'{}'}]}
  response={'findings':[{'text':'A new park is reported.','source_ids':['L1N1']}],'next_steps':[],'missing_information':[],'follow_ups':[]}
  model=Mock();model.call.side_effect=[((p,{}),'test'),((json.dumps(response),{}),'test')]
  result={'tool':'search_current_news','status':'found','checkedAt':NOW.isoformat(),'url':'','articles':[{**article(),'source':'News','scope':'neighborhood'}]}
  with patch.object(ai_news,'search',return_value=result) as search:
   answer=ai_lookups.ask_with_tools(model,store,{'question':'Find current news'},'Sunnyside')
  search.assert_called_once_with('71');self.assertEqual(answer['sources'][-1]['id'],'L1N1');self.assertEqual(answer['sources'][-1]['kind'],'Live news excerpt')
  self.assertEqual(answer['sources'][-1]['url'],article()['url'])
 def test_failed_live_check_removes_saved_news_citations(self):
  store=Mock();store.community_id='71';store.workspace.return_value={'state':{'intelligence':[{**article(),'summary':'Old saved story'}]}};store.findings.return_value=[]
  p={'status':'completed','output':[{'type':'function_call','name':'search_current_news','call_id':'n1','arguments':'{}'}]}
  model=Mock();model.call.side_effect=[((p,{}),'test'),((json.dumps({'findings':[{'text':'Saved news is current.','source_ids':['S1']}],'next_steps':[],'missing_information':[],'follow_ups':[]}),{}),'test')]
  with patch.object(ai_news,'search',return_value={'tool':'search_current_news','status':'unavailable','checkedAt':NOW.isoformat(),'url':'','articles':[]}):
   answer=ai_lookups.ask_with_tools(model,store,{'question':'Find current news'},'Sunnyside')
  self.assertEqual([s['id'] for s in answer['sources']],['L1']);self.assertEqual(answer['findings'],[]);self.assertTrue(answer['warning'])
 def test_council_page_requests_are_bounded(self):
  src={**SOURCE,'format':'council','district':'D','kind':'news'}
  def fetch(source,fetch):
   for _ in range(4):fetch('https://www.houstontx.gov/council/d/')
  with patch.object(ai_news.council_sources,'fetch_district',side_effect=fetch),patch.object(ai_news.council_sources,'download',return_value='page') as download:
   self.assertEqual(ai_news.check_source(src,'71',NOW)['status'],'failed');self.assertEqual(download.call_count,3)
