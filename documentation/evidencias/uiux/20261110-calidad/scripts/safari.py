import json,urllib.request,base64
from pathlib import Path
sid=json.load(open('.local/uiux-quality-20261110/safari-session.json'))['value']['sessionId']
root='http://127.0.0.1:15052/session/'+sid
out=Path('documentation/evidencias/uiux/20261110-calidad')
def call(path,body=None,method=None):
 req=urllib.request.Request(root+path,data=json.dumps(body).encode() if body is not None else None,method=method or ('POST' if body is not None else 'GET'),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)['value']
report={'browser':'Safari 26.6.1 macOS real','origin':'synthetic Jinja fixtures; no authenticated route','checks':[]}
try:
 for width in [1440,1024,768,390,320]:
  call('/window/rect',{'width':width,'height':1000,'x':0,'y':0})
  size=call('/execute/sync',{'script':'return {innerWidth,outerWidth,ratio:devicePixelRatio};','args':[]})
  call('/window/rect',{'width':round(width*size['outerWidth']/size['innerWidth']),'height':1000,'x':0,'y':0})
  for family in ['campaigns','alerts','documents','login','operations']:
   call('/url',{'url':f'http://127.0.0.1:15053/after/DONOR-{family}.html'})
   measurement=call('/execute/sync',{'script':'return {width:innerWidth,height:innerHeight,devicePixelRatio,outerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,rows:document.querySelectorAll("tbody>tr").length,selectHeights:[...document.querySelectorAll("main select")].map(x=>x.getBoundingClientRect().height)};','args':[]})
   report['checks'].append({'requestedWidth':width,'family':family,**measurement})
   (out/f'safari-{family}-requested-{width}.png').write_bytes(base64.b64decode(call('/screenshot')))
 report['result']='reviewed';report['note']='Ancho CSS medido, ventana ajustada a ese ancho. Safari conserva zoom previo 85 % (DPR 1.7 en pantalla Retina 2x); no se redujo para acomodar controles.'
except Exception as e:report['error']=str(e)
finally:
 (out/'safari.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
