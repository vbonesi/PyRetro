package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class GlyphRulesTest {
    @Test fun detectsCommonFamiliesAndManualChoiceWins() {
        assertEquals("ps",GlyphRules.family("auto",listOf("Sony Interactive Entertainment Wireless Controller")))
        assertEquals("xbox",GlyphRules.family("auto",listOf("GameSir Galileo G8")))
        assertEquals("generic",GlyphRules.family("auto",emptyList()))
        assertEquals("xbox",GlyphRules.family("xbox",listOf("DualSense")))
        assertEquals("✕",GlyphRules.key("ps","A"));assertEquals("L1",GlyphRules.key("ps","LB"))
        assertEquals("A",GlyphRules.key("xbox","A"))
    }
}
