package com.pyretro.app

/** Desejados: filtro por loja (Todos + as lojas que existem na lista). */
object WishRules {
    fun stores(items: List<WishItem>) = ExtrasRules.STORES.keys.filter { s -> items.any { it.source == s } }
    fun filter(items: List<WishItem>, source: String) = if (source.isBlank()) items else items.filter { it.source == source }
    fun subtitle(item: WishItem) = (listOf(ExtrasRules.STORES.getValue(item.source), item.genre).filter { it.isNotBlank() }.joinToString(" · ")) + " · na sua lista de desejos"
}

/** Tudo o que a tela Situação e opções mostra, já lido (fora da thread principal). */
data class StatusInfo(
    val readyGames: Int = 0, val catalogSize: Int = 0, val catalogAt: Long = 0, val folderProblems: List<String> = emptyList(),
    val serverBlank: Boolean = true, val online: Boolean = false, val driveConnected: Boolean = false, val driveEmail: String = "",
    val rootFolder: FolderAccess = FolderAccess.UNSELECTED, val retroarchFolder: FolderAccess = FolderAccess.UNSELECTED,
    val pending: Int = 0, val lastSyncAt: Long = 0, val downloads: Int = 0, val failedDownloads: Int = 0, val pausedDownloads: Int = 0,
    val version: String = "",
)

object SituationRules {
    fun attention(i: StatusInfo) = GridRules.attention(i.pending, i.failedDownloads, i.folderProblems.size, 0)
    fun buttonLabel(i: StatusInfo) = GridRules.statusLabel(attention(i))

    fun notebook(i: StatusInfo) = when {
        i.serverBlank -> "Endereço não configurado."
        i.online -> "Online para transmissões e manutenção do PC."
        else -> "Offline. Biblioteca local, jogos do celular e acesso direto ao Drive continuam disponíveis."
    }
    fun drive(i: StatusInfo) = if (i.driveConnected) "Conectada: ${i.driveEmail.ifBlank { "conta Google" }}. ROMs do Drive baixam direto, sem o notebook." else "Conta Google não conectada."
    fun folder(access: FolderAccess) = when (access) {
        FolderAccess.READ_WRITE -> "✓ pronta"; FolderAccess.READ_ONLY -> "somente leitura"; FolderAccess.RESELECT -> "permissão expirada"; FolderAccess.UNSELECTED -> "não escolhida"
    }
    fun local(i: StatusInfo, date: (Long) -> String) = "${i.readyGames} jogo(s) prontos para jogar · ${i.catalogSize} no catálogo (${if (i.catalogAt > 0) date(i.catalogAt) else "ainda não"})." +
        if (i.folderProblems.isEmpty()) "" else "\nNão foi possível ler: ${i.folderProblems.joinToString()}."
    fun tracking(i: StatusInfo, date: (Long) -> String) =
        if (i.pending == 0) "Tudo enviado. Última sincronização: ${if (i.lastSyncAt > 0) date(i.lastSyncAt) else "ainda não"}." else "${i.pending} alteração(ões) guardada(s) neste celular para enviar pela nuvem."
    fun downloads(i: StatusInfo) = if (i.downloads == 0) "Fila vazia." else "${i.downloads} na fila · ${i.failedDownloads} com falha · ${i.pausedDownloads} pausado(s)."
}

/** Clientes de transmissão que o Início oferece (antes a aba Stream). */
data class StreamClient(val label: String, val pkg: String)
object StreamRules {
    val clients = listOf(StreamClient("Xbox · XBXPlay", "com.grill.xbxplay"), StreamClient("PS4 · Remote Play", "com.playstation.remoteplay"), StreamClient("PC e Switch · Moonlight", "com.limelight"))
}
