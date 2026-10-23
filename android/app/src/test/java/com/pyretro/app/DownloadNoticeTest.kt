package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Texto da notificação de downloads para cada estado da fila. */
class DownloadNoticeTest {
    private fun row(name:String,state:DownloadState,bytes:Long=0,total:Long?=null,error:String="")=
        QuededHelper.row(name,state,bytes,total,error)
    @Test fun runningShowsPercentAndQueue() {
        val n=DownloadNotice.of(listOf(row("A",DownloadState.RUNNING,50,200),row("B",DownloadState.WAITING)),true)!!
        assertEquals("Baixando A",n.title);assertEquals("25% · mais 1 na fila",n.text);assertEquals(25,n.percent);assertTrue(n.ongoing)
    }
    @Test fun finishedStatesBecomeResultNotices() {
        assertEquals("Download falhou: B",DownloadNotice.of(listOf(row("A",DownloadState.DONE),row("B",DownloadState.FAILED,error="sem rede")),false)!!.title)
        assertEquals("Downloads pausados",DownloadNotice.of(listOf(row("A",DownloadState.PAUSED)),false)!!.title)
        assertEquals("A está pronto em Neste celular",DownloadNotice.of(listOf(row("A",DownloadState.DONE)),false)!!.text)
        assertEquals("2 jogos prontos em Neste celular",DownloadNotice.of(listOf(row("A",DownloadState.DONE),row("B",DownloadState.DONE)),false)!!.text)
        assertNull(DownloadNotice.of(emptyList(),false))
    }
}

private object QuededHelper {
    fun row(name:String,state:DownloadState,bytes:Long,total:Long?,error:String)=
        QueuedDownload(Game("",name,name,"NES"),"src","tree",state,bytes,total,error)
}
