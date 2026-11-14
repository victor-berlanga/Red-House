"""Run read-only readiness in the real image, with separate temporary headers."""
import hashlib,json,subprocess,sys,time
sys.path.insert(0,'/tmp/redhouse-scanner20-20261113')
import deploy as release

release.target()
script=(release.INPUT/'clamav_readiness.sh').read_bytes()
assert hashlib.sha256(script).hexdigest()=='71b312e8edac0e9b374f1b60ffa9f36153a31e6bf6049ab9e929e6e4ad6e4049'
daemon=release.capture(['docker','ps','-q','--filter','name=^/redhouse-parcial2-clamav-1$'])
assert daemon and '\n' not in daemon
state=json.loads(release.capture(['docker','inspect',daemon]))[0]
assert state['HostConfig']['Memory']==2147483648
result={'script_sha256':hashlib.sha256(script).hexdigest(),'image':state['Image'],
        'daemon':daemon,'checks':[],'installed':False,'real_signature_files_modified':False}

def probe(name, expected, directory=None):
    command=['docker','exec','-i']
    if directory is not None:
        command+=['--env','CLAMAV_DATABASE_DIR='+directory]
    command+=[daemon,'sh','-s']
    started=time.monotonic()
    checked=subprocess.run(command,input=script,capture_output=True,timeout=20)
    report={'name':name,'exit':checked.returncode,'message':checked.stdout.decode().strip(),
            'stderr_empty':not checked.stderr,'seconds':time.monotonic()-started}
    result['checks'].append(report)
    release.save('readiness-image-test.json',result)
    assert (checked.returncode,report['message'])==expected and not checked.stderr

probe('real signatures',(0,'healthy: signatures current'))
header=release.capture(['docker','exec',daemon,'head','-c','512','/var/lib/clamav/daily.cld'])
parts=header.split(':')
assert len(parts)==9 and parts[0]=='ClamAV-VDB' and parts[2].isdigit()
directory=release.capture(['docker','exec',daemon,'mktemp','-d','/tmp/rh-readiness-XXXXXX'])
assert directory.startswith('/tmp/rh-readiness-') and '/' not in directory[len('/tmp/'):]
try:
    for name,field,value,expected in (
        ('old synthetic header',8,str(int(time.time())-172801),(1,'degraded: signature age')),
        ('mismatched synthetic header',2,str(int(parts[2])+1),(1,'degraded: version mismatch')),
    ):
        modified=parts.copy();modified[field]=value
        data=':'.join(modified).strip().ljust(512).encode()
        assert len(data)==512
        response=subprocess.run(['docker','exec','-i',daemon,'sh','-c','cat > "$1/daily.cld"','sh',directory],
                                input=data,capture_output=True,timeout=10)
        assert response.returncode==0
        probe(name,expected,directory)
finally:
    release.run(['docker','exec',daemon,'rm','-f',directory+'/daily.cld'])
    release.run(['docker','exec',daemon,'rmdir',directory])
    result['synthetic_directory_removed']=True
    release.save('readiness-image-test.json',result)
print(json.dumps(result))
