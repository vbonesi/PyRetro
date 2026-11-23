/* Janela nativa (QtWebEngine): o user agent traz PyRetroApp/1 (gui/app.py). Funções puras, sem DOM. */
export const isNativeApp = (ua = navigator.userAgent) => /PyRetroApp\//.test(ua);
export const fullscreenText = full => full ? "Sair da tela cheia" : "Tela cheia";
