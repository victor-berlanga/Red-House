"""Continue only the private restored copy retained by the previous failed probe."""
import json
import subprocess
import time
import deploy as release

release.target()
assert release.storage()['schema'] == 19
assert (release.BACKUP / 'restore.private.log').exists()
assert not (release.BACKUP / 'rehearsal.json').exists()
assert release.digest(release.BACKUP / 'database.dump') == release.read('database-backup.json')['sha256']
database = release.REHEARSAL
assert release.sql("SELECT count(*) FROM pg_database WHERE datname='" + database + "' AND pg_get_userbyid(datdba)='rh_shared_owner';") == '1'
assert release.sql("SELECT count(*) FROM pg_roles WHERE rolcanlogin AND NOT rolsuper AND has_database_privilege(rolname,'" + database + "','CONNECT');") == '0'
assert release.sql_database('SELECT max(version) FROM red_house.schema_migration;', database) == '19'
before = release.containers()
inspect = release.INSPECT.replace("database='red_house'", "database='" + database + "'")
program = release.MIGRATE.replace("database='red_house'", "database='" + database + "'")
intent = json.loads(release.capture(release.migration_command(inspect)))
release.durable_record('rehearsal-migration-intent.json', intent)
command = release.migration_command(program)
assert command.count('-i') == 1
without_stdin = list(command)
without_stdin.remove('-i')
started = time.monotonic()
# Reproduce the original command with its input captured privately. Because
# Docker closes stdin without -i, Python fails before opening the database.
failed = subprocess.run(without_stdin, input=json.dumps(intent),text=True,capture_output=True,timeout=150)
(release.BACKUP / 'rehearsal-diagnostic.private.log').write_text(failed.stdout + failed.stderr)
assert failed.returncode != 0 and 'JSONDecodeError' in failed.stderr
assert release.sql_database('SELECT max(version) FROM red_house.schema_migration;', database) == '19'
passed = subprocess.run(command, input=json.dumps(intent),text=True,capture_output=True,timeout=150)
(release.BACKUP / 'rehearsal-directed.private.log').write_text(passed.stdout + passed.stderr)
assert passed.returncode == 0, 'Private migration failed; retain database and diagnostics'
result = json.loads(passed.stdout)
assert result['version'] == 20
assert release.sql_database('SELECT max(version) FROM red_house.schema_migration;', database) == '20'
assert release.storage()['schema'] == 19 and release.containers() == before
release.durable_record('rehearsal.json', {
    'database': database, 'restored_from_schema': 19, 'migration': result,
    'directed_seconds': time.monotonic() - started,
    'production_schema':19, 'runtime_unchanged':True,
    'prior_restore_retained':True, 'prior_failed_command_reproduced':True,
    'scope':'Private PostgreSQL restore plus directed schema migration; separate from failed first attempt and not platform recovery'})
release.sql('DROP DATABASE ' + database + ';')
release.durable_record('rehearsal-cleanup.json', {'dropped_only_private_database':database})
print(json.dumps(release.read('rehearsal.json')))
