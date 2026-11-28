package com.pyretro.app

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class EdicoesTest {
    private val colecao = JSONObject("""{"tipo_card":"colecao","ids_antigos":["old1","old2"],"edicoes":[
        {"id":"old1","nome":"Castlevania: Rondo of Blood","plataforma":"PC Engine CD","tipo":"item","rom":"rom:PCECD","progresso":{"finalizado":true,"nota":8.5}},
        {"id":null,"nome":"Castlevania: Symphony of the Night","plataforma":"PS1","tipo":"item","rom":null,"progresso":{}},
        {"id":"old2","nome":"Dracula X","plataforma":"PS4","tipo":"item","rom":"rom:PS","progresso":{"iniciado":true}}]}""")
    private val versao = JSONObject("""{"tipo_card":"versao","edicoes":[{"id":null,"nome":"Remaster","plataforma":"PS4","tipo":"atual","rom":null,"progresso":{}},
        {"id":"v","nome":"Original","plataforma":"PS2","tipo":"edicao","rom":"rom:PS2","progresso":{"platinado":true}}]}""")

    @Test fun `lista as entradas com plataforma e progresso`() {
        val l = Edicoes.lista(colecao)
        assertEquals(3, l.size)
        assertEquals("finalizado · nota 8,5", l[0].progresso); assertEquals("", l[1].progresso); assertEquals("iniciado", l[2].progresso)
        assertEquals("PC Engine CD", l[0].plataforma); assertNull(l[1].rom)
        assertEquals("platinado", Edicoes.lista(versao)[1].progresso)
    }
    @Test fun `colecao com ROM retro baixa pelo sistema retro`() {
        assertEquals("PCECD", Edicoes.codigoRetro(colecao))
        assertNull(Edicoes.codigoRetro(versao))                 // versão não vira retrô
        assertNull(Edicoes.codigoRetro(JSONObject("""{"tipo_card":"colecao","edicoes":[{"nome":"x","rom":"rom:PS"}]}""")))
        assertTrue(OndeRoda.noGrupo(OndeRoda.Grupo.RETRO, Edicoes.codigoRetro(colecao).orEmpty(), colecao))
    }
    @Test fun `ids antigos viram alias de chave`() {
        val g = Game("novo", "pc:novo", "Coleção", "PS4", tracking = colecao)
        assertEquals(mapOf("pc:old1" to "pc:novo", "pc:old2" to "pc:novo"), Edicoes.aliases(listOf(g, Game("", "x", "Sem id", "PS"))))
    }
}
