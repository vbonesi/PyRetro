package com.pyretro.app

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** Biblioteca local e diário; só segmentos imutáveis são enviados pelo celular. */
class CloudLibrary(private val store:LibraryStore) {
    companion object { private val syncLock=Any() }
    val db=AndroidJournalDb(store.context,store.preferenceName+"-library.db")
    val journal=LibraryJournal(db,store.prefs.getString("library-device",null) ?: ("android-"+UUID.randomUUID()).also { store.prefs.edit().putString("library-device",it).commit() })
    val drive=GoogleDrive(store.context,store.prefs)
    private val remote get()=DriveCloudStorage(drive)
    fun ready()=db.meta("cloud_loaded")==true
    fun seed(legacy:List<Game>)=journal.seed(CloudCatalog.libraryFrom(legacy))
    fun game(id:String)=if(id.isBlank())null else db.game(id)
    fun edit(game:Game,fields:JSONObject) {
        seed(store.legacyCached())
        db.transaction {
            val library=journal.library();val rows=JournalRules.games(library)
            val row=rows[game.id] ?: CloudCatalog.libraryFrom(listOf(game)).getJSONArray("games").getJSONObject(0).also { rows[game.id]=it }
            for(field in fields.keys()) {
                if(field=="_play_sessions") { val merged=row.optJSONObject(field) ?: JSONObject();val incoming=fields.getJSONObject(field)
                    for(event in incoming.keys()) { require(!merged.has(event) || merged.getLong(event)==incoming.getLong(event));merged.put(event,incoming.getLong(event)) };row.put(field,merged)
                } else row.put(field,fields.opt(field) ?: JSONObject.NULL)
            }
            library.put("games",JSONArray(rows.values.toList()));journal.record(library)
        }
        if(store.preferenceName=="pyretro" && MainActivity.automaticUpdates && drive.connected)LibraryWorker.enqueue(store.context)
    }
    fun session(game:Game,minutes:Int,event:String) {
        require(minutes in 1..1440)
        val row=this.game(game.id) ?: CloudCatalog.libraryFrom(listOf(game)).getJSONArray("games").getJSONObject(0)
        val sessions=row.optJSONObject("_play_sessions") ?: JSONObject()
        val key=journal.device+":"+event
        if(sessions.has(key)) { require(sessions.getLong(key)==minutes*60L);return }
        sessions.put(key,minutes*60L);edit(game,JSONObject().put("_play_sessions",sessions))
    }
    fun migratePending() {
        val byKey=store.legacyCached().associateBy { it.key }
        for((key,value) in store.prefs.all.filterKeys { it.startsWith("pending:") || it.startsWith("time-event:") }) {
            val raw=value as? String ?: continue
            if(store.prefs.getString("conflict:$key",null)==raw)continue
            val item=JSONObject(raw);val game=byKey[item.optString("key")] ?: continue
            if(game.id.isBlank())continue
            if(key.startsWith("pending:"))edit(game,item.getJSONObject("campos"))
            else session(game,item.getInt("minutes"),item.getString("event"))
            if(store.prefs.getString(key,null)==raw)store.prefs.edit().remove(key).remove("conflict:$key").commit()
        }
        if(!store.prefs.getBoolean("library-favorites-migrated",false)) {
            for(g in byKey.values)if(g.id.isNotBlank() && store.prefs.contains("favorite:${g.key}"))edit(g,JSONObject().put("favorite",store.prefs.getBoolean("favorite:${g.key}",false)))
            store.prefs.edit().putBoolean("library-favorites-migrated",true).commit()
        }
    }
    fun files():Map<String,List<DriveRef>> = store.folders.keys.associateWith { code ->
        val rows=JSONArray(store.prefs.getString("drive-index:$code","[]"));(0 until rows.length()).map { rows.getJSONObject(it) }.map { DriveRef(it.getString("id"),it.getString("name"),it.getLong("size"),it.optString("md5")) }
    }
    fun catalog()=CloudCatalog.games(journal.library(),store.legacyCached(),files(),store::accepts)
    fun sync(forceIndex:Boolean=false):String=synchronized(syncLock) {
        require(drive.connected) { "Conecte a conta Google em Opções para sincronizar a Biblioteca sem o notebook." }
        seed(store.legacyCached())
        val account=drive.accountId();val previous=db.meta("account") as? String
        require(previous==null || account==previous) { "Outra conta Google: a Biblioteca e a fila atuais foram preservadas. Reconecte a conta anterior." }
        db.transaction { db.putMeta("account",account) }
        val cloud=remote
        if(!ready()) {
            val pointer=JSONObject(String(cloud.get("snapshots/library/latest.json"),Charsets.UTF_8));val file=pointer.getString("file")
            require(Regex("[0-9]{8}-[0-9]{6}-[a-f0-9]{12}").matches(file)) { "Nome de snapshot inválido." }
            val bytes=cloud.get("snapshots/library/$file")
            require(bytes.size<=32*1024*1024 && CloudRules.sha256(bytes)==pointer.getString("sha256") && bytes.size.toLong()==pointer.getLong("size")) { "Snapshot não confere; Biblioteca local preservada." }
            journal.bootstrap(JSONObject(String(bytes,Charsets.UTF_8)),pointer.optJSONObject("journal") ?: JSONObject())
        }
        migratePending()
        val applied=journal.pull(cloud);val sent=journal.publish(cloud)
        val errors=mutableListOf<String>()
        if(forceIndex || System.currentTimeMillis()-store.prefs.getLong("drive-index-at",0)>6*60*60*1000L) {
            for(code in store.folders.keys)runCatching { drive.romFiles(code) }.onSuccess { rows ->
                store.prefs.edit().putString("drive-index:$code",JSONArray(rows.map { JSONObject().put("id",it.id).put("name",it.name).put("size",it.size).put("md5",it.md5) }).toString()).commit()
            }.onFailure { errors.add("$code: ${it.message}") }
            if(errors.isEmpty())store.prefs.edit().putLong("drive-index-at",System.currentTimeMillis()).apply()
        }
        val message="Biblioteca na nuvem: $sent alteração(ões) enviada(s), $applied recebida(s)."+(if(errors.isEmpty())"" else " Índice parcial: ${errors.joinToString()}")
        store.prefs.edit().putLong("library-sync-at",System.currentTimeMillis()).putString("library-sync-result",message).putLong("updated",System.currentTimeMillis()).apply()
        message
    }
}
