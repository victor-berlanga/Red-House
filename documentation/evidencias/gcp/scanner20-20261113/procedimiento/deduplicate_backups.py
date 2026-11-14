"""Remove only this release's byte-identical copies of retained backup archives."""
import json
import shutil
from pathlib import Path
import deploy as release

release.target()
assert release.storage()['schema'] == 19
assert not (release.BACKUP / 'publication-started.json').exists()
assert release.digest(release.BACKUP / 'database.dump') == release.read('database-backup.json')['sha256']
source = release.CFG / 'backups'
duplicate = release.BACKUP / 'configuration/backups'
assert source.is_dir() and duplicate.is_dir()
assert not source.is_symlink() and not duplicate.is_symlink()
previous = release.read('preflight.json')['configuration']
names = {name: value for name, value in previous.items() if name.startswith('backups/')}
assert names
expected = {name.removeprefix('backups/') for name in names}
assert {str(p.relative_to(duplicate)) for p in duplicate.rglob('*') if p.is_file()} == expected
assert not any(p.is_symlink() for p in duplicate.rglob('*'))
total = 0
for name, checksum in names.items():
    original = release.CFG / name
    copy = release.BACKUP / 'configuration' / name
    assert original.is_file() and not original.is_symlink()
    assert release.digest(original) == release.digest(copy) == checksum
    total += copy.stat().st_size
before = shutil.disk_usage(release.ROOT).free
release.durable_record('historical-backup-references.json', {
    'original_directory': str(source), 'removed_duplicate_directory': str(duplicate),
    'sha256': names, 'bytes_in_duplicates': total,
    'scope': 'Historical archives remain at their original paths; they are not an independent copy in this release snapshot.',
    'deletion_complete': False})
# This is the new duplicate subtree created by prepare(), never the originals.
shutil.rmtree(duplicate)
assert all(release.digest(release.CFG / name) == checksum for name, checksum in names.items())
record = release.read('historical-backup-references.json')
record.update(deletion_complete=True, original_archives_preserved=True,
              free_before=before, free_after=shutil.disk_usage(release.ROOT).free)
release.durable_record('historical-backup-references.json', record)
assert release.digest(release.BACKUP / 'database.dump') == release.read('database-backup.json')['sha256']
print(json.dumps({k:record[k] for k in ('bytes_in_duplicates','original_archives_preserved','free_before','free_after')}))
