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
    private fun ncch(title:Long):ByteArray { val h=ByteArray(512);"NCCH".toByteArray().copyInto(h,0x100)
        h[0x104]=4 // 4 unidades de 512
        for(i in 0 until 8)h[0x118+i]=((title ushr (8*i)) and 0xff).toByte();return h }
    @Test fun programIdFromNcchAndNcsd() {
        val id=0x0004000000055D00L
        assertEquals("0004000000055d00",SaveIdRules.programId(4096) { ncch(id) })
        val ncsd=ByteArray(512);"NCSD".toByteArray().copyInto(ncsd,0x100);ncsd[0x120]=2;ncsd[0x124]=6
        assertEquals("0004000000055d00",SaveIdRules.programId(8*512L) { off -> if(off==0L)ncsd else { assertEquals(1024L,off);ncch(id) } })
        assertThrows(IllegalArgumentException::class.java) { SaveIdRules.programId(4096) { ncch(0x0004000E00055D00L) } }
        assertThrows(IllegalArgumentException::class.java) { SaveIdRules.programId(100) { ByteArray(512) } }
    }
}
