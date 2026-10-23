package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Origem do Drive guardada, consulta escapada e escolha do arquivo do jogo. */
class DriveSourceTest {
    @Test fun encodedReferenceRoundTripsAndRejectsPaths() {
        val ref=DriveRef("1AbCdEfGhIjK_-z","Jogo (USA) & Cia.chd",123,"abc")
        assertEquals(ref,DriveSource.parse(ref.encoded()))
        assertNull(DriveSource.parse(DriveRef("1AbCdEfGhIjK","../x.chd",1,"").encoded()))
        assertNull(DriveSource.parse("pyretro-rom:PS/x.chd?etag=1&size=1"))
        assertNull(DriveSource.parse(DriveRef("curto","x.chd",1,"").encoded()))
    }
    @Test fun queryEscapesQuotesAndBackslashes() {
        assertEquals("'pai' in parents and trashed = false and name = 'Assassin\\'s \\\\ Creed' and mimeType = 'application/vnd.google-apps.folder'",
            DriveSource.childQuery("pai","Assassin's \\ Creed",folder=true))
    }
    @Test fun candidatesPreferExactNameThenStemAndSkipDescriptors() {
        val files=listOf(DriveRef("1","Jogo.chd",10,""),DriveRef("2","Jogo.cue",1,""),DriveRef("3","Jogo (Disc 2).chd",10,""),DriveRef("4","Outro.zip",0,""))
        val accepts={ name:String -> name.substringAfterLast('.') in setOf("chd","cue","zip") }
        assertEquals(listOf("1"),DriveSource.candidates(files,"Jogo",accepts).map { it.id })
        assertEquals(listOf("3"),DriveSource.candidates(files,"Jogo (Disc 2).chd",accepts).map { it.id })
        assertTrue(DriveSource.candidates(files,"Outro",accepts).isEmpty())
    }
}
