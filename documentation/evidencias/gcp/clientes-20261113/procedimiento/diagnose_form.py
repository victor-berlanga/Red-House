import json,re
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser
import requests
OUT=Path(__file__).resolve().parent
PASSWORD=json.loads((OUT.parents[1]/'.local/password-maintenance-20261111/remote-input.json').read_text())['password']
BASE='https://34.18.186.116'
class Links(HTMLParser):
    def __init__(self): super().__init__();self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a': self.hrefs.append(dict(attrs).get('href',''))
with requests.Session() as session:
    session.headers.update({'Origin':BASE,'Referer':BASE+'/login'})
    response=session.get(BASE+'/login',timeout=20)
    token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',response.text).group(1)
    response=session.post(BASE+'/login',data={'login_email':'donor1','password':PASSWORD,'csrf_token':token},timeout=30,allow_redirects=False)
    assert response.status_code==302 and '/login' not in response.headers.get('Location','')
    try:
        page=session.get(BASE+'/donantes/donor',timeout=30)
        parser=Links();parser.feed(page.text)
        candidates=[x for x in parser.hrefs if '/mis-datos' in x]
        report={'http':page.status_code,'edit_text': 'Editar mi nombre' in page.text,'action_count':len(candidates),'action_query_present':any(urlsplit(x).query for x in candidates),'record_detail_count':sum(bool(re.fullmatch(r'/donantes/donor/[0-9a-f-]{36}',urlsplit(x).path)) for x in parser.hrefs)}
        if candidates:
            url=urlsplit(candidates[0]);assert not url.scheme and not url.netloc and re.fullmatch(r'/donantes/donor/[0-9a-f-]{36}/mis-datos',url.path)
            form=session.get(BASE+candidates[0],timeout=30,allow_redirects=False)
            report.update(form_http=form.status_code,display_name_present='name="display_name"' in form.text,csrf_present='csrf_token' in form.text)
        (OUT/'form-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    finally:
        page=session.get(BASE+'/panel',timeout=30)
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text).group(1)
        response=session.post(BASE+'/logout',data={'csrf_token':token},timeout=20,allow_redirects=False)
        assert response.status_code in (302,303)
        assert session.get(BASE+'/sesion/estado',timeout=20).status_code==401
