package com.pyretro.app

/** O que a ficha precisa saber do jogo e do aparelho para escolher ações; sem Android. */
data class GameFacts(
    val key: String, val id: String, val code: String, val platform: String, val rom: Boolean,
    val onPhone: Boolean, val queued: Boolean, val linked: Boolean, val downloadable: Boolean, val pcLocal: Boolean, val drive: Boolean,
    val online: Boolean, val driveConnected: Boolean, val streamPackage: String?, val viaNotebook: Boolean,
    val duckStation: Boolean = false, val coverTarget: Boolean = false, val pinned: Boolean = false, val favorite: Boolean = false,
) {
    val waiting get() = rom && !onPhone && queued
    val canDownload get() = rom && (linked || downloadable)
}

/** Ações da ficha que a tela antiga (MainActivity) executa; o [id] viaja na intent. */
enum class GameAction(val id: String) {
    PLAY("play"), QUEUE("queue"), DOWNLOAD("download"), STREAM("stream"), SWITCH("switch"), MOONLIGHT("moonlight"), DRIVE_SEARCH("drive-search"),
    SAVES("saves"), ADD_LIBRARY("add-library"), DUCKSTATION("duckstation"), OTHER_ROM("other-rom"), DRIVE_PICK("drive-pick"),
    TEXTURES("textures"), EDIT("edit"), COVER("cover"), REMOVE("remove"), DRAW("draw");
    companion object { fun of(id: String?) = values().firstOrNull { it.id == id } }
}

object GameRules {
    const val XBOX = "com.grill.xbxplay"

    /** A próxima coisa que faz sentido para o jogo: uma só ação principal, com o texto do PC/tela antiga. */
    fun primary(f: GameFacts): Pair<GameAction, String>? = when {
        f.onPhone -> GameAction.PLAY to "▶ Jogar neste celular"
        f.waiting -> GameAction.QUEUE to "⬇ Na fila · ver downloads"
        f.canDownload -> GameAction.DOWNLOAD to "⬇ Baixar para este celular"
        f.streamPackage != null -> GameAction.STREAM to (if (f.streamPackage == XBOX) "📡 Transmitir do Xbox · XBXPlay" else "📡 Transmitir do PlayStation · Remote Play")
        f.viaNotebook -> GameAction.SWITCH to "📡 Transmitir do Switch pelo notebook"
        f.code.isEmpty() && !f.key.startsWith("local:") -> GameAction.MOONLIGHT to "🖥 Jogar no notebook · Moonlight"
        f.rom -> GameAction.DRIVE_SEARCH to "Procurar a ROM no Drive"
        else -> null
    }

    fun state(f: GameFacts): String = when {
        f.onPhone -> "Neste celular"
        f.waiting -> "Na fila de downloads"
        f.canDownload -> "Pronto para baixar" + when {
            !f.online && f.driveConnected -> " do Drive (conta Google)"
            f.pcLocal -> " do notebook"
            f.drive -> " do Drive"
            else -> " do arquivo vinculado"
        }
        f.streamPackage != null || f.viaNotebook -> "Console · transmita do aparelho"
        f.pcLocal -> "Instalado no notebook"
        else -> "Só no catálogo"
    }

    /** Frases de apoio sob a ação principal. */
    fun notes(f: GameFacts): List<String> = listOfNotNull(
        "Abrir o jogo direto não é possível: escolha-o no console depois de conectar.".takeIf { f.streamPackage != null },
        "Abra o jogo no Switch. O notebook liga o SysDVR e o Moonlight mostra a tela.".takeIf { f.viaNotebook },
        "O notebook não tem esta ROM. Escolha o arquivo no Drive uma vez; depois o download é direto.".takeIf { f.rom && !f.onPhone && !f.waiting && !f.linked && !f.downloadable },
    )

    /** Fileira secundária (visível): saves, capa, editar, texturas… O que é raro vai para [more]. */
    fun secondary(f: GameFacts): List<GameAction> = listOfNotNull(
        GameAction.SAVES.takeIf { f.rom },
        GameAction.COVER.takeIf { f.coverTarget },
        GameAction.EDIT.takeIf { f.id.isNotBlank() },
        GameAction.TEXTURES.takeIf { f.code in setOf("PS", "PSP", "3DS") },
        GameAction.ADD_LIBRARY.takeIf { f.id.isBlank() && f.rom },
    )

    /** Menu "⋯ Mais". */
    fun more(f: GameFacts): List<GameAction> = listOfNotNull(
        GameAction.MOONLIGHT.takeIf { f.rom && f.pcLocal && f.code !in setOf("NDS", "3DS") },
        GameAction.DUCKSTATION.takeIf { f.code == "PS" && f.duckStation },
        GameAction.OTHER_ROM.takeIf { f.rom },
        GameAction.DRIVE_PICK.takeIf { f.rom },
        GameAction.REMOVE.takeIf { f.onPhone || f.drive },
    )

    fun label(action: GameAction) = when (action) {
        GameAction.SAVES -> "💾 Saves"
        GameAction.COVER -> "🖼 Trocar capa"
        GameAction.EDIT -> "✎ Editar dados"
        GameAction.TEXTURES -> "Texturas HD"
        GameAction.ADD_LIBRARY -> "📚 Adicionar à Biblioteca"
        GameAction.MOONLIGHT -> "🖥 Jogar no notebook · Moonlight"
        GameAction.DUCKSTATION -> "Abrir DuckStation · escolher jogo"
        GameAction.OTHER_ROM -> "Usar outra ROM deste celular"
        GameAction.DRIVE_PICK -> "Escolher o arquivo no Drive"
        GameAction.REMOVE -> "🗑 Remover…"
        GameAction.DRAW -> "🎲 Sortear novamente"
        else -> action.id
    }

    fun playedLabel(minutes: Long) = if (minutes <= 0) null else if (minutes >= 60) "⏱ ${minutes / 60}h${"%02d".format(minutes % 60)} no celular" else "⏱ $minutes min no celular"
}
