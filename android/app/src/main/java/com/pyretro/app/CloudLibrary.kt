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
    private val remote get()=DriveCloudStorage(drive,maxBytes=32*1024*1024)
    fun ready()=db.meta("cloud_loaded")==true
    fun available()=db.meta("seeded")==true
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
    fun catalog()=CloudCatalog.games(journal.library(),store.legacyCached(),files(),JSONObject(store.prefs.getString("arcade-names","{}")),store::accepts)
    fun leaveWishlist(item:WishItem,bought:Boolean) {
        db.transaction { journal.record(LibraryView.leaveWishlist(journal.library(),item,bought)) }
        if(store.preferenceName=="pyretro" && MainActivity.automaticUpdates && drive.connected)LibraryWorker.enqueue(store.context)
    }
    fun register(game:Game,name:String):JSONObject {
        seed(store.legacyCached());require(game.code in store.folders && name.isNotBlank())
        require(!DownloadQueue.get(store).contains(game.key)) { "Aguarde o download ou retire o jogo da fila antes de cadastrar." }
        var id="";var created=false
        db.transaction {
            val data=journal.library();val rows=JournalRules.games(data)
            val candidates=rows.values.filter { CloudCatalog.code(it)==game.code && CloudCatalog.romName(it.optString("nome"))==CloudCatalog.romName(name) }
            require(candidates.size<=1) { "Mais de um cadastro com este nome; escolha o correto na Biblioteca." }
            val row=candidates.singleOrNull() ?: JSONObject().apply {
                put("id","android-"+UUID.randomUUID());put("nome",name);put("plataforma",store.folders.getValue(game.code))
                for(field in listOf("subgenero","genero","nota","data_final","tempo","meta","observacoes","sinopse","lancamento","desenvolvedora","capa"))put(field,JSONObject.NULL)
                for(field in listOf("iniciado","finalizado","platinado","savestate","oculto"))put(field,false)
                put("fontes",JSONArray().put("rom:${game.code}"));put("nomes_alt",JSONArray())
            }.also { rows[it.getString("id")]=it;created=true }
            id=row.getString("id")
            store.prefs.getString("pending:${game.key}",null)?.takeUnless { store.prefs.getString("conflict:pending:${game.key}",null)==it }?.let { raw -> val fields=JSONObject(raw).getJSONObject("campos");for(field in fields.keys())row.put(field,fields.get(field)) }
            if(store.prefs.contains("favorite:${game.key}"))row.put("favorite",store.prefs.getBoolean("favorite:${game.key}",false))
            journal.record(data.put("games",JSONArray(rows.values.toList())))
        }
        if(store.prefs.getString("conflict:pending:${game.key}",null)==null)store.prefs.edit().remove("pending:${game.key}").apply()
        for((key,raw) in store.prefs.all.filterKeys { it.startsWith("time-event:") }) {
            val event=JSONObject(raw as String);if(event.optString("key")!=game.key)continue
            session(game.copy(id=id),event.getInt("minutes"),event.getString("event"));store.prefs.edit().remove(key).apply()
        }
        if(store.preferenceName=="pyretro" && MainActivity.automaticUpdates && drive.connected)LibraryWorker.enqueue(store.context)
        return JSONObject().put("id",id).put("created",created)
    }
    fun cover(game:Game,publish:Boolean=true):java.io.File? {
        if(game.id.isBlank())return null
        val directory=java.io.File(store.context.cacheDir,"covers").apply { mkdirs() }
        val file=java.io.File(directory,"cloud-"+CloudRules.sha256(game.id.toByteArray()))
        val checked="cover-checked:"+game.id
        if(file.isFile && System.currentTimeMillis()-store.prefs.getLong(checked,0)<5*60*1000L)return file
        if(!drive.connected)return file.takeIf { it.isFile }
        try {
            val remote=DriveCloudStorage(drive,maxBytes=CloudCovers.MAX_BYTES)
            val bytes=try { CloudCovers.get(remote,game.id) } catch(_:CloudNotFound) {
                val relative=this.game(game.id)?.optString("capa")?.takeUnless { it.isBlank() || it=="null" } ?: return file.takeIf { it.isFile }
                val original=DriveCloudStorage(drive,listOf("Jogos","Biblioteca"),CloudCovers.MAX_BYTES).get(relative)
                if(publish)CloudCovers.publish(remote,game.id,original)
                original
            }
            val temp=java.io.File.createTempFile("cover-",".tmp",directory)
            try { temp.writeBytes(bytes);check(temp.renameTo(file)) } finally { temp.delete() }
            // Pré-busca não suprime o envio quando o jogo for de fato exibido.
            if(publish)store.prefs.edit().putLong(checked,System.currentTimeMillis()).apply()
            directory.listFiles()?.sortedBy { it.lastModified() }?.dropLast(LibraryStore.COVER_CACHE_LIMIT)?.forEach { it.delete() }
            return file
        } catch(error:Exception) { if(file.isFile)return file;throw error }
    }
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
        try {
            val bytes=cloud.get("catalog/arcade.json");require(bytes.size<=4*1024*1024);val data=JSONObject(String(bytes,Charsets.UTF_8));val parents=ArcadeRules.parse(data)
            val names=data.optJSONObject("names") ?: JSONObject();require(names.length()<=100000)
            for(name in names.keys())require(parents.has(name) && names.getString(name).length in 1..512)
            store.prefs.edit().putString("arcade-parents",parents.toString()).putString("arcade-names",names.toString()).apply()
        } catch(_:CloudNotFound) { /* Mantém o índice anterior e a proteção conservadora. */ }
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
