"""Revise only the reviewed scanner generator in the unpublished payload."""
import hashlib
import json
import shutil
import tarfile
import deploy as release

release.target()
assert release.storage()['schema']==19
assert not (release.BACKUP/'publication-started.json').exists()
assert not (release.BACKUP/'gate-state.json').exists()
name='deployment/gcp/configure_scanner.py'
before=release.read('manifest.json')
after=json.loads((release.INPUT/'manifest.json').read_text())
assert set(before)==set(after)
assert {key for key in before if before[key]!=after[key]}=={name}
assert release.digest(release.ROOT/name)==release.read('preflight.json')['source_hashes'][name]
for build in release.read('builds.json').values():
    assert all(after[key]==value for key,value in build['files'].items())
with tarfile.open(release.INPUT/'payload.tar.gz') as archive:
    members=archive.getmembers()
    assert len(members)==len(after) and {m.name for m in members}==set(after)
    for member in members:
        assert member.isfile()
        content=archive.extractfile(member).read()
        assert hashlib.sha256(content).hexdigest()==after[member.name]
        if member.name==name:
            generator=content
compile(generator,name,'exec')
prior=release.BACKUP/'payload-before-freshclam'
prior.mkdir(mode=0o700)
for filename in ('manifest.json','source.json'):
    shutil.copy2(release.BACKUP/filename,prior/filename)
shutil.copy2(release.BACKUP/'payload'/name,prior/'configure_scanner.py')
(release.BACKUP/'payload'/name).write_bytes(generator)
for filename in ('manifest.json','source.json'):
    shutil.copy2(release.INPUT/filename,release.BACKUP/filename)
release.save('host-payload-update.json',{'only_changed_file':name,'before_sha256':before[name],
    'after_sha256':after[name],'images_unchanged':True,'migration_unchanged':True,
    'live_configuration_unchanged':True})
print(json.dumps(release.read('host-payload-update.json')))
