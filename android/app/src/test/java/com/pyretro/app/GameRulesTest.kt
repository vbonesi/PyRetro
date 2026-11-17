package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class GameRulesTest {
    private fun facts(
        code: String = "FC", key: String = "k", id: String = "i", onPhone: Boolean = false, queued: Boolean = false, linked: Boolean = false,
        downloadable: Boolean = false, pcLocal: Boolean = false, drive: Boolean = false, online: Boolean = true, driveConnected: Boolean = false,
        stream: String? = null, viaNotebook: Boolean = false,
    ) = GameFacts(key, id, code, "NES", code.isNotEmpty() && code in setOf("FC", "PS", "NDS", "3DS", "PSP"), onPhone, queued, linked, downloadable, pcLocal, drive,
        online, driveConnected, stream, viaNotebook)

    @Test fun `a acao principal segue o contexto do jogo`() {
        assertEquals(GameAction.PLAY, GameRules.primary(facts(onPhone = true))!!.first)
        assertEquals(GameAction.QUEUE, GameRules.primary(facts(queued = true, downloadable = true))!!.first)
        assertEquals(GameAction.DOWNLOAD, GameRules.primary(facts(downloadable = true))!!.first)
        assertEquals(GameAction.DOWNLOAD, GameRules.primary(facts(linked = true))!!.first)
        assertEquals("📡 Transmitir do Xbox · XBXPlay", GameRules.primary(facts(code = "", stream = GameRules.XBOX))!!.second)
        assertEquals(GameAction.STREAM, GameRules.primary(facts(code = "", stream = "com.playstation.remoteplay"))!!.first)
        assertEquals(GameAction.SWITCH, GameRules.primary(facts(code = "", viaNotebook = true))!!.first)
        assertEquals(GameAction.MOONLIGHT, GameRules.primary(facts(code = ""))!!.first)
        assertEquals(GameAction.DRIVE_SEARCH, GameRules.primary(facts())!!.first)
        assertNull(GameRules.primary(facts(code = "", key = "local:x")))
    }
    @Test fun `no celular vence a fila e o download`() {
        assertEquals(GameAction.PLAY, GameRules.primary(facts(onPhone = true, queued = true, downloadable = true))!!.first)
    }
    @Test fun `estado em texto`() {
        assertEquals("Neste celular", GameRules.state(facts(onPhone = true)))
        assertEquals("Na fila de downloads", GameRules.state(facts(queued = true)))
        assertEquals("Pronto para baixar do notebook", GameRules.state(facts(downloadable = true, pcLocal = true)))
        assertEquals("Pronto para baixar do Drive", GameRules.state(facts(downloadable = true, drive = true)))
        assertEquals("Pronto para baixar do Drive (conta Google)", GameRules.state(facts(downloadable = true, online = false, driveConnected = true)))
        assertEquals("Pronto para baixar do arquivo vinculado", GameRules.state(facts(linked = true)))
        assertEquals("Console · transmita do aparelho", GameRules.state(facts(code = "", viaNotebook = true)))
        assertEquals("Instalado no notebook", GameRules.state(facts(code = "", pcLocal = true)))
        assertEquals("Só no catálogo", GameRules.state(facts(code = "")))
    }
    @Test fun `fileira secundaria e menu mais`() {
        assertEquals(listOf(GameAction.SAVES, GameAction.EDIT), GameRules.secondary(facts()))
        assertEquals(listOf(GameAction.SAVES, GameAction.TEXTURES, GameAction.ADD_LIBRARY), GameRules.secondary(facts(code = "PS", id = "")))
        assertEquals(emptyList<GameAction>(), GameRules.more(facts(code = "")))
        assertEquals(listOf(GameAction.OTHER_ROM, GameAction.DRIVE_PICK), GameRules.more(facts()))
        assertEquals(listOf(GameAction.MOONLIGHT, GameAction.OTHER_ROM, GameAction.DRIVE_PICK, GameAction.REMOVE), GameRules.more(facts(pcLocal = true, drive = true)))
        assertFalse(GameAction.MOONLIGHT in GameRules.more(facts(code = "NDS", pcLocal = true)))
    }
    @Test fun `avisos e ids das acoes`() {
        assertEquals(1, GameRules.notes(facts(code = "", viaNotebook = true)).size)
        assertEquals(1, GameRules.notes(facts()).size)           // ROM que o notebook não tem
        assertTrue(GameRules.notes(facts(downloadable = true)).isEmpty())
        assertEquals(GameAction.TEXTURES, GameAction.of("textures")); assertNull(GameAction.of("nada"))
        assertEquals(GameAction.values().size, GameAction.values().map { it.id }.toSet().size)
        assertEquals("⏱ 1h05 no celular", GameRules.playedLabel(65)); assertEquals("⏱ 20 min no celular", GameRules.playedLabel(20)); assertNull(GameRules.playedLabel(0))
    }
}
