"""Generate an optical QR poster from the disposable lab's opaque resource ID only."""
import json
import os
import subprocess
import sys
from pathlib import Path

lab=json.loads(Path(sys.argv[1]).read_text())
cache=Path(os.environ.get("GRADLE_USER_HOME",str(Path.home()/".gradle")))
jars=list((cache/"caches/modules-2/files-2.1/com.google.zxing/core/3.4.1").glob("*/*.jar"))
if len(jars)!=1:
    raise SystemExit("Build Android first with its pinned ZXing dependency and set GRADLE_USER_HOME.")
java=Path(os.environ["JAVA_HOME"])/"bin/java" if "JAVA_HOME" in os.environ else "java"
subprocess.run([str(java),"-cp",str(jars[0]),str(Path(__file__).with_name("QRPoster.java")),lab["resource_id"],sys.argv[2]],check=True)
print("Synthetic QR poster generated. No lab credentials were copied.")
