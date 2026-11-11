from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
root=Path.cwd();base=root/'.local/uiux-quality-20261110';out=root/'documentation/evidencias/uiux/20261110-calidad'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((base/'before.json').read_text());changed=[name for name,h in before.items() if (root/name).is_file() and sha(root/name)!=h]
protected=json.loads(Path('/private/tmp/redhouse-uiux-correction/baseline.json').read_text());scopes=('apps/services/','data/database/','deployment/','apps/mobile/composeApp/src/commonMain/kotlin/org/redhouse/mobile/')
protectedchanges=[name for name,h in protected.items() if name.startswith(scopes[:3]) and (root/name).is_file() and sha(root/name)!=h]
report={'modifiedExistingPresentationFiles':changed,'protectedChangesSincePromptPreparation':protectedchanges,'mobile':{},'jvm':{'tests':0,'failures':0,'errors':0,'skipped':0}}
for name in ['App.kt','DonorScreen.kt','TransportScreen.kt']:
 rel=Path('apps/mobile/composeApp/src/commonMain/kotlin/org/redhouse/mobile')/name
 old=(base/'before'/rel).read_text();new=(root/rel).read_text()
 paths=lambda s:sorted(re.findall(r'"(/api/v1/[^"\n]*)',s))
 report['mobile'][name]={'sameLiteralApiPaths':paths(old)==paths(new)}
 if name=='TransportScreen.kt':
  start=lambda s:s.index('    LaunchedEffect(id)')
  end=lambda s:s.index('\n',s.index('    DisposableEffect(id)'))
  report['mobile'][name]['sameTopLevelEffects']=old[start(old):end(old)]==new[start(new):end(new)]
for p in (root/'apps/mobile/composeApp/build/test-results/testDebugUnitTest').glob('TEST-*.xml'):
 suite=E.parse(p).getroot()
 for k in report['jvm']:report['jvm'][k]+=int(suite.get(k,0))
apk=root/'apps/mobile/composeApp/build/outputs/apk/debug/composeApp-debug.apk';report['apkSha256']=sha(apk)
(out/'invariantes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
