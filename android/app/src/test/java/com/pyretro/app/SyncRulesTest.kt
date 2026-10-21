package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class SyncRulesTest {
    @Test fun oneSidedChangesAreDetectedAgainstCommonBaseline() {
        assertEquals("upload",SyncRules.direction("new","old","old"))
        assertEquals("download",SyncRules.direction("old","new","old"))
        assertEquals("same",SyncRules.direction("same","same",null))
        assertEquals("upload",SyncRules.direction("first",null,null))
        assertEquals("download",SyncRules.direction(null,"first",null))
    }
    @Test fun firstSyncDivergenceAndRemovalAreAlwaysConflicts() {
        assertEquals("conflict",SyncRules.direction("left","right",null))
        assertEquals("conflict",SyncRules.direction("left","right","old"))
        assertEquals("conflict",SyncRules.direction(null,"right","old"))
        assertEquals("conflict",SyncRules.direction("left",null,"old"))
        assertEquals("same",SyncRules.direction(null,null,"old"))
    }
    @Test fun pathsAndGroupsCannotIncludeRomsConfigOrHistory() {
        for(path in listOf("../outside.srm","/outside.srm","foo/../a.srm","foo\\a.srm","a:b.srm",".pyretro-history/a.srm","ROM.nes"))assertFalse(SyncRules.accepted("retro-saves",path))
        assertTrue(SyncRules.accepted("retro-saves","Jogo.srm"))
        assertTrue(SyncRules.accepted("retro-states","core/Jogo.state.auto.png"))
        assertTrue(SyncRules.accepted("retro-runtime","core/Jogo.lrtl"))
        assertTrue(SyncRules.accepted("psp-saves","ULUS12345DATA/DATA.BIN"))
        assertFalse(SyncRules.accepted("psp-saves","SYSTEM/ppsspp.ini"))
    }
    @Test fun sdmcIncludesOnlyGameDataAndExtdata() {
        val prefix="Nintendo 3DS/"+"0".repeat(32)+"/"+"1".repeat(32)+"/"
        assertTrue(SyncRules.accepted("3ds-saves",prefix+"title/00040000/00123400/data/00000001/main"))
        assertTrue(SyncRules.accepted("3ds-saves",prefix+"extdata/00000000/00123400/00000001"))
        assertFalse(SyncRules.accepted("3ds-saves",prefix+"title/00040000/00123400/content/game.app"))
        assertFalse(SyncRules.accepted("3ds-saves",prefix+"dbs/title.db"))
    }
}
