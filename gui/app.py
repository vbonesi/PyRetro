#!/usr/bin/env python3
"""Janela nativa do PyRetro: abre o modo TV (/tv) sem depender do Chrome.

O servidor continua sendo o serviço `pyretro-gui` (o celular também o usa); esta
janela só o inicia se não estiver no ar e mostra a interface em QtWebEngine.
"""
import argparse
import subprocess
import sys
import time
import urllib.request

URL = 'http://127.0.0.1:8000'
APP_ID = 'pyretro-tv'


def server_up():
    try:
        with urllib.request.urlopen(URL + '/tv', timeout=2):
            return True
    except OSError:
        return False


def ensure_server(timeout=30):
    if server_up():
        return True
    subprocess.run(['systemctl', '--user', 'start', 'pyretro-gui'], check=False)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server_up():
            return True
        time.sleep(0.5)
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--windowed', action='store_true', help='não abrir em tela cheia')
    parser.add_argument('--path', default='/tv', help='caminho a abrir (padrão: /tv)')
    args = parser.parse_args(argv)
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print('PyQt6 ausente: instale python-pyqt6-webengine (pacman) ou use tools/pyretro-tv.sh.',
              file=sys.stderr)
        return 3
    if not ensure_server():
        print('Servidor do PyRetro não respondeu em 30 s (systemctl --user status pyretro-gui).',
              file=sys.stderr)
        return 2
    QGuiApplication.setDesktopFileName(APP_ID)
    app = QApplication([sys.argv[0]])
    app.setApplicationName('PyRetro')
    profile = QWebEngineProfile('pyretro-tv')
    view = QWebEngineView()
    view.setPage(QWebEnginePage(profile, view))
    view.setWindowTitle('PyRetro')
    # O JS pede tela cheia (F11/Esc); sem isso o Qt a recusa silenciosamente.
    view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    view.page().fullScreenRequested.connect(lambda req: (req.accept(),
        view.showFullScreen() if req.toggleOn() else view.showNormal()))
    view.load(QUrl(URL + args.path))
    view.showNormal() if args.windowed else view.showFullScreen()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
