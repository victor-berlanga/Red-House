"""Respaldo coordinado y ensayo de restauración en contenedores nuevos sin puertos.

Usar con el Python de apps/services/.venv. Los archivos privados permanecen en
.local/compose/backups; el informe público solo contiene conteos y hashes.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from start import START_ORDER

ROOT = Path(__file__).resolve().parents[1]
MONGO_TOOL = """
import json,os,subprocess,tempfile,sys
password=open('/run/secrets/mongo_password').read().strip()
fd,path=tempfile.mkstemp(suffix='.json')
try:
 with os.fdopen(fd,'w') as f:json.dump({'uri':'mongodb://rh_bootstrap@127.0.0.1/?authSource=admin','password':password},f)
 command=[sys.argv[1],'--config',path,'--archive','--gzip']
 if sys.argv[1]=='mongorestore':command+=['--drop','--nsInclude='+sys.argv[2]]
 result=subprocess.run(command,stderr=subprocess.PIPE)
 if result.returncode:
  diagnostic=result.stderr.decode(errors='replace').replace(password,'[REDACTED]')
  raise SystemExit('Mongo archive operation failed: '+diagnostic[-1600:])
finally:os.unlink(path)
"""
MONGO_STATE = r"""
import json,hashlib
from pymongo import MongoClient
from bson import json_util
password=open('/run/secrets/mongo_password').read().strip()
with MongoClient('mongodb://127.0.0.1',username='rh_bootstrap',password=password,authSource='admin',serverSelectionTimeoutMS=1000) as client:
 result={}
 for name in sorted(client.list_database_names()):
  if not name.startswith('rh_'):continue
  for collection in sorted(client[name].list_collection_names()):
   rows=sorted(json_util.dumps(x,sort_keys=True) for x in client[name][collection].find({}))
   result[name+'.'+collection]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
 for collection in ('system.users','system.roles'):
  rows=sorted(json_util.dumps(x,sort_keys=True) for x in client.admin[collection].find({}))
  result['admin.'+collection]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
 print(json.dumps(result))
