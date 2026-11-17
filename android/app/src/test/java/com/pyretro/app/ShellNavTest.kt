package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class ShellNavTest {
    @Test fun `voltar de qualquer destino chega ao inicio e so depois sai`() {
        val nav = NavStack()
        assertEquals(Destination.INICIO, nav.current); assertFalse(nav.back())
        nav.select(Destination.BIBLIOTECA); nav.select(Destination.DESEJADOS)
        assertEquals(Destination.DESEJADOS, nav.current)
        assertTrue(nav.back()); assertEquals(Destination.INICIO, nav.current); assertFalse(nav.back())
    }
    @Test fun `escolher o inicio limpa a pilha`() {
        val nav = NavStack(); nav.select(Destination.BUSCA); nav.select(Destination.INICIO)
        assertFalse(nav.canGoBack); assertEquals(Destination.INICIO, nav.current)
    }
    @Test fun `barra lateral em paisagem ou com controle`() {
        assertEquals(NavLayout.BOTTOM_BAR, navLayout(landscape = false, gamepad = false))
        assertEquals(NavLayout.RAIL, navLayout(landscape = true, gamepad = false))
        assertEquals(NavLayout.RAIL, navLayout(landscape = false, gamepad = true))
    }
    @Test fun `quatro destinos`() {
        assertEquals(listOf("Início", "Biblioteca", "Desejados", "Busca"), Destination.values().map { it.label })
    }
}
