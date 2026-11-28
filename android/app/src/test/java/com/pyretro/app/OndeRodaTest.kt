package com.pyretro.app

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class OndeRodaTest {
    private val tracking = JSONObject("""{"onde_roda":{"xbox":{"existe":true,"gb":60.0},"switch":{"existe":true,"gb":6},"ps4":{"existe":false},"switch2":{"existe":null}},
        "jogar":{"estado":"tenho","plataforma":"xbox","loja":null}}""")

    @Test fun `selos na ordem do modo TV com marca de posse`() {
        assertEquals(listOf("Switch", "✓ Xbox"), OndeRoda.selos(tracking))
        assertEquals("Switch ~6 GB · Xbox ~60 GB", OndeRoda.detalhe(tracking))
    }
    @Test fun `quero jogar sem plataforma e card sem dados`() {
        assertEquals(listOf("♡ Quero jogar"), OndeRoda.selos(JSONObject("""{"jogar":{"estado":"quero"}}""")))
        assertEquals(emptyList<String>(), OndeRoda.selos(JSONObject()))
    }
    @Test fun `so o retro baixa`() {
        assertTrue(listOf("FC", "SFC", "MD", "SMS", "GG", "GB", "GBC", "GBA", "N64", "PCE", "PCECD", "ARCADE").all(OndeRoda::retro))
        assertFalse(listOf("PS", "PSP", "NDS", "3DS", "NGC", "WII", "NSW", "").any(OndeRoda::retro))
    }
    @Test fun `grupos do Sortear`() {
        val g = OndeRoda.Grupo.values().associateBy { it.name }
        assertTrue(OndeRoda.noGrupo(g.getValue("RETRO"), "SFC", JSONObject()))
        assertFalse(OndeRoda.noGrupo(g.getValue("RETRO"), "PS", JSONObject()))
        val quero = JSONObject("""{"onde_roda":{"ps4":{"existe":true}},"jogar":{"estado":"quero"}}""")
        assertTrue(OndeRoda.noGrupo(g.getValue("QUERO"), "", quero)); assertFalse(OndeRoda.noGrupo(g.getValue("TENHO"), "", quero))
        assertTrue(OndeRoda.noGrupo(g.getValue("TENHO"), "", JSONObject("""{"jogar":{"estado":"tenho","plataforma":"pc"}}""")))
        assertFalse(OndeRoda.noGrupo(g.getValue("QUERO"), "", JSONObject("""{"onde_roda":{"xbox":{"existe":true}},"jogar":{"estado":"quero"}}""")))
    }
}
