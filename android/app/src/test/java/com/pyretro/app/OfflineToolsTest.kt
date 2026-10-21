package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.security.MessageDigest

class OfflineToolsTest {
    private fun hash(data:ByteArray)=MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { "%02x".format(it) }
    private fun temporary(block:(File)->Unit) { val file=File.createTempFile("pyretro-test-",".part");try { block(file) } finally { file.delete() } }
    @Test fun resumedCopyValidatesPrefixAndReturnsCompleteChecksum()=temporary { file ->
        val bytes=ByteArray(900000) { (it%251).toByte() };file.writeBytes(bytes.copyOf(123456))
        assertEquals(hash(bytes),ResumableCopy.copy(ByteArrayInputStream(bytes),file,bytes.size.toLong()))
        assertArrayEquals(bytes,file.readBytes())
    }
    @Test fun divergentOrShorterOriginCannotAppendToCheckpoint()=temporary { file ->
        file.writeText("original-prefix")
        for(bytes in listOf("changed-prefix-longer".toByteArray(),"ori".toByteArray())) {
            try { ResumableCopy.copy(ByteArrayInputStream(bytes),file,null);fail() } catch(_:IllegalArgumentException) {}
            assertEquals("original-prefix",file.readText())
        }
    }
    @Test fun interruptedTransferKeepsBytesForRetry()=temporary { file ->
        val bytes=ByteArray(700000) { (it%197).toByte() }
        val broken=object:InputStream() {
            var count=0
            override fun read():Int { if(count>=100000)throw IOException("offline");return bytes[count++].toInt() and 255 }
            override fun read(target:ByteArray,off:Int,len:Int):Int { if(count>=100000)throw IOException("offline");val n=minOf(len,100000-count);bytes.copyInto(target,off,count,count+n);count+=n;return n }
        }
        try { ResumableCopy.copy(broken,file,bytes.size.toLong());fail() } catch(_:IOException) {}
        assertEquals(100000L,file.length())
        assertEquals(hash(bytes),ResumableCopy.copy(ByteArrayInputStream(bytes),file,bytes.size.toLong()))
    }
    @Test fun pauseKeepsCheckpointAndSecondPassCompletes()=temporary { file ->
        val bytes=ByteArray(600000) { 42 };var pause=false
        try { ResumableCopy.copy(ByteArrayInputStream(bytes),file,bytes.size.toLong(),cancelled={pause},progress={if(it>0)pause=true});fail() } catch(_:ResumableCopy.Paused) {}
        assertTrue(file.length() in 1 until bytes.size.toLong())
        ResumableCopy.copy(ByteArrayInputStream(bytes),file,bytes.size.toLong());assertArrayEquals(bytes,file.readBytes())
    }
    @Test fun sizeLimitsAndPrematureEndAreNotSuccessful()=temporary { file ->
        try { ResumableCopy.copy(ByteArrayInputStream(byteArrayOf(1,2,3)),file,2);fail() } catch(_:IllegalArgumentException) {}
        assertEquals(0L,file.length())
        try { ResumableCopy.copy(ByteArrayInputStream(byteArrayOf(1,2,3)),file,4);fail() } catch(_:IllegalArgumentException) {}
        assertEquals(3L,file.length())
    }
    @Test fun shortReadsAndUnknownSizeAreSupported()=temporary { file ->
        val bytes="small but complete".toByteArray();file.writeBytes(bytes.copyOf(5))
        val input=object:ByteArrayInputStream(bytes) { override fun read(b:ByteArray,off:Int,len:Int)=super.read(b,off,minOf(2,len)) }
        assertEquals(hash(bytes),ResumableCopy.copy(input,file,null));assertArrayEquals(bytes,file.readBytes())
    }
    @Test fun catalogRequiresUniqueCandidateAndUniqueOwner() {
        assertEquals(mapOf("mario" to "uri:1"),CatalogRules.match(mapOf("mario" to setOf("mario64")),mapOf("uri:1" to "Mario 64.z64")))
        assertTrue(CatalogRules.match(mapOf("a" to setOf("same"),"b" to setOf("same")),mapOf("uri" to "Same.nes")).isEmpty())
        assertTrue(CatalogRules.match(mapOf("a" to setOf("same")),mapOf("uri:1" to "Same.nes","uri:2" to "Same.zip")).isEmpty())
    }
    @Test fun playlistRemovalOnlyAffectsChosenSystemAndRoot() {
        val existing=listOf("/games/FC/missing.nes","/games/FC/keep.nes","/games/SFC/other.sfc","/games/FC/Disc.cue","/games/FC-backup/old.nes")
        assertEquals(setOf("/games/FC/missing.nes"),PlaylistRules.removed(existing,setOf("/games/FC/keep.nes"),"/games/FC",setOf("nes","zip")))
        assertEquals("/storage/emulated/0/Jogos/FC/Game.nes",PlaylistRules.path("primary:Jogos/FC/Game.nes"))
        try { PlaylistRules.path("primary:Jogos/../outside");fail() } catch(_:IllegalArgumentException) {}
    }
}
