package com.pyretro.app

import android.net.Uri
import android.os.StatFs
import android.provider.DocumentsContract

data class RomStamp(val name:String,val size:Long?,val modified:Long?)
data class SpaceRom(val game:Game,val stamp:RomStamp,val pinned:Boolean,val finished:Boolean)
data class SpaceSnapshot(val roms:List<SpaceRom>,val errors:List<String>,val privateFree:Long)

/** Só enumera ROMs concedidas e metadados. Fixação protege todas as rotas de remoção. */
class SpaceStore(private val store:LibraryStore) {
    companion object { val mutationLock=Any() }
    fun documentKey(uri:Uri):String=uri.authority+"|"+store.documentId(uri)
    /** Mesmo critério de [pinned], lendo as preferências uma vez só (listas com milhares de jogos). */
    fun pinnedChecker():(Game)->Boolean {
        val all=store.prefs.all;val identities=all.filterKeys { it.startsWith("keep:") }.values.toSet()
        return { game -> all.containsKey("keep:${game.key}") || game.localUri?.let { documentKey(it) in identities } == true }
    }
    fun pinned(game:Game):Boolean {
        if(store.prefs.contains("keep:${game.key}"))return true
        val uri=game.localUri ?: return false
        val identity=documentKey(uri)
        return store.prefs.all.any { (key,value) -> key.startsWith("keep:") && value==identity }
    }
    fun setPinned(game:Game,value:Boolean)=synchronized(mutationLock) {
        val identity=game.localUri?.let(::documentKey)
        val edit=store.prefs.edit()
        if(value)edit.putString("keep:${game.key}",identity ?: "")
        else {
            edit.remove("keep:${game.key}")
            if(identity!=null)store.prefs.all.filter { it.key.startsWith("keep:") && it.value==identity }.keys.forEach(edit::remove)
        }
        require(edit.commit()) { "Não foi possível guardar a fixação." }
    }
    fun attachPin(game:Game) { if(store.prefs.contains("keep:${game.key}"))setPinned(game,true) }
    fun stamp(uri:Uri):RomStamp=store.context.contentResolver.query(uri,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED),null,null,null)?.use { c ->
        require(c.moveToFirst()) { "ROM indisponível. Atualize a lista." }
        RomStamp(c.getString(0),if(c.isNull(1))null else c.getLong(1),if(c.isNull(2))null else c.getLong(2))
    } ?: error("Sem permissão para conferir a ROM.")
    fun scan(catalog:List<Game>):SpaceSnapshot {
        val errors=mutableListOf<String>();val storage=SafStorage(store)
        val files=store.folders.keys.flatMap { code ->
            runCatching {
                val tree=store.tree(code)
                if(tree==null || storage.folder(tree,false)==null)emptyList() else store.files(code,true)
            }.getOrElse { errors.add(store.folders.getValue(code));emptyList() }
        }
        val bound=store.bind(catalog,files).filter { it.localUri!=null }.groupBy { documentKey(it.localUri!!) }
        val rows=files.distinctBy { documentKey(it.uri) }.mapNotNull { rom ->
            runCatching {
                val matches=bound[documentKey(rom.uri)].orEmpty()
                val game=matches.firstOrNull() ?: Game("",GameLogic.localKey(rom.code,rom.uri.toString()),GameLogic.fileLabel(rom.name),store.folders.getValue(rom.code),rom.code,rom.name,localUri=rom.uri)
                SpaceRom(game,stamp(rom.uri),matches.any(::pinned) || pinned(game),matches.isNotEmpty() && matches.all { store.tracking(it).optBoolean("finalizado") })
            }.getOrElse { errors.add("${store.folders[rom.code]} · ${rom.name}");null }
        }
        return SpaceSnapshot(rows.sortedByDescending { it.stamp.size ?: -1 },errors.distinct(),StatFs(store.context.filesDir.path).availableBytes)
    }
}
