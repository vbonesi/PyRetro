package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class GameLogicTest {
    @Test fun exactAliasesNeverPickASequelOrAmbiguousFile() {
        assertEquals("Jogo Á.chd",GameLogic.exactFile("Jogo A",emptyList(),listOf("Jogo Á.chd","Jogo A II.chd")))
        assertEquals("Original.nds",GameLogic.exactFile("Novo nome",listOf("Original"),listOf("Original.nds")))
        assertNull(GameLogic.exactFile("Jogo",emptyList(),listOf("Jogo.chd","Jogo.pbp")))
        assertNull(GameLogic.exactFile("Jogo",emptyList(),listOf("Jogo II.chd")))
    }
    @Test fun progressKeepsCascadeConsistentOffline() {
        assertEquals(mapOf("iniciado" to true,"finalizado" to true,"platinado" to true),GameLogic.progress("platinado",true))
        assertEquals(mapOf("finalizado" to false,"platinado" to false),GameLogic.progress("finalizado",false))
        assertEquals(mapOf("iniciado" to true),GameLogic.progress("iniciado",true))
    }
    @Test fun localIdentityPreservesSameNameInDifferentFolders() {
        assertNotEquals(GameLogic.localKey("PS","content://local/edition-a/Jogo.chd"),GameLogic.localKey("PS","content://local/edition-b/Jogo.chd"))
        assertEquals(GameLogic.localKey("PS","content://local/Jogo.chd"),GameLogic.localKey("PS","content://local/Jogo.chd"))
    }
    @Test fun removalIsOfferedOnlyForNewCompletionWithLocalRom() {
        assertTrue(GameLogic.offerRemoval(false,true,true))
        assertFalse(GameLogic.offerRemoval(true,true,true))
        assertFalse(GameLogic.offerRemoval(false,false,true))
        assertFalse(GameLogic.offerRemoval(false,true,false))
    }
    @Test fun coreProfilesKeepExistingDefaultsAndRejectUnknownPaths() {
        assertEquals("nestopia",CoreProfiles.id("FC"))
        assertEquals("mednafen_pce",CoreProfiles.id("PCECD"))
        assertEquals("melonds",CoreProfiles.id("NDS"))
        assertEquals("mupen64plus_next_gles3",CoreProfiles.id("N64"))
        assertEquals("fceumm",CoreProfiles.id("FC","fceumm"))
        try { CoreProfiles.id("FC","../../bad.so");fail("core livre não pode formar um caminho") } catch(_:IllegalArgumentException) {}
        try { CoreProfiles.id("FC","snes9x");fail("core de outro sistema não pode ser usado") } catch(_:IllegalArgumentException) {}
    }
    @Test fun remoteRoutingOnlyUsesCompatibleConsoles() {
        assertEquals("com.playstation.remoteplay",GameLogic.remotePackage("PlayStation 4"))
        assertEquals("com.grill.xbxplay",GameLogic.remotePackage("Xbox One"))
        for(platform in listOf("Xbox 360","PlayStation 3","Nintendo Switch","Steam"))assertNull(GameLogic.remotePackage(platform))
    }
}
