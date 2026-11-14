"""Local-only simulations; no Docker, services or remote access."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import ModuleType

HERE = Path(__file__).resolve().parent
sys.modules['release_base'] = ModuleType('release_base')
sys.modules['release_base'].ROOT = Path('/private/tmp/test-root')
sys.modules['release_base'].CFG = Path('/private/tmp/test-cfg')
spec = importlib.util.spec_from_file_location('scanner_health_release', HERE / 'deploy.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix='rh-health-sim-') as name:
    root = Path(name)
    config = root / 'override'
    old, new = b'old-reviewed-content', b'new-reviewed-content'
    config.write_bytes(old)
    inode = config.stat().st_ino
    module.write_preserve_inode(config, new, (old, new))
    assert config.read_bytes() == new and config.stat().st_ino == inode
    config.write_bytes(new[:5])
    module.write_preserve_inode(config, old, (old, new))
    assert config.read_bytes() == old and config.stat().st_ino == inode
    config.write_bytes(b'unrecognized')
    try:
        module.write_preserve_inode(config, new, (old, new))
        raise AssertionError('unexpected config accepted')
    except AssertionError as exc:
        assert str(exc) == 'Unknown interrupted write'
    helper = root / 'helper'
    module.atomic_install(helper, b'script', 0o444)
    assert helper.read_bytes() == b'script' and helper.stat().st_mode & 0o777 == 0o444
    (root / 'helper.health-new').write_bytes(b'sc')
    module.atomic_install(helper, b'script', 0o444)
    assert helper.read_bytes() == b'script'
    (root / 'helper.health-new').write_bytes(b'alien')
    try:
        module.atomic_install(helper, b'script', 0o444)
        raise AssertionError('unexpected temp accepted')
    except AssertionError as exc:
        assert str(exc) == 'Unknown temporary file'
print('local helper simulations passed')
