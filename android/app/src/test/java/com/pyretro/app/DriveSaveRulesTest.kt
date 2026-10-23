package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Identidade igual à de core/drive_saves.identity e nome das pendências. */
class DriveSaveRulesTest {
    @Test fun identityMatchesPythonReference() {
        assertEquals("5fea31d3a892c05391ecd9d660cef1edeaeff4032fa519de39aeb77e1aa0eefa",
            DriveSaveRules.identity("123","fold","retro-saves","content://x/tree/primary%3ARetroArch"))
        assertEquals("c9fe53be4303749a796ad2ab727deb3ef40c5777251c6c027134e86ef928dc87",
            DriveSaveRules.identity("é😀","f\"\\","psp-saves","tab\tnl\n"))
    }
    @Test fun pendingNamesRoundTrip() {
        val base="a".repeat(64)
        assertEquals(1700000000000L to base,DriveSaveRules.parsePending(DriveSaveRules.pendingName(1700000000000L,base)))
        assertEquals(1700000000000L to null,DriveSaveRules.parsePending(DriveSaveRules.pendingName(1700000000000L,null)))
        assertNull(DriveSaveRules.parsePending("x.pending"))
    }
}
