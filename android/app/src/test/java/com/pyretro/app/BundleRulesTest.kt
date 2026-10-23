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
}
