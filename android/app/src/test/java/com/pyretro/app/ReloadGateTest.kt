package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class ReloadGateTest {
    @Test fun leituraMaisNovaPrevalece() {
        val gate = ReloadGate()
        val velha = gate.next(); val nova = gate.next()
        assertFalse(gate.isCurrent(velha)); assertTrue(gate.isCurrent(nova))
    }
    @Test fun leituraUnicaPublica() { val gate = ReloadGate(); assertTrue(gate.isCurrent(gate.next())) }
    @Test fun entradaSoLocalSaiDaLista() {
        val local = Game("", "local:a", "Zool", "SNES", "SNES", "z.sfc")
        val cadastrada = Game("1", "k1", "Outro", "SNES", "SNES", "o.sfc", pcLocal = true)
        val lista = RemovalView.afterLocalRemoval(listOf(local, cadastrada), "local:a")
        assertEquals(listOf("k1"), lista.map { it.key })
    }
    @Test fun cadastradaFicaSemArquivo() {
        val g = Game("1", "k1", "Zool", "SNES", "SNES", "z.sfc", pcLocal = true)
        val lista = RemovalView.afterLocalRemoval(listOf(g), "k1")
        assertEquals(1, lista.size); assertNull(lista[0].localUri)
    }
    @Test fun chaveDesconhecidaNaoMudaNada() {
        val g = Game("1", "k1", "Zool", "SNES"); assertEquals(listOf(g), RemovalView.afterLocalRemoval(listOf(g), "x"))
    }
}
