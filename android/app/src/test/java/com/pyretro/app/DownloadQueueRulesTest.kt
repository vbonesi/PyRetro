package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class DownloadQueueRulesTest {
    @Test fun nextPreservesOrderAndNeverRetriesFailuresAutomatically() {
        val rows=listOf(QueuePosition("failed",DownloadState.FAILED),QueuePosition("paused",DownloadState.PAUSED),QueuePosition("b",DownloadState.WAITING),QueuePosition("a",DownloadState.WAITING))
        assertEquals("b",DownloadQueueRules.next(rows))
        assertNull(DownloadQueueRules.next(rows.take(2)))
    }
    @Test fun processRecoveryDoesNotRestartInterruptedTransfer() {
        assertEquals(DownloadState.PAUSED,DownloadQueueRules.recover(DownloadState.RUNNING))
        for(state in DownloadState.entries.filter { it!=DownloadState.RUNNING })assertEquals(state,DownloadQueueRules.recover(state))
    }
    @Test fun reorderChangesOnlyTheSelectedPosition() {
        val rows=listOf("a","b","c").map { QueuePosition(it,DownloadState.WAITING) }
        assertEquals(listOf("b","a","c"),DownloadQueueRules.move(rows,"b",-1).map { it.key })
        assertEquals(listOf("a","c","b"),DownloadQueueRules.move(rows,"b",1).map { it.key })
        assertEquals(rows,DownloadQueueRules.move(rows,"a",-1))
    }
    @Test fun movingActiveOrUnknownEntryIsRefused() {
        val rows=listOf(QueuePosition("a",DownloadState.RUNNING))
        for(key in listOf("a","unknown"))try { DownloadQueueRules.move(rows,key,1);fail() } catch(_:IllegalArgumentException) {}
    }
    @Test fun pinsQueueAndDependentDescriptorsCannotBecomeRemovalCandidates() {
        assertTrue(DownloadQueueRules.removable(false,false,"CHD"))
        assertFalse(DownloadQueueRules.removable(true,false,"nes"))
        assertFalse(DownloadQueueRules.removable(false,true,"nes"))
        for(extension in listOf("cue","CUE","m3u","M3U"))assertFalse(DownloadQueueRules.removable(false,false,extension))
    }
}
