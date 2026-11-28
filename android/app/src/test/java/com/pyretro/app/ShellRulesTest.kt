package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class ShellRulesTest {
    private val list = listOf(LibEntry("1", "Super Mario 64", "N64", genre = "Plataforma"), LibEntry("2", "Mario Kart", "SNES", genre = "Corrida"),
        LibEntry("3", "Zelda", "NES", genre = "Aventura"), LibEntry("4", "Pokémon Ruby", "GBA", genre = "RPG"))

    @Test fun `busca ignora acento e caixa e acha por nome, plataforma ou genero`() {
        assertEquals(listOf("2", "1"), LibraryRules.search(list, "MARIO"))   // quem começa pelo termo vem antes
        assertEquals(listOf("4"), LibraryRules.search(list, "pokemon"))
        assertEquals(listOf("3"), LibraryRules.search(list, "aventura"))
        assertEquals(listOf("1"), LibraryRules.search(list, "n64"))
        val col = listOf(LibEntry("c", "Super Mario 3D All-Stars", inside = "Super Mario 64 Super Mario Sunshine"), LibEntry("m", "Mario Kart"))
        assertEquals(listOf("c"), LibraryRules.search(col, "mario 64")); assertEquals(listOf("m", "c"), LibraryRules.search(col, "kart") + LibraryRules.search(col, "sunshine"))
        assertTrue(LibraryRules.search(list, "   ").isEmpty()); assertTrue(LibraryRules.search(list, "xyz").isEmpty())
    }
    @Test fun `busca respeita o limite`() {
        val many = (1..300).map { LibEntry("k$it", "Jogo $it") }
        assertEquals(200, LibraryRules.search(many, "jogo").size); assertEquals(5, LibraryRules.search(many, "jogo", 5).size)
    }
    private fun wish(source: String, genre: String = "") = WishItem("i", source, "N", "c", genre)
    @Test fun `desejados filtram por loja`() {
        val items = listOf(wish("steam"), wish("xbox"), wish("steam"))
        assertEquals(listOf("steam", "xbox"), WishRules.stores(items))
        assertEquals(2, WishRules.filter(items, "steam").size); assertEquals(3, WishRules.filter(items, "").size)
        assertEquals("Xbox · RPG · na sua lista de desejos", WishRules.subtitle(wish("xbox", "RPG")))
        assertEquals("Steam · na sua lista de desejos", WishRules.subtitle(wish("steam")))
    }
    @Test fun `situacao em texto`() {
        val date = { t: Long -> "d$t" }
        val i = StatusInfo(readyGames = 3, catalogSize = 100, catalogAt = 7, folderProblems = listOf("PSP"), serverBlank = false, online = true, pending = 2,
            downloads = 3, failedDownloads = 1, pausedDownloads = 1, driveConnected = true, driveEmail = "a@b")
        assertEquals("3 jogo(s) prontos para jogar · 100 no catálogo (d7).\nNão foi possível ler: PSP.", SituationRules.local(i, date))
        assertEquals("Online para transmissões e manutenção do PC.", SituationRules.notebook(i))
        assertEquals("Endereço não configurado.", SituationRules.notebook(StatusInfo()))
        assertEquals("Offline. Biblioteca local, jogos do celular e acesso direto ao Drive continuam disponíveis.", SituationRules.notebook(i.copy(online = false)))
        assertEquals("Conectada: a@b. ROMs do Drive baixam direto, sem o notebook.", SituationRules.drive(i)); assertEquals("Conta Google não conectada.", SituationRules.drive(StatusInfo()))
        assertEquals("2 alteração(ões) guardada(s) neste celular para enviar pela nuvem.", SituationRules.tracking(i, date))
        assertEquals("Tudo enviado. Última sincronização: ainda não.", SituationRules.tracking(StatusInfo(), date))
        assertEquals("3 na fila · 1 com falha · 1 pausado(s).", SituationRules.downloads(i)); assertEquals("Fila vazia.", SituationRules.downloads(StatusInfo()))
        assertEquals("pronta".let { "✓ $it" }, SituationRules.folder(FolderAccess.READ_WRITE)); assertEquals("não escolhida", SituationRules.folder(FolderAccess.UNSELECTED))
    }
    @Test fun `o botao Situacao conta o que pede atencao`() {
        assertEquals("Situação", SituationRules.buttonLabel(StatusInfo()))
        assertEquals("Situação · 4", SituationRules.buttonLabel(StatusInfo(pending = 2, failedDownloads = 1, folderProblems = listOf("x"))))
    }
}
