"""Live HPW capital projects intersecting the selected official neighborhood."""
import datetime as dt
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import shape
from neighborops_server import get_boundary, request_json
from communities import profile

SOURCE = 'https://services1.arcgis.com/XpTq0H1nJ5DHgofs/arcgis/rest/services/EngageHouston/FeatureServer'
LAYERS = ['Roads', 'Storm sewer', 'Wastewater', 'Water', 'Drainage']

def read_layer(index, boundary, now):
    url = SOURCE + '/' + str(index)
    metadata = request_json(url + '?f=json', timeout=25)
    edited = (metadata.get('editingInfo') or {}).get('dataLastEditDate')
    if not edited or now.timestamp() - edited / 1000 > 90 * 86400:
        raise ValueError('Source has no update within the last 90 days')
    xmin, ymin, xmax, ymax = boundary.bounds
    parameters = dict(f='geojson', where="PROJECT_STAGE IN ('Construction','Design')",
                      outFields='*', returnGeometry='true', outSR=4326, inSR=4326,
                      geometry=f'{xmin},{ymin},{xmax},{ymax}',
                      geometryType='esriGeometryEnvelope', spatialRel='esriSpatialRelIntersects',
                      orderByFields='OBJECTID', resultRecordCount=1000)
    features = []
    for offset in range(0, 20000, 1000):
        parameters['resultOffset'] = offset
        result = request_json(url + '/query?' + urllib.parse.urlencode(parameters), timeout=30)
        if result.get('error') or result.get('type') != 'FeatureCollection':
            raise ValueError('HPW returned an invalid project response')
        batch = result.get('features', [])
        for feature in batch:
            props = feature.get('properties') or {}
            if props.get('PROJECT_STAGE') not in ('Construction', 'Design'):
                continue
            geometry = feature.get('geometry')
            if geometry and shape(geometry).intersects(boundary):
                props.update(ledgerCategory=LAYERS[index], ledgerSource=url,
                             ledgerSourceUpdated=dt.datetime.fromtimestamp(edited/1000, dt.timezone.utc).isoformat())
                features.append(feature)
        more = result.get('exceededTransferLimit') or (result.get('properties') or {}).get('exceededTransferLimit')
        if not more and len(batch) < 1000:
            return features
    raise ValueError('HPW response exceeded the supported page limit')

def lookup():
    now = dt.datetime.now(dt.timezone.utc)
    boundary = shape(get_boundary()['geometry'])
    features, checks = [], []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(read_layer, i, boundary, now) for i in range(5)]
        for index, future in enumerate(futures):
            try:
                rows = future.result()
                features.extend(rows)
                checks.append(dict(name=LAYERS[index], status='ok', count=len(rows)))
            except Exception as error:
                checks.append(dict(name=LAYERS[index], status='unavailable', message=str(error)[:220]))
    return dict(type='FeatureCollection', features=features, checks=checks,
                checkedAt=now.isoformat(), communityId=profile()['id'], source=SOURCE)
