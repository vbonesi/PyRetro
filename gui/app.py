#!/usr/bin/env python3
"""Janela nativa do PyRetro: abre o modo TV (/tv) sem depender do Chrome.

O servidor continua sendo o serviço `pyretro-gui` (o celular também o usa); esta
janela só o inicia se não estiver no ar e mostra a interface em QtWebEngine.
"""
import argparse
import fcntl
import os
import subprocess
import sys
import time
import urllib.request

URL = 'http://127.0.0.1:8000'
APP_ID = 'pyretro-tv'
RAISE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools/raise-window.sh')


def single_instance():
    """Trava por sessão: o botão Guide pode chamar o app de novo; a segunda chamada só traz a janela."""
    path = os.path.join(os.environ.get('XDG_RUNTIME_DIR', '/tmp'), 'pyretro-tv.lock')
    handle = open(path, 'w')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return None
    return handle


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


APP_MARKER = 'PyRetroApp/1'


def toggle_fullscreen(view):
    """Alterna a própria janela entre tela cheia e maximizada com moldura."""
    view.showMaximized() if view.isFullScreen() else view.showFullScreen()


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
    lock = single_instance()
    if lock is None:
        if os.environ.get('DBUS_SESSION_BUS_ADDRESS') and os.path.isfile(RAISE):
            subprocess.run([RAISE, APP_ID, '3'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    if not ensure_server():
        print('Servidor do PyRetro não respondeu em 30 s (systemctl --user status pyretro-gui).',
              file=sys.stderr)
        return 2
    QGuiApplication.setDesktopFileName(APP_ID)
    app = QApplication([sys.argv[0]])
    app.setApplicationName('PyRetro')
    profile = QWebEngineProfile('pyretro-tv')
    # Marcador para a página saber que está na janela nativa (botões Tela cheia e Fechar).
    profile.setHttpUserAgent(profile.httpUserAgent() + ' ' + APP_MARKER)
    view = QWebEngineView()

    def push_state():
        view.page().runJavaScript(
            'window.pyretroFullscreen && window.pyretroFullscreen(%s)' % ('true' if view.isFullScreen() else 'false'))

    class BridgePage(QWebEnginePage):
        # A página fala com o Qt navegando para pyretro-app://…; a navegação é recusada e vira ação.
        def acceptNavigationRequest(self, url, nav_type, is_main_frame):
            if url.scheme() == 'pyretro-app':
                acao = url.host()
                if acao == 'fullscreen':
                    toggle_fullscreen(view)
                    push_state()
                elif acao == 'quit':
                    QApplication.quit()
                return False
            return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    view.setPage(BridgePage(profile, view))
    view.setWindowTitle('PyRetro')
    # O JS pede tela cheia (F11/Esc); sem isso o Qt a recusa silenciosamente.
    view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    # Pedidos de tela cheia do próprio conteúdo (vídeo) só são aceitos; a janela é alternada pela ponte.
    view.page().fullScreenRequested.connect(lambda req: req.accept())
    view.page().loadFinished.connect(lambda ok: push_state())
    view.load(QUrl(URL + args.path))
    view.showNormal() if args.windowed else view.showFullScreen()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
