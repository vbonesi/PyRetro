package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.locks.ReentrantLock

class DownloadStore(private val store:LibraryStore) {
    private val resolver=store.context.contentResolver
    private val directory=File(store.context.filesDir,if(store.preferenceName=="pyretro")"downloads" else store.preferenceName+"-downloads").apply { mkdirs() }
    private val storage=SafStorage(store,12L*1024*1024*1024)
    companion object {
        private val paused=AtomicBoolean(false)
        private val locks=ConcurrentHashMap<String,ReentrantLock>()
        fun pause() { paused.set(true) }
    }
    private fun <T> exclusive(action:()->T):T {
        val lock=locks.getOrPut(store.preferenceName) { ReentrantLock() }
        require(lock.tryLock()) { "Há uma transferência em andamento. Pause e aguarde antes de descartar ou iniciar outra cópia." }
        try { return action() } finally { lock.unlock() }
    }
    private fun id(key:String)=MessageDigest.getInstance("SHA-256").digest(key.toByteArray()).joinToString("") { "%02x".format(it) }
    private fun record(key:String)=File(directory,id(key)+".json")
    private fun part(key:String)=File(directory,id(key)+".part")
    private fun save(job:JSONObject) {
        val dest=record(job.getString("key"));val temp=File(directory,dest.name+".tmp")
        temp.writeText(job.toString());require(temp.renameTo(dest)) { "Não foi possível guardar o download." }
    }
    private fun metadata(uri:Uri):JSONObject = resolver.query(uri,arrayOf(OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED),null,null,null)?.use { c ->
        require(c.moveToFirst()) { "Origem indisponível." }
        JSONObject().put("name",c.getString(0)).put("size",if(c.isNull(1))-1 else c.getLong(1)).put("modified",if(c.isNull(2))0 else c.getLong(2))
    } ?: error("Permissão da origem indisponível; selecione novamente o arquivo.")
    fun jobs():List<JSONObject> = directory.listFiles().orEmpty().filter { it.extension=="json" }.map { file ->
        val job=JSONObject(file.readText());require(file.name==id(job.getString("key"))+".json")
        job.put("bytes",part(job.getString("key")).length())
    }
    private fun cleanStage(job:JSONObject) {
        val value=job.optString("stage");if(value.isBlank())return
        val tree=Uri.parse(job.getString("tree"));val parent=storage.folder(tree,false) ?: error("Pasta do download indisponível.")
        val candidate=storage.children(tree,parent).entries.find { it.value.toString()==value }
        if(candidate!=null) {
            require(candidate.key.matches(Regex("\\.pyretro-stage-[0-9a-f-]{36}"))) { "Arquivo temporário mudou; confira a pasta." }
            require(DocumentsContract.deleteDocument(resolver,candidate.value))
        }
        job.remove("stage");save(job)
    }
    fun discard(key:String)=exclusive {
        val file=record(key);if(file.exists())cleanStage(JSONObject(file.readText()))
        require(!part(key).exists() || part(key).delete());require(!file.exists() || file.delete())
    }
    fun download(game:Game,sourceOverride:Uri?=null,treeOverride:Uri?=null,cancelled:()->Boolean={false},onSize:(Long?)->Unit={},progress:(Long)->Unit):Uri=exclusive {
        copy(game,sourceOverride,treeOverride,cancelled,onSize,progress)
    }
    private fun copy(game:Game,sourceOverride:Uri?,treeOverride:Uri?,cancelled:()->Boolean,onSize:(Long?)->Unit,progress:(Long)->Unit):Uri {
        paused.set(false)
        val source=sourceOverride ?: Uri.parse(store.prefs.getString("cloud:${game.key}",null) ?: error("Vincule a ROM ou indexe a nuvem primeiro."))
        require(source.scheme=="content") { "Escolha um arquivo pelo seletor Android." }
        val tree=treeOverride ?: store.tree(game.code) ?: error("Escolha uma pasta local de ${game.code}.")
        require(tree.authority=="com.android.externalstorage.documents")
        val meta=metadata(source);val name=meta.getString("name")
        require(store.accepts(game.code,name) && name.substringAfterLast('.').lowercase() !in setOf("cue","m3u")) { "Escolha um formato independente; PS1 sob demanda usa CHD/PBP." }
        require(name !in listOf(".","..") && !name.contains('/') && !name.contains('\\'))
        val saved=record(game.key)
        val job=if(saved.exists())JSONObject(saved.readText()) else JSONObject().put("key",game.key).put("code",game.code).put("title",game.name).put("source",source.toString()).put("tree",tree.toString()).put("metadata",meta)
        require(job.getString("source")==source.toString() && job.getString("tree")==tree.toString() && job.getString("code")==game.code) { "Origem ou destino mudou. Descarte o download anterior em Downloads antes de reiniciar." }
        val before=job.getJSONObject("metadata")
        require(listOf("name","size","modified").all { before.get(it).toString()==meta.get(it).toString() }) { "Origem mudou. A cópia parcial está preservada; descarte-a para reiniciar." }
        save(job);cleanStage(job)
        val size=meta.getLong("size").takeIf { it>=0 }
        require(size==null || size<=12L*1024*1024*1024) { "ROM acima do limite de 12 GB." }
        if(size!=null)require(android.os.StatFs(store.context.filesDir.path).availableBytes>=maxOf(0,size-part(game.key).length())) { "Espaço insuficiente para o checkpoint privado. Libere espaço e continue a fila." }
        onSize(size)
        val checksum=resolver.openInputStream(source).use { input -> requireNotNull(input);ResumableCopy.copy(input,part(game.key),size,cancelled={paused.get() || cancelled()},progress=progress) }
        if(paused.get() || cancelled())throw ResumableCopy.Paused()
        val after=metadata(source)
        require(listOf("name","size","modified").all { before.get(it).toString()==after.get(it).toString() }) { "Origem mudou durante a cópia; parcial preservado." }
        job.put("sha256",checksum);save(job)
        val parent=storage.folder(tree,true)!!;val existing=storage.children(tree,parent)[name]
        val finished=if(existing!=null) {
            require(storage.fingerprint(existing).sha256==checksum) { "Já existe $name diferente no celular. Nenhum arquivo foi substituído." };existing
        } else {
            storage.publish(tree,parent,name,part(game.key),checksum,null) { stage -> job.put("stage",stage.toString());save(job) }
            storage.children(tree,parent)[name] ?: error("Arquivo concluído não encontrado; checkpoint preservado.")
        }
        require(store.prefs.edit().putString("rom:${game.key}",finished.toString()).commit())
        part(game.key).delete();saved.delete();return finished
    }
}
