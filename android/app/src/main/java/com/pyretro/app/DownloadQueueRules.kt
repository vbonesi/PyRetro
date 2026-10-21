package com.pyretro.app

enum class DownloadState { WAITING, RUNNING, PAUSED, FAILED, DONE }
data class QueuePosition(val key:String,val state:DownloadState)

object DownloadQueueRules {
    fun recover(state:DownloadState)=if(state==DownloadState.RUNNING)DownloadState.PAUSED else state
    fun next(rows:List<QueuePosition>)=rows.firstOrNull { it.state==DownloadState.WAITING }?.key
    fun move(rows:List<QueuePosition>,key:String,step:Int):List<QueuePosition> {
        require(step in listOf(-1,1))
        val index=rows.indexOfFirst { it.key==key };require(index>=0)
        require(rows[index].state!=DownloadState.RUNNING) { "Pause a fila antes de mover o download ativo." }
        val target=(index+step).coerceIn(0,rows.lastIndex)
        return rows.toMutableList().apply { add(target,removeAt(index)) }
    }
    fun removable(pinned:Boolean,queued:Boolean,extension:String)=!pinned && !queued && extension.lowercase() !in setOf("cue","m3u")
}
