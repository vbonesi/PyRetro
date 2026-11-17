package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class AppSyncTest {
    private val min = 60_000L
    @Test fun `atualiza na primeira vez e depois so apos 15 minutos`() {
        assertTrue(AppSync.due(1_000, 0, force = false))
        assertFalse(AppSync.due(10 * min, 1_000, force = false))
        assertFalse(AppSync.due(1_000 + 15 * min - 1, 1_000, force = false))
        assertTrue(AppSync.due(1_000 + 15 * min, 1_000, force = false))
    }
    @Test fun `forcar ignora o limite mas desligado nunca atualiza`() {
        assertTrue(AppSync.due(2_000, 1_000, force = true))
        assertFalse(AppSync.due(2_000, 0, force = true, enabled = false))
    }
    @Test fun `o plano segue Drive, pendencias e catalogo velho`() {
        assertEquals(AppSync.Step.WORKER_AND_TRACKING, AppSync.plan(true, 0, false, false))
        assertEquals(AppSync.Step.TRACKING, AppSync.plan(false, 2, true, true))
        assertEquals(AppSync.Step.CATALOG, AppSync.plan(false, 0, true, false))
        assertEquals(AppSync.Step.CATALOG, AppSync.plan(false, 0, false, true))
        assertEquals(AppSync.Step.NONE, AppSync.plan(false, 0, false, false))
    }
    @Test fun `catalogo e velho depois de 6 horas`() {
        assertFalse(AppSync.isStale(1_000, 1_000 + 6 * 60 * min)); assertTrue(AppSync.isStale(1_000, 1_001 + 6 * 60 * min))
    }
    @Test fun `texto de estado do Inicio`() {
        val f = { t: Long -> "dia$t" }
        assertEquals("Online · atualizado dia5", AppSync.statusLine(true, 5, false, f))
        assertEquals("Online · notebook conectado. Buscando o catálogo…", AppSync.statusLine(true, 0, true, f))
        assertEquals("Offline · catálogo em cache de dia5", AppSync.statusLine(false, 5, false, f))
        assertEquals("Offline · catálogo em cache", AppSync.statusLine(false, 0, false, f))
        assertEquals("Offline · sem catálogo em cache", AppSync.statusLine(false, 0, true, f))
    }
}
