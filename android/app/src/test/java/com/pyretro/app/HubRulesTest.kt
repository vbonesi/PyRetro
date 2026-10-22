package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.File
import java.security.MessageDigest

/** 0.6: download pelo notebook em um toque e saves por jogo. */
class HubRulesTest {
    private fun hash(data:ByteArray)=MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { "%02x".format(it) }
    @Test fun notebookSourceRoundTripsNamesWithSpacesAndSubfolders() {
        val ref=RomRef("PS","FF7/Final Fantasy VII (Disc 1) & co.chd","123-2026-10-22T10:00:00Z",123)
        assertEquals(ref,RomSource.parse(ref.encoded()))
        assertEquals("Final Fantasy VII (Disc 1) & co.chd",ref.name)
        assertNull(RomSource.parse("content://com.google.android.apps.docs.storage/document/x"))
        for(bad in listOf("pyretro-rom:PS/../x.chd?etag=1&size=1","pyretro-rom:PS/x.chd?etag=1&size=0","pyretro-rom:/x.chd?etag=1&size=3","pyretro-rom:PS/x.chd?size=3"))
            assertNull(bad,RomSource.parse(bad))
    }
    @Test fun retroarchFolderMustBeTheRootNotSavesOrStates() {
        assertNull(SaveRules.retroarchFolderProblem("primary:RetroArch"))
        assertNull(SaveRules.retroarchFolderProblem("primary:Android/data/com.retroarch/files"))
        for(bad in listOf("primary:RetroArch/saves","primary:RetroArch/states/","primary:RetroArch/Saves"))
            assertNotNull(bad,SaveRules.retroarchFolderProblem(bad))
    }
    @Test fun onlyStandaloneFormatsTheAppAcceptsAreOffered() {
        val options=listOf(RomOption("Crash.cue",10,"e","pc"),RomOption("Crash.chd",10,"e","pc"),RomOption("Crash.bin",10,"e","pc"),RomOption("Vazio.chd",0,"e","pc"))
        assertEquals(listOf("Crash.chd"),RomSource.playable(options) { it.substringAfterLast('.') in setOf("chd","pbp","cue","m3u") }.map { it.file })
    }
    @Test fun resumedTransferHashesLocalPrefixWithoutRereadingIt() {
        val file=File.createTempFile("pyretro-test-",".part")
        try {
            val bytes=ByteArray(800000) { (it%233).toByte() };file.writeBytes(bytes.copyOf(300000))
            val rest=ByteArrayInputStream(bytes.copyOfRange(300000,bytes.size))
            assertEquals(hash(bytes),ResumableCopy.copy(rest,file,bytes.size.toLong(),resumed=true))
            assertArrayEquals(bytes,file.readBytes())
        } finally { file.delete() }
    }
    @Test fun savesBelongToTheirGameAndSystemOnly() {
        assertTrue(SaveRules.belongs("N64/Super Mario 64.srm","N64","Super Mario 64"))
        assertTrue(SaveRules.belongs("N64/Super Mario 64.state1.png","N64","Super Mario 64"))
        assertTrue(SaveRules.belongs("N64/Super Mario 64.state.auto","N64","Super Mario 64"))
        assertTrue(SaveRules.belongs("ARCADE/fbneo/kof97.fs","ARCADE","kof97"))
        assertFalse(SaveRules.belongs("FC/Super Mario Bros. 3.srm","FC","Super Mario Bros"))
        assertFalse(SaveRules.belongs("SFC/Aladdin.srm","MD","Aladdin"))
        assertFalse(SaveRules.belongs("Aladdin.srm","MD","Aladdin"))
        assertEquals("Super Mario Bros. 3",SaveRules.label("Super Mario Bros. 3",setOf("nes","zip")))
        assertEquals("Super Mario Bros. 3",SaveRules.label("Super Mario Bros. 3.nes",setOf("nes","zip")))
    }
    @Test fun consolePlatformsSuggestStreamingTheConsole() {
        assertEquals("com.grill.xbxplay",GameLogic.remotePackage("Xbox Series X"))
        assertEquals("com.playstation.remoteplay",GameLogic.remotePackage("PlayStation 5"))
        assertTrue(GameLogic.streamedThroughNotebook("Nintendo Switch"))
        assertFalse(GameLogic.streamedThroughNotebook("Steam"))
    }
}
