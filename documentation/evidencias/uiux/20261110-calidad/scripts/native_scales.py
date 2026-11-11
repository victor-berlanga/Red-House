import subprocess as S,json,time,threading,shlex,os
from pathlib import Path
adb='/tmp/redhouse-sdk/platform-tools/adb';out=Path('documentation/evidencias/uiux/20261110-calidad');report={'environment':'temporary API 30 emulator; no credentials or authentication requests','checks':[]}
def run(*args):return S.check_output([adb,*args],stderr=S.STDOUT,text=True,timeout=30).strip()
report['original']={'size':run('shell','wm','size'),'fontScale':run('shell','settings','get','system','font_scale'),'accelerometerRotation':run('shell','settings','get','system','accelerometer_rotation'),'userRotation':run('shell','settings','get','system','user_rotation')}
def save():(out/os.environ.get('REDHOUSE_SCALE_REPORT','android-scales.json')).write_text(json.dumps(report,indent=2))
try:
 for width in [int(x) for x in os.environ.get('REDHOUSE_WIDTHS','360,412').split(',')]:
  for font in [float(x) for x in os.environ.get('REDHOUSE_FONTS','1.0,1.3,2.0').split(',')]:
   run('shell','am','force-stop','org.redhouse.mobile');run('shell','wm','size',f'{width}x{width*2}');run('shell','settings','put','system','font_scale',str(font))
   record={'widthDp':width,'fontScale':font,'captures':[]};report['checks'].append(record);save()
   logger=S.Popen([adb,'logcat','-T','1','-v','brief','-s','VisualQuality:I','*:S'],stdout=S.PIPE,stderr=S.DEVNULL,text=True)
   def watch():
    for line in logger.stdout:
     stage=line.strip().split(':')[-1].strip()
     if stage not in ['access','keyboard','landscape']:continue
     S.run(['osascript','-e','tell application "System Events" to tell process "qemu-system-x86_64" to set frontmost to true','-e','tell application "System Events" to tell process "qemu-system-x86_64" to perform action "AXRaise" of window 2'],stdout=S.DEVNULL,stderr=S.DEVNULL)
     time.sleep(.7);name=f'android-{stage}-{width}-{int(font*100)}.png'
     S.run(['/usr/sbin/screencapture','-x','-R100,30,360,748',str(out/name)],stdout=S.DEVNULL,stderr=S.DEVNULL);record['captures'].append(name);save()
   thread=threading.Thread(target=watch,daemon=True);thread.start()
   try:
    result=S.run([adb,'shell','am','instrument','-w','-r','-e','class','org.redhouse.mobile.VisualScaleTest','org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner'],capture_output=True,text=True,timeout=140)
    log=result.stdout+result.stderr;(out/f'scale-{width}-{int(font*100)}.txt').write_text(log);record['status']='passed' if 'OK (1 test)' in log else 'failed'
   except S.TimeoutExpired:
    record['status']='timeout';record['timeoutSeconds']=140
    (out/f'scale-{width}-{int(font*100)}.txt').write_text('HOST TIMEOUT after 140 seconds; no final instrumentation result.\n')
   finally:logger.terminate();thread.join(timeout=5);save()
finally:
 original=report['original']['size'];override=original.split('Override size:')[-1].strip() if 'Override size:' in original else 'reset'
 run('shell','wm','size',override);run('shell','settings','put','system','font_scale',report['original']['fontScale'])
 for key,setting in [('accelerometerRotation','accelerometer_rotation'),('userRotation','user_rotation')]:
  value=report['original'][key]
  run('shell','settings','delete','system',setting) if value=='null' else run('shell','settings','put','system',setting,value)
 save()
