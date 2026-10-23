"""Inventory public fixture paths and licenses without accessing proprietary code."""
import concurrent.futures
import json
from pathlib import Path
import urllib.request

TARGETS=[('DynamoDS/DynamoRevit','Revit2024'),('specklesystems/speckle-sharp','main'),('mcneel/rhino.inside-revit','1.x'),('jeremytammik/DirectShapeFromFace','master'),('specklesystems/Regression-Testing','main'),('specklesystems/speckle-sharp-connectors','dev'),('specklesystems/xUnitRevit','master'),('ricaun-io/ricaun.Revit.FileInfo','master'),('Pa1best/direct-shape-framework','main')]

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'rvt-cleanroom-fixture-research'})
    return urllib.request.urlopen(req).read()

def scan(target):
    repo,ref=target;base='https://api.github.com/repos/'+repo
    try:
        commit=json.loads(get(base+'/commits/'+ref))['sha']
        tree=json.loads(get(base+'/git/trees/'+commit+'?recursive=1'))
        fixtures=[x for x in tree['tree'] if x['path'].lower().endswith(('.rvt','.rfa','.rte'))]
        licenses=[x['path'] for x in tree['tree'] if x['path'].rsplit('/',1)[-1].lower() in ('license','license.txt','license.md','copying','notice','notice.txt')]
        return {'repository':repo,'ref':ref,'commit':commit,'tree_truncated':tree.get('truncated'),
                'fixtures':fixtures,'license_paths':licenses}
    except Exception as e:return {'repository':repo,'ref':ref,'error':str(e)}

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(scan,TARGETS))
    print(json.dumps({'repositories':results},indent=2))
