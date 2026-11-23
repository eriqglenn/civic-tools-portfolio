"""Fresh, read-only public news checks. Never reads saved findings or writes a workspace."""
import datetime as dt
import re
from concurrent.futures import ThreadPoolExecutor
import collectors
import council_sources
from community_sources import parse_notices
from communities import selected,profile
from news_dedup import unique_news

def check_source(source,community_id,now):
    with selected(community_id):
        try:
            if source.get('format')=='council':
                calls=0
                def bounded(url):
                    nonlocal calls
                    calls+=1
                    if calls>3:raise ValueError('Quick search page limit reached; more entries may exist.')
                    return council_sources.download(url)
                raw=council_sources.fetch_district(source,fetch=bounded)
                result=council_sources.parse_district(raw,source,now=now,days=30)
            else:
                raw=collectors.fetch_feed(source)
                parser=parse_notices if source.get('format')=='html' else collectors.parse_feed
                result=parser(raw,source,now=now,days=30)
            articles=[]
            unrelated=0
            if result.get('status') in ('success','partial'):
                for row in result.get('results',[]):
                    # City press feeds contain incidents across Houston. Keep local incidents
                    # only when the source text actually names this selected community.
                    from news_policy import classify
                    if source['scope']=='citywide' and not row.get('matchedTerms') and (classify(row.get('title',''),row.get('summary',''))=='crime' or re.search(r'\binvestigation\b|\bfatal (crash|collision)\b',row.get('title',''),re.I)):
                        unrelated+=1;continue
                    date=str(row.get('publishedAt') or '')
                    try:day=dt.date.fromisoformat(date[:10] if len(date)>=10 else date+'-01')
                    except ValueError:continue
                    if not 0<=(now.date()-day).days<=30:continue
                    from ledger_ai import safe_url,text
                    url=safe_url(row.get('url'))
                    if not url:continue
                    articles.append({'title':text(row.get('title'),240),'summary':text(row.get('summary'),600),
                        'url':url,'publishedAt':date,'source':source['name'],'scope':source['scope'],
                        'publicationPrecision':row.get('publicationPrecision','day')})
            warnings=[str(w)[:250] for w in result.get('warnings',[])[:2]]
            if unrelated:warnings.append(f'{unrelated} City incident reports without a selected-neighborhood match were excluded.')
            return {'name':source['name'],'url':source['url'],'status':result.get('status','failed'),
                    'count':len(articles),'warnings':warnings,'articles':articles}
        except Exception:
            return {'name':source['name'],'url':source['url'],'status':'failed','count':0,
                    'warnings':['Could not retrieve this live source. No saved results substituted.'],'articles':[]}

def search(community_id):
    now=dt.datetime.now(dt.timezone.utc)
    with selected(community_id):
        community=profile()
        sources=[s for s in collectors.sources_for_community() if s.get('format') not in ('ical','classes') and s.get('kind')!='calendar']
    with ThreadPoolExecutor(max_workers=6) as pool:
        checks=list(pool.map(lambda source:check_source(source,community_id,now),sources))
    articles=unique_news([row for check in checks for row in check.pop('articles')])
    articles.sort(key=lambda r:(r['scope']=='neighborhood',r['scope']=='districtwide',r['publishedAt']),reverse=True)
    incomplete=any(c['status']!='success' for c in checks)
    available=any(c['status'] in ('success','partial','stale','not_posted') for c in checks)
    return {'tool':'search_current_news','status':('partial' if incomplete else 'found') if articles else ('not_found' if available else 'unavailable'),
        'communityId':str(community_id),'communityName':community['name'],'checkedAt':now.isoformat(),'url':'',
        'windowDays':30,'articleCount':len(articles),'shownCount':min(12,len(articles)),'articles':articles[:12],'checks':checks,
        'message':f"Checked live news sources for {community['name']}. {len(articles)} grouped stories from the last 30 days; showing up to 12 with neighborhood coverage first, newest within each scope. "
        +('Some sources could not provide current results. ' if incomplete else '')
        +'Citywide and districtwide items are labeled. Feed coverage is incomplete; article bodies were not read. No saved results were substituted.'}
