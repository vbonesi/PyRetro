package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Mesmas amostras de referência de `tests/test_app.html` (notaColor em logic.js). */
class NotaRulesTest {
    private fun rgb(n:Double?)=NotaRules.rgb(n)?.toList()
    @Test fun referenceSamplesMatchTheWebScale() {
        assertEquals(listOf(237,106,106),rgb(0.0));assertEquals(listOf(237,106,106),rgb(1.0))
        assertEquals(listOf(233,155,86),rgb(4.0));assertEquals(listOf(212,188,99),rgb(6.5))
        assertEquals(listOf(149,200,120),rgb(7.0));assertEquals(listOf(102,210,155),rgb(10.0))
        assertEquals(listOf(241,199,91),rgb(11.0));assertNull(rgb(null))
    }
    @Test fun onlyExactlyElevenIsGoldAndOverTenUsesFullGreen() {
        assertTrue(NotaRules.special(11.0));assertFalse(NotaRules.special(10.5));assertFalse(NotaRules.special(null))
        assertEquals(rgb(10.0),rgb(10.5))
        assertNotEquals(rgb(6.4),rgb(6.9))
    }
    @Test fun editorJumpsBetweenTenAndEleven() {
        assertEquals(11.0,NotaRules.adjust(10.0,0.1),0.0);assertEquals(10.0,NotaRules.adjust(11.0,-0.1),0.0)
        assertEquals(10.0,NotaRules.adjust(9.9,0.1),0.0);assertEquals(11.0,NotaRules.adjust(11.0,0.1),0.0)
        assertEquals(0.0,NotaRules.adjust(0.0,-0.1),0.0);assertEquals(7.6,NotaRules.adjust(7.5,0.1),0.0)
    }
}