"""


def command(args, *, data=None, output=None):
    result = subprocess.run(
        args,
        input=data,
        stdout=output or subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "Falló "
            + " ".join(args[:5])
            + "; diagnóstico privado: "
            + result.stderr.decode(errors="replace")[-800:]
        )
    return result.stdout


def sql_state(prefix):
    tables = json.loads(
        command(
            prefix
            + [
                "psql",
                "-U",
                "rh_bootstrap",
                "-d",
                "red_house",
                "-qAt",
                "-c",
                "SELECT json_agg(json_build_object('name',tablename) ORDER BY tablename) FROM pg_tables WHERE schemaname='red_house'",
            ]
        )
    )
    queries = []
    for table in tables:
        name = table["name"]
        assert name.replace("_", "").isalnum()
        queries.append(
            f"SELECT '{name}' AS name,count(*) AS rows,md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),'')) AS digest FROM red_house.{name} t"
        )
    queries.append(
        "SELECT 'web_runtime.session_revocations' AS name,count(*) AS rows,"
        "md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),'')) AS digest "
        "FROM web_runtime.session_revocations t"
    )
    query = (
        "SELECT json_agg(x ORDER BY x.name) FROM ("
        + " UNION ALL ".join(queries)
        + ") x"
    )
    return json.loads(
        command(
            prefix
            + ["psql", "-U", "rh_bootstrap", "-d", "red_house", "-qAt", "-c", query]
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "documentation/evidencias/segundo-parcial/backup-restore.json",
        help="Informe público de esta ejecución, separado de evidencias anteriores.",
    )
    parser.add_argument(
        "--leave-stopped",
        action="store_true",
        help="Mantener las aplicaciones pausadas para continuar un mantenimiento explícito.",
    )
    args = parser.parse_args()
    directory = args.directory.resolve()
    if directory.name == "runtime" or not (directory / "installation.json").exists():
        raise ValueError("Solo instalaciones Docker aisladas con marcador.")
    os.environ["REDHOUSE_COMPOSE_DIR"] = str(directory)
    os.umask(0o077)
    destination = (
        directory / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    destination.mkdir(parents=True)
    compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    running = (
        command(compose + ["ps", "--services", "--status", "running"]).decode().split()
    )
    apps = [x for x in running if x not in ("postgres", "mongodb", "redis")]
    temporary = []
    probe = "backup-proof:" + uuid4().hex
    password = (directory / "redis-password").read_text().strip()
    redis_prefix = compose + ["exec", "-T", "redis", "redis-cli", "--raw"]
    try:
        if apps:
            command(compose + ["stop", *apps])
        before = {
            "postgres": sql_state(compose + ["exec", "-T", "postgres"]),
            "mongo": json.loads(
                command(
                    compose + ["exec", "-T", "mongodb", "python3", "-c", MONGO_STATE]
                )
            ),
        }
        for filename, parameters in (
            (
                "postgres.dump",
                ["pg_dump", "-U", "rh_bootstrap", "-d", "red_house", "-Fc"],
            ),
            ("roles.sql", ["pg_dumpall", "-U", "rh_bootstrap", "--globals-only"]),
        ):
            with (destination / filename).open("wb") as stream:
                command(
                    compose + ["exec", "-T", "postgres", *parameters], output=stream
                )
        with (destination / "mongo.archive.gz").open("wb") as stream:
            command(
                compose
                + ["exec", "-T", "mongodb", "python3", "-c", MONGO_TOOL, "mongodump"],
                output=stream,
            )
        reply = command(
            redis_prefix,
            data=f"AUTH {password}\nSET {probe} restored EX 3600\nSAVE\n".encode(),
        )
        assert reply.decode().splitlines() == ["OK", "OK", "OK"]
        command(compose + ["cp", "redis:/data/dump.rdb", str(destination / "dump.rdb")])
        command(
            compose + ["cp", "redis:/data/users.acl", str(destination / "redis.acl")]
        )
        private = destination / "configuration"
        private.mkdir()
        for name in (
            "apps",
            "postgres-password",
            "mongo-password",
            "redis-password",
            "web.json",
            "state.json",
            "installation.json",
        ):
            source = directory / name
            if source.is_dir():
                shutil.copytree(source, private / name)
            else:
                shutil.copy2(source, private / name)
        for name in ("gcs.compose.yaml", "gcs-adc.json"):
            source = directory / name
            if source.exists():
                shutil.copy2(source, private / name)
        result = {
            "date": datetime.now(timezone.utc).isoformat(),
            "backup": "passed",
            "private_path": str(destination),
            "before": before,
        }
        if args.verify:
            suffix = uuid4().hex[:10]
            pg, mongo, redis = [
                "redhouse-restore-" + x + "-" + suffix for x in ("pg", "mongo", "redis")
            ]
            specs = [
                (
                    pg,
                    [
                        "--mount",
                        f"type=bind,source={private / 'postgres-password'},target=/run/password,readonly",
                        "-e",
                        "POSTGRES_USER=rh_bootstrap",
                        "-e",
                        "POSTGRES_PASSWORD_FILE=/run/password",
                        "postgres:14-bookworm",
                    ],
                ),
                (
                    mongo,
                    [
                        "--mount",
                        f"type=bind,source={private / 'mongo-password'},target=/run/secrets/mongo_password,readonly",
                        "-e",
                        "MONGO_INITDB_ROOT_USERNAME=rh_bootstrap",
                        "-e",
                        "MONGO_INITDB_ROOT_PASSWORD_FILE=/run/secrets/mongo_password",
                        "redhouse/mongodb-health:8.0",
                    ],
                ),
                (
                    redis,
                    [
                        "--mount",
                        f"type=bind,source={destination / 'dump.rdb'},target=/backup/dump.rdb,readonly",
                        "--mount",
                        f"type=bind,source={destination / 'redis.acl'},target=/backup/users.acl,readonly",
                        "--entrypoint",
                        "/bin/sh",
                        "redis:7.4-bookworm",
                        "-c",
                        "set -eu\n"
                        "cp /backup/dump.rdb /data/dump.rdb\n"
                        "cp /backup/users.acl /data/users.acl\n"
                        "chown redis:redis /data/dump.rdb /data/users.acl\n"
                        "exec /usr/local/bin/docker-entrypoint.sh redis-server "
                        '--aclfile /data/users.acl --save "" --appendonly no',
                    ],
                ),
            ]
            for name, arguments in specs:
                command(["docker", "run", "-d", "--name", name, *arguments])
                temporary.append(name)
            deadline = time.monotonic() + 45
            while True:
                try:
                    # Official images briefly expose a temporary database during
                    # initialization. Wait for the final server to own PID 1.
                    for name, process in ((pg, "postgres"), (mongo, "mongod")):
                        command(
                            [
                                "docker",
                                "exec",
                                name,
                                "sh",
                                "-c",
                                'test "$(cat /proc/1/comm)" = ' + process,
                            ]
                        )
                    command(["docker", "exec", pg, "pg_isready", "-U", "rh_bootstrap"])
                    command(["docker", "exec", mongo, "python3", "-c", MONGO_STATE])
                    break
                except RuntimeError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(1)
            roles = (
                (destination / "roles.sql")
                .read_text()
                .replace("CREATE ROLE rh_bootstrap;", "")
            )
            command(
                [
                    "docker",
                    "exec",
                    "-i",
                    pg,
                    "psql",
                    "-U",
                    "rh_bootstrap",
                    "-v",
                    "ON_ERROR_STOP=1",
                ],
                data=roles.encode(),
            )
            command(
                ["docker", "exec", pg, "createdb", "-U", "rh_bootstrap", "red_house"]
            )
            command(
                [
                    "docker",
                    "exec",
                    "-i",
                    pg,
                    "pg_restore",
                    "-U",
                    "rh_bootstrap",
                    "-d",
                    "red_house",
                    "--exit-on-error",
                ],
                data=(destination / "postgres.dump").read_bytes(),
            )
            # Restoring admin replaces credentials. Authenticate a new restore
            # process afterward, before creating application collections/indexes.
            for namespace in ("admin.*", "rh_*.*"):
                command(
                    [
                        "docker",
                        "exec",
                        "-i",
                        mongo,
                        "python3",
                        "-c",
                        MONGO_TOOL,
                        "mongorestore",
                        namespace,
                    ],
                    data=(destination / "mongo.archive.gz").read_bytes(),
                )
            after = {
                "postgres": sql_state(["docker", "exec", pg]),
                "mongo": json.loads(
                    command(["docker", "exec", mongo, "python3", "-c", MONGO_STATE])
                ),
            }
            assert before == after, (
                "Contenido restaurado diferente al respaldo coordinado"
            )
            reply = (
                command(
                    ["docker", "exec", "-i", redis, "redis-cli", "--raw"],
                    data=f"AUTH {password}\nGET {probe}\nTTL {probe}\n".encode(),
                )
                .decode()
                .splitlines()
            )
            assert reply[1] == "restored" and 0 < int(reply[2]) <= 3600
            web_permissions = json.loads(
                command(
                    [
                        "docker",
                        "exec",
                        pg,
                        "psql",
                        "-U",
                        "rh_bootstrap",
                        "-d",
                        "red_house",
                        "-qAt",
                        "-c",
                        "SELECT json_build_object('technical_table',has_table_privilege('rh_web_sessions','web_runtime.session_revocations','SELECT,INSERT,UPDATE,DELETE'),"
                        "'domain_schema',has_schema_privilege('rh_web_sessions','red_house','USAGE'))",
                    ]
                )
            )
            assert web_permissions == {"technical_table": True, "domain_schema": False}
            result.update(
                restore="passed",
                after=after,
                redis={"restored": True, "ttl": int(reply[2])},
                isolated_containers=temporary,
                web_permissions=web_permissions,
            )
    finally:
        command(redis_prefix, data=f"AUTH {password}\nDEL {probe}\n".encode())
        for name in temporary:
            command(["docker", "stop", name])
        if apps and not args.leave_stopped:
            # Keep the existing containers and their mounts, starting event sinks
            # first. Restoring all Python processes at once can starve readiness.
            groups = [["gateway"]]
            groups += [[name + "-a", name + "-b"] for name in START_ORDER]
            groups += [["web"]]
            assert set(apps) <= {name for group in groups for name in group}
            for group in groups:
                selected = [name for name in group if name in apps]
                if selected:
                    command(compose + ["start", "--wait", *selected])
    # Publish success only after cleanup and the requested application state.
    result["applications_restored"] = [] if args.leave_stopped else apps
    result["applications_left_stopped"] = apps if args.leave_stopped else []
    report = args.output
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "backup": "passed",
                "restore": result.get("restore", "not_requested"),
                "private_path": str(destination),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
