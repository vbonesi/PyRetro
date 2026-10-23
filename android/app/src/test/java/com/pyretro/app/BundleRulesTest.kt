package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Conjuntos de discos: origem guardada, caminhos seguros e ordem de publicação. */
class BundleRulesTest {
    private val id="a".repeat(64)
    @Test fun referenceRoundTripsAndRejectsUnsafeEntries() {
        val ref=BundleRef("PS","Jogo (Disc 1).m3u",id,100)
        assertEquals(ref,BundleRules.parse(ref.encoded()))
        assertNull(BundleRules.parse(BundleRef("PS","../Jogo.cue",id,1).encoded()))
        assertNull(BundleRules.parse(BundleRef("PS","Jogo.chd",id,1).encoded()))
        assertNull(BundleRules.parse(BundleRef("PS","Jogo.cue","curto",1).encoded()))
    }
    @Test fun dependenciesFirstEntryLast() {
        val members=listOf(BundleMember("Jogo.m3u",1,"e",true),BundleMember("CD/Jogo (Disc 1).cue",1,"e",true),
            BundleMember("CD/Jogo (Disc 1).bin",9,"e",false),BundleMember("CD/Jogo (Disc 2).cue",1,"e",true),BundleMember("CD/Jogo (Disc 2).bin",9,"e",false))
        assertEquals(listOf("CD/Jogo (Disc 1).bin","CD/Jogo (Disc 2).bin","CD/Jogo (Disc 1).cue","CD/Jogo (Disc 2).cue","Jogo.m3u"),
            BundleRules.publishOrder(members,"Jogo.m3u").map { it.file })
    }
    @Test fun invalidManifestsAreRefused() {
        assertThrows(IllegalArgumentException::class.java) { BundleRules.publishOrder(listOf(BundleMember("../x.bin",1,"e",false),BundleMember("x.cue",1,"e",true)),"x.cue") }
        assertThrows(IllegalArgumentException::class.java) { BundleRules.publishOrder(listOf(BundleMember("x.bin",1,"e",false)),"x.cue") }
        assertThrows(IllegalArgumentException::class.java) { BundleRules.publishOrder(listOf(BundleMember("x.cue",1,"e",true),BundleMember("x.cue",1,"e",true)),"x.cue") }
    }
    @Test fun referencesLikeServer() {
        assertEquals(listOf("Jogo (Track 1).bin","Jogo (Track 2).bin"),BundleRules.references("FILE \"Jogo (Track 1).bin\" BINARY\n  TRACK 01 MODE2/2352\nFILE \"Jogo (Track 2).bin\" BINARY\n","cue"))
        assertEquals(listOf("A.cue","B.cue"),BundleRules.references("#EXTM3U\nA.cue\n\nB.cue\n","m3u"))
        assertEquals(listOf("track01.bin","track 02.raw"),BundleRules.references("2\n1 0 4 2352 track01.bin 0\n2 450 0 2352 \"track 02.raw\" 0\n","gdi"))
        assertThrows(IllegalArgumentException::class.java) { BundleRules.references("FILE ../x.bin BINARY","cue") }
    }
    @Test fun removalKeepsSharedTracksAndRefusesWhenSomethingIsUnreadable() {
        val files=mapOf("Jogo.m3u" to "D1.cue\nD2.cue","D1.cue" to "FILE \"D1.bin\" BINARY","D2.cue" to "FILE \"D2.bin\" BINARY","Extra.cue" to "FILE \"D2.bin\" BINARY")
        val inventory=files.keys+setOf("D1.bin","D2.bin","Outro.chd")
        val plan=BundleRules.removalPlan("Jogo.m3u",inventory) { files.getValue(it) }
        assertTrue(plan.complete)
        assertEquals(listOf("Jogo.m3u","D1.cue","D2.cue","D1.bin"),plan.remove)
        assertEquals(listOf("D2.bin"),plan.preserve)
        val broken=BundleRules.removalPlan("D1.cue",inventory+"Ruim.cue") { if(it=="Ruim.cue")error("ilegível") else files.getValue(it) }
        assertFalse(broken.complete);assertTrue(broken.remove.isEmpty())
    }
}
