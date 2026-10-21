#!/usr/bin/env python3
"""Compila, verifica e copia o APK pessoal. Requer JDK 17 e SDK Android 35."""
import argparse
import hashlib
import os
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gradle', help='Gradle já instalado; por padrão usa o wrapper versionado')
    args = parser.parse_args()
    java = Path(os.environ.get('JAVA_HOME', '')) / 'bin/keytool'
    keytool = str(java) if java.is_file() else shutil.which('keytool')
    if not keytool or not (os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or (ROOT/'android/local.properties').exists()):
        parser.error('Configure JAVA_HOME (JDK 17) e ANDROID_HOME (SDK Android 35). Veja android/README.md.')
    keystore = ROOT / 'android/.gradle/debug.keystore'
    if not keystore.exists():
        keystore.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([keytool, '-genkeypair', '-keystore', str(keystore), '-storepass', 'android',
                        '-alias', 'androiddebugkey', '-keypass', 'android', '-keyalg', 'RSA', '-keysize', '2048',
                        '-validity', '10000', '-dname', 'CN=Android Debug,O=Android,C=US'], check=True)
        keystore.chmod(0o600)
    gradle = str(Path(args.gradle).resolve()) if args.gradle else str(ROOT/'android/gradlew')
    subprocess.run([gradle, '--no-daemon', ':app:assembleDebug', ':app:testDebugUnitTest', ':app:lintDebug'],
                   cwd=ROOT/'android', check=True)
    version = re.search(r'versionName\s*=\s*"([0-9.]+)"', (ROOT/'android/app/build.gradle.kts').read_text()).group(1)
    dest = ROOT/f'cache/artifacts/PyRetro-{version}-debug.apk'; dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',dest)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix('.apk.sha256').write_text(f'{digest}  {dest.name}\n')
    print(f'APK: {dest}\nSHA-256: {digest}')


if __name__ == '__main__':
    main()
