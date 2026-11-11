import subprocess as S,json,time,shlex,threading,base64,hmac,hashlib,struct,os
from pathlib import Path
adb='/tmp/redhouse-sdk/platform-tools/adb';out=Path('documentation/evidencias/uiux/20261110-calidad')
seed=json.loads(Path('.local/compose/state.json').read_text());demo=json.loads(Path('.local/video-gcp-20261104/demo-input.json').read_text())
report={'method':'Compose instrumented UI on API 30; host window capture; device size and font recorded below; real existing GCP demo accounts; no business writes','profiles':[]}
report['size']=S.check_output([adb,'shell','wm','size'],text=True).strip()
report['fontScale']=S.check_output([adb,'shell','settings','get','system','font_scale'],text=True).strip()
def save():(out/os.environ.get('REDHOUSE_REPORT','android-final.json')).write_text(json.dumps(report,indent=2))
for user,first in [('donor1','Citas'),('transport1','Traslados'),('operator1','Inventario'),('coordinator1','Traslados'),('medical1','Solicitudes')]:
 if os.environ.get('REDHOUSE_VISUAL_USER') and user!=os.environ['REDHOUSE_VISUAL_USER']:continue
 S.run([adb,'shell','am','force-stop','org.redhouse.mobile'],stdout=S.DEVNULL)
 secret=demo['password'] if user in ['coordinator1','medical1'] else seed['password']
 otp=None
 if user in ['coordinator1','medical1']:
  mfa=demo['accounts']['coordinator' if user=='coordinator1' else 'origin']['secret']
  if time.time()%30>15:time.sleep(31-time.time()%30)
  digest=hmac.new(base64.b32decode(mfa+'='*((-len(mfa))%8)),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
  otp=str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
 record={'user':user,'first':first,'status':'running','captures':[]};report['profiles'].append(record);save()
 logger=S.Popen([adb,'logcat','-T','1','-v','brief','-s','VisualQuality:I','*:S'],stdout=S.PIPE,stderr=S.DEVNULL,text=True)
 def watch():
  started=False
  for line in logger.stdout:
   stage=line.strip().split(':')[-1].strip()
   if stage in ['work','login-or-query-error','baseline-account','baseline-work','task','contacts','appointments','booking-form','subhub','secondary-list']:started=True
   if not started:continue
   if stage in ['work','account','privacy','notices','login-or-query-error','baseline-account','baseline-work','task','contacts','appointments','booking-form','subhub','secondary-list']:
    S.run(['osascript','-e','tell application "System Events" to tell process "qemu-system-x86_64" to set frontmost to true','-e','tell application "System Events" to tell process "qemu-system-x86_64" to perform action "AXRaise" of window 2'],stdout=S.DEVNULL,stderr=S.DEVNULL)
    time.sleep(.5);name=f'{user}-{stage}-'+os.environ.get('REDHOUSE_VISUAL_SIZE','360-130')+'.png'
    S.run(['/usr/sbin/screencapture','-x','-R100,30,360,748',str(out/name)],stdout=S.DEVNULL,stderr=S.DEVNULL)
    record['captures'].append(name);save()
 thread=threading.Thread(target=watch,daemon=True);thread.start()
 args=['am','instrument','-w','-r','-e','class','org.redhouse.mobile.'+os.environ.get('REDHOUSE_TEST_CLASS','VisualProfileTest'),'-e','demoUser',user,'-e','demoPassword',secret,'-e','firstDestination',first]
 if os.environ.get('REDHOUSE_TEST_CLASS')=='BaselineVisualTest':args+=['-e','baseline','true']
 if otp:args+=['-e','demoOtp',otp]
 args+=['org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner']
 try:
  result=S.run([adb,'shell',shlex.join(args)],capture_output=True,text=True,timeout=180)
  log=result.stdout+result.stderr
  log=log.replace(secret,'[OCULTO]')
  if otp:log=log.replace(otp,'[OCULTO]')
  (out/(user+'-'+os.environ.get('REDHOUSE_TEST_CLASS','VisualProfileTest')+'-'+os.environ.get('REDHOUSE_VISUAL_SIZE','360-130')+'-instrumentation.txt')).write_text(log)
  record['status']='passed' if 'OK (1 test)' in log else 'failed'
 except S.TimeoutExpired:record['status']='timeout'
 finally:logger.terminate();thread.join(timeout=5);save()

