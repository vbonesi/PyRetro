package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class PlaySessionTest {
    private class MemoryStore : SessionStore {
        val data = mutableMapOf<String, Any?>()
        override fun getString(key: String) = data[key] as? String
        override fun getLong(key: String) = data[key] as? Long ?: 0L
        override fun getBoolean(key: String) = data[key] as? Boolean ?: false
        override fun put(values: Map<String, Any?>) { values.forEach { (k, v) -> if (v == null) data.remove(k) else data[k] = v } }
    }
    private val min = 60_000L

    @Test fun `o tempo vai do inicio a volta, em minutos inteiros`() {
        val s = MemoryStore(); PlaySession.begin(s, "jogo", 1_000)
        PlaySession.markLeft(s)
        val ended = PlaySession.end(s, 1_000 + 45 * min + 59_000)!!
        assertEquals("jogo", ended.key); assertEquals(45, ended.minutes); assertTrue(ended.worthOffering)
    }
    @Test fun `menos de um minuto nao vira registro`() {
        val s = MemoryStore(); PlaySession.begin(s, "k", 0); PlaySession.markLeft(s)
        val ended = PlaySession.end(s, 59_999)!!
        assertEquals(0, ended.minutes); assertFalse(ended.worthOffering)
    }
    @Test fun `sem sair do app a sessao continua e nada e oferecido`() {
        val s = MemoryStore(); PlaySession.begin(s, "k", 0)
        assertNull(PlaySession.end(s, 10 * min)); assertEquals("k", PlaySession.active(s))
    }
    @Test fun `a sessao so e entregue uma vez`() {
        val s = MemoryStore(); PlaySession.begin(s, "k", 0); PlaySession.markLeft(s)
        assertNotNull(PlaySession.end(s, 5 * min)); assertNull(PlaySession.end(s, 6 * min)); assertNull(PlaySession.active(s))
    }
    @Test fun `sair de cena sem sessao nao cria sessao`() {
        val s = MemoryStore(); PlaySession.markLeft(s); assertNull(PlaySession.active(s)); assertNull(PlaySession.end(s, 100))
    }
    @Test fun `uma nova sessao zera a saida anterior`() {
        val s = MemoryStore(); PlaySession.begin(s, "a", 0); PlaySession.markLeft(s); PlaySession.begin(s, "b", 10 * min)
        assertNull(PlaySession.end(s, 20 * min))          // b ainda não saiu de cena
        PlaySession.markLeft(s); assertEquals(EndedSession("b", 10), PlaySession.end(s, 20 * min))
    }
    @Test fun `limites do registro manual e relogio que anda para tras`() {
        assertTrue(PlaySession.valid(1)); assertTrue(PlaySession.valid(1440)); assertFalse(PlaySession.valid(0)); assertFalse(PlaySession.valid(1441)); assertFalse(PlaySession.valid(null))
        assertEquals(1440, PlaySession.clamp(5000)); assertEquals(1, PlaySession.clamp(0))
        assertEquals(0, PlaySession.minutes(10 * min, 5 * min))
    }
    @Test fun `cancelar apaga a sessao`() {
        val s = MemoryStore(); PlaySession.begin(s, "k", 0); PlaySession.cancel(s); assertNull(PlaySession.active(s))
    }
}
