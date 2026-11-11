"""Prepare test-only public trust and private test assets outside the repository."""
import json,sys,shutil
from pathlib import Path
lab=Path(sys.argv[1]);target=lab.parent/'android'
(target/'res/raw').mkdir(parents=True,exist_ok=True);(target/'res/xml').mkdir(exist_ok=True);(target/'assets').mkdir(exist_ok=True)
shutil.copy(lab,target/'assets/lab.json');(target/'assets/lab.json').chmod(0o600)
shutil.copy(lab.parent/'ca.pem',target/'res/raw/mobile_lab_ca.pem')
(target/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:networkSecurityConfig="@xml/mobile_lab_security" /></manifest>')
(target/'res/xml/mobile_lab_security.xml').write_text('<network-security-config><base-config cleartextTrafficPermitted="false"><trust-anchors><certificates src="system"/></trust-anchors></base-config><domain-config cleartextTrafficPermitted="false"><domain>10.0.2.2</domain><trust-anchors><certificates src="@raw/mobile_lab_ca"/></trust-anchors></domain-config></network-security-config>')
print(target)
