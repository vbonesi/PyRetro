package com.pyretro.app

import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

data class QueuedDownload(val game:Game,val source:String,val tree:String,val state:DownloadState=DownloadState.WAITING,
    val bytes:Long=0,val total:Long?=null,val error:String="")

/** Executor do processo, sem Activity retida e sem reinício automático/serviço em segundo plano. */
class DownloadQueue private constructor(private val store:LibraryStore) {
    companion object {
        private val instances=mutableMapOf<String,DownloadQueue>()
        @Synchronized fun get(store:LibraryStore):DownloadQueue=instances.getOrPut(store.preferenceName) {
            DownloadQueue(LibraryStore(store.context.applicationContext,store.preferenceName))
        }
    }
    private val lock=Any()
    private val worker=Executors.newSingleThreadExecutor()
    private val stop=AtomicBoolean(false)
    @Volatile var running=false;private set
    val pausing:Boolean get()=running && stop.get()
    @Volatile var revision=0L;private set
    @Volatile var completedAt=store.prefs.getLong("queue-completed-at",0);private set
    private fun read():List<QueuedDownload> {
        val rows=JSONArray(store.prefs.getString("download-queue","[]")!!)
        return (0 until rows.length()).map { i -> val row=rows.getJSONObject(i)
            QueuedDownload(store.parse(JSONArray().put(row.getJSONObject("game"))).single(),row.getString("source"),row.getString("tree"),
                DownloadState.valueOf(row.getString("state")),row.optLong("bytes"),if(row.isNull("total"))null else row.getLong("total"),row.optString("error"))
        }.also { rowsList -> require(rowsList.map { it.game.key }.distinct().size==rowsList.size) { "Fila inválida; nenhum download foi iniciado." } }
    }
    private fun save(rows:List<QueuedDownload>) {
        val data=JSONArray(rows.map { row -> JSONObject().put("game",row.game.cache()).put("source",row.source).put("tree",row.tree)
            .put("state",row.state.name).put("bytes",row.bytes).put("total",row.total ?: JSONObject.NULL).put("error",row.error) })
        require(store.prefs.edit().putString("download-queue",data.toString()).commit()) { "Não foi possível guardar a fila." };revision++
    }
    init { synchronized(lock) { val rows=read();if(rows.any { it.state==DownloadState.RUNNING })save(rows.map { it.copy(state=DownloadQueueRules.recover(it.state)) }) } }
    fun snapshot():List<QueuedDownload> = synchronized(lock) { read() }
    fun contains(key:String)=snapshot().any { it.game.key==key && it.state!=DownloadState.DONE }
    private fun identity(uri:String)=runCatching { SpaceStore(store).documentKey(Uri.parse(uri)) }.getOrDefault(uri)
    fun enqueue(game:Game)=synchronized(lock) {
        require(game.code in store.folders)
        val source=store.prefs.getString("cloud:${game.key}",null) ?: error("Vincule a ROM no Drive antes de adicionar à fila.")
        val tree=store.tree(game.code) ?: error("Escolha a pasta local deste sistema primeiro.")
        require(tree.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local de destino." }
        val rows=read();require(rows.none { it.state!=DownloadState.DONE && (it.game.key==game.key || (identity(it.source)==identity(source) && identity(it.tree)==identity(tree.toString()))) }) { "Este arquivo já está na fila para esta pasta." }
        val remaining=rows.filter { it.game.key!=game.key };require(remaining.size<200) { "Fila cheia (200 itens). Retire registros concluídos." }
        save(remaining+QueuedDownload(game.copy(localUri=null),source,tree.toString()))
    }
    fun move(key:String,step:Int)=synchronized(lock) {
        val rows=read();val order=DownloadQueueRules.move(rows.map { QueuePosition(it.game.key,it.state) },key,step)
        save(order.map { position -> rows.first { it.game.key==position.key } })
    }
    fun remove(key:String)=synchronized(lock) {
        val rows=read();require(rows.none { it.game.key==key && it.state==DownloadState.RUNNING }) { "Pause e aguarde o download antes de retirá-lo." }
        save(rows.filter { it.game.key!=key }) // O checkpoint permanece até descarte explícito.
    }
    fun retry(key:String)=synchronized(lock) {
        val rows=read();require(rows.any { it.game.key==key && it.state in setOf(DownloadState.FAILED,DownloadState.PAUSED) })
        save(rows.map { if(it.game.key==key)it.copy(state=DownloadState.WAITING,error="") else it })
    }
    fun pause()=synchronized(lock) { stop.set(true);revision++ }
    fun start(onProgress:(QueuedDownload)->Unit={})=synchronized(lock) {
        require(!running) { "A fila está em andamento ou concluindo a pausa." }
        val rows=read().map { if(it.state==DownloadState.PAUSED)it.copy(state=DownloadState.WAITING,error="") else it }
        require(rows.any { it.state==DownloadState.WAITING }) { "Nenhum download aguardando. Falhas exigem Tentar novamente." }
        save(rows);stop.set(false);running=true;revision++
        worker.execute {
            try {
                while(!stop.get()) {
                    val next=synchronized(lock) {
                        val all=read();val key=DownloadQueueRules.next(all.map { QueuePosition(it.game.key,it.state) })
                        val item=all.firstOrNull { it.game.key==key }
                        if(item!=null)save(all.map { if(it.game.key==key)it.copy(state=DownloadState.RUNNING,error="") else it })
                        item
                    } ?: break
                    var last=0L
                    fun update(transform:(QueuedDownload)->QueuedDownload)=synchronized(lock) { save(read().map { if(it.game.key==next.game.key)transform(it) else it }) }
                    try {
                        require(store.prefs.getString("cloud:${next.game.key}",null)==next.source && store.tree(next.game.code).toString()==next.tree) { "Origem ou pasta mudou. Retire da fila e adicione novamente; parcial preservado." }
                        val uri=DownloadStore(store).download(next.game,sourceOverride=Uri.parse(next.source),treeOverride=Uri.parse(next.tree),cancelled={stop.get()},onSize={ size -> update { it.copy(total=size) } }) { bytes ->
                            val now=System.currentTimeMillis();if(now-last>=500) { last=now;update { it.copy(bytes=bytes) } }
                            onProgress(next.copy(state=DownloadState.RUNNING,bytes=bytes))
                        }
                        next.game.localUri=uri;SpaceStore(store).attachPin(next.game)
                        val playlist=PlaylistStore(store).afterChange(next.game.code)
                        update { it.copy(state=DownloadState.DONE,bytes=SpaceStore(store).stamp(uri).size ?: it.bytes,error=playlist) }
                        completedAt=System.currentTimeMillis();store.prefs.edit().putLong("queue-completed-at",completedAt).apply()
                    } catch(error:Exception) {
                        val paused=stop.get() || error is ResumableCopy.Paused
                        val partial=runCatching { DownloadStore(store).jobs().firstOrNull { it.getString("key")==next.game.key }?.getLong("bytes") }.getOrNull()
                        update { it.copy(state=if(paused)DownloadState.PAUSED else DownloadState.FAILED,bytes=partial ?: it.bytes,error=if(paused)"Cópia parcial preservada." else error.message ?: "Falha no download.") }
                        stop.set(true)
                    }
                }
            } finally { synchronized(lock) { running=false;revision++ } }
        }
    }
}
