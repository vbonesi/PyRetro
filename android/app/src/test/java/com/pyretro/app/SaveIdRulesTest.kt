package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Mesmos casos de core/game_save_ids.matches: prefixo exato do serial, nada de extdata. */
class SaveIdRulesTest {
    private val id0="0".repeat(32);private val id1="1".repeat(32)
    @Test fun pspMatchesOnlyTheExactSerialPrefix() {
        assertTrue(SaveIdRules.matches("psp-saves","ULUS12345DATA00/DATA.BIN","ULUS12345"))
        assertTrue(SaveIdRules.matches("psp-states","ULUS12345_1.00_0.ppst","ULUS12345"))
        assertFalse(SaveIdRules.matches("psp-saves","ULUS12346DATA00/DATA.BIN","ULUS12345"))
        assertFalse(SaveIdRules.matches("psp-saves","ULES12345DATA00/DATA.BIN","ULUS12345"))
        assertFalse(SaveIdRules.matches("psp-saves","ULUS12345DATA00/DATA.BIN","ulus12345"))
    }
    @Test fun threeDsTitleDataOnlyNeverExtdata() {
        assertTrue(SaveIdRules.matches("3ds-saves","Nintendo 3DS/$id0/$id1/title/00040000/00123400/data/00000001/main","0004000000123400"))
        assertFalse(SaveIdRules.matches("3ds-saves","Nintendo 3DS/$id0/$id1/extdata/00000000/00001234/x","0004000000123400"))
        assertFalse(SaveIdRules.matches("3ds-saves","Nintendo 3DS/$id0/$id1/title/00040000/00999900/data/x","0004000000123400"))
        assertEquals(listOf("psp-saves","psp-states"),SaveIdRules.groups("PSP"))
        assertTrue(SaveIdRules.valid("3DS","0004000000123400"));assertFalse(SaveIdRules.valid("3DS","0004000E00123400"))
    }
    @Test fun threeDsTreesListedOncePerId0Id1() {
        val a="Nintendo 3DS/$id0/$id1";val b="Nintendo 3DS/${"2".repeat(32)}/$id1"
        val paths=listOf("$a/title/00040000/00123400/data/00000001/main","$a/title/00040000/00123400/data/00000001/x","$b/title/00040000/00123400/data/00000001/main","$b/title/00040000/00999900/data/y")
        assertEquals(listOf(a,b).sorted(),SaveIdRules.trees(paths,"0004000000123400"))
        assertEquals(listOf(a,b).sorted().take(1),SaveIdRules.trees(paths.take(2),"0004000000123400"))
    }
}
