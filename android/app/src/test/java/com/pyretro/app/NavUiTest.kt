package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class NavUiTest {
    @Test fun `memoria de foco guarda o ultimo card por tela`() {
        assertNull(FocusMemory.get("teste-a"))
        FocusMemory.set("teste-a", "k1"); FocusMemory.set("teste-a", "k2"); FocusMemory.set("teste-b", "x")
        assertEquals("k2", FocusMemory.get("teste-a")); assertEquals("x", FocusMemory.get("teste-b"))
    }
    @Test fun `faixa de botoes preserva a ordem e as condicoes`() {
        val scope = FlowScope(); val seen = mutableListOf<String>()
        scope.item { seen += "a" }; scope.items(listOf(1, 2)) { seen += "i$it" }
        assertEquals(3, scope.parts.size)
    }
}
