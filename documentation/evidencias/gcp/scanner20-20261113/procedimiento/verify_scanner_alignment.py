"""Check loaded signatures against disk; explicit bounded reload, no file scans."""
import json
import re
import sys
import time
import deploy as release


def daemon_command(runtime, command):
    assert command in ('VERSION', 'RELOAD')
    program = '''
import json,socket,sys
with socket.create_connection(('clamav',3310),timeout=5) as client:
 client.settimeout(10);client.sendall(('z'+sys.argv[1]+'\\0').encode());result=b''
 while b'\\0' not in result and len(result)<4096:
  part=client.recv(1024)
  if not part:break
  result+=part
 assert result.endswith(b'\\0')
 print(json.dumps(result[:-1].decode('ascii')))
'''
    return json.loads(release.capture(['docker','exec',runtime['documentos-a']['id'],
                                      'python','-c',program,command]))


def disk_header(runtime):
    # Read only the 512-byte CVD/CLD header, not the complete signature database.
    script = '''
set -eu
if [ -f /var/lib/clamav/daily.cld ] && [ ! -f /var/lib/clamav/daily.cvd ]; then
 head -c 512 /var/lib/clamav/daily.cld
elif [ -f /var/lib/clamav/daily.cvd ] && [ ! -f /var/lib/clamav/daily.cld ]; then
 head -c 512 /var/lib/clamav/daily.cvd
else
 exit 2
fi
'''
    value = release.capture(['docker','exec',runtime['clamav']['id'],'sh','-c',script])
    parts = value.split(':')
    assert parts[0] == 'ClamAV-VDB' and len(parts) >= 4 and parts[2].isdigit()
    return {'version':int(parts[2]),'header':value}


def observation(runtime):
    before = disk_header(runtime)
    version = daemon_command(runtime,'VERSION')
    after = disk_header(runtime)
    match = re.fullmatch(r'ClamAV ([^/]+)/([0-9]+)/(.+)',version)
    assert match, 'Malformed daemon version'
    stable = before == after
    return {'loaded':int(match.group(2)), 'disk':after['version'],
            'stable_disk':stable,'aligned':stable and int(match.group(2))==after['version'],
            'version':version}


def verify(allow_reload=False, record_name='scanner-alignment.json'):
    assert record_name in ('scanner-alignment.json','scanner-alignment-final.json')
    release.target()
    release.check_gate()
    runtime = release.containers()
    daemon = json.loads(release.capture(['docker','inspect',runtime['clamav']['id']]))[0]
    env = dict(v.split('=',1) for v in daemon['Config']['Env'])
    assert env['TZ']=='UTC' and env['FRESHCLAM_CHECKS']=='12'
    assert env['CLAMD_CONF_ConcurrentDatabaseReload']=='no'
    configuration = release.capture(['docker','exec',runtime['clamav']['id'],'cat','/etc/clamav/clamd.conf'])
    assert re.findall(r'^ConcurrentDatabaseReload\s+(\S+)\s*$',configuration,re.M)==['no']
    first = observation(runtime)
    report = {'before':first,'reload_requested':False,'attempts':[],'result':'pending',
              'memory_limit':daemon['HostConfig']['Memory'],'scanned_files':0}
    release.save(record_name,report)
    if not first['aligned']:
        assert allow_reload, 'Loaded signatures differ from stable disk database'
        answer = daemon_command(runtime,'RELOAD')
        assert answer == 'RELOADING', 'Reload was not acknowledged'
        report['reload_requested']=True
        release.save(record_name,report)
    deadline = time.monotonic()+180
    while True:
        try:
            current = observation(runtime)
        except Exception as exc:
            current = {'aligned':False,'error_type':type(exc).__name__}
        report['attempts'].append(current)
        release.save(record_name,report)
        if current['aligned']:
            time.sleep(1)
            confirmation = observation(runtime)
            if confirmation['aligned'] and confirmation['version']==current['version']:
                report['after']=confirmation
                report['result']='passed'
                release.check_gate()
                release.save(record_name,report)
                print(json.dumps(report))
                return report
        assert time.monotonic()<deadline, 'Signatures did not converge before deadline'
        time.sleep(5)


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('check','reload-if-needed')
    verify(sys.argv[1]=='reload-if-needed')
