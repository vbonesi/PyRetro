package com.pyretro.app

import org.json.JSONObject

/** Passos de download e de "jogar no notebook" sem tela, compartilhados pela casca em Compose e pela tela antiga. */
object DownloadFlow {
    /** Vincula a origem escolhida ao jogo e coloca na fila (ou reaproveita/ reinicia o item que já está lá), iniciando a fila se estiver parada. */
    fun enqueue(store: LibraryStore, game: Game) {
        val helper = DownloadQueue.get(store); val source = store.prefs.getString("cloud:${game.key}", null)
        val existing = helper.snapshot().firstOrNull { it.game.key == game.key && it.state != DownloadState.DONE }
        when {
            existing == null -> helper.enqueue(game)
            existing.state == DownloadState.RUNNING -> Unit
            existing.source == source -> if (existing.state != DownloadState.WAITING) helper.retry(game.key)
            else -> { helper.remove(game.key); helper.enqueue(game) }
        }
        if (!helper.running) helper.start()
    }
    fun linkNotebook(store: LibraryStore, game: Game, option: RomOption) {
        store.prefs.edit().putString("cloud:${game.key}", RomRef(game.code, option.file, option.etag, option.size).encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
    }
    fun linkDrive(store: LibraryStore, game: Game, ref: DriveRef) {
        store.prefs.edit().putString("cloud:${game.key}", ref.encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
    }

    /** Pede ao notebook para iniciar o jogo (o vídeo vai pelo Moonlight). Lança com mensagem para o usuário quando precisa de escolha manual. */
    fun startOnNotebook(store: LibraryStore, game: Game) {
        if (game.code.isNotEmpty()) {
            val options = JSONObject(store.request("/api/play/options?code=${android.net.Uri.encode(game.code)}&name=${android.net.Uri.encode(game.romName)}")).getJSONArray("options")
            val valid = (0 until options.length()).map { options.getJSONObject(it) }.filter { it.isNull("error") }
            require(valid.size == 1) { "Escolha o disco/formato na interface do notebook." }
            store.request("/api/play/start", JSONObject().put("code", game.code).put("name", valid[0].getString("name")))
        } else {
            require(game.id.isNotBlank()); val options = JSONObject(store.request("/api/pc/options?id=" + android.net.Uri.encode(game.id)))
            val remote = options.optJSONObject("remote")
            if (remote != null) store.request("/api/tv/apps/launch", JSONObject().put("id", remote.getJSONObject("app").getString("id")))
            else { require(options.optBoolean("available")) { "Jogo não instalado no notebook. Abra a loja pelo Moonlight para instalar." }; store.request("/api/pc/launch", JSONObject().put("id", game.id)) }
        }
    }
}
