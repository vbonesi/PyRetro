package com.pyretro.app

import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.InputStream
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID

data class Game(val id:String, val key:String, val name:String, val platform:String, val code:String="",
    val romName:String="", val cover:String="", val genre:String="", val aliases:List<String> = emptyList(),
    val tracking:JSONObject=JSONObject(), val pcLocal:Boolean=false, var localUri:Uri?=null) {
    fun cache():JSONObject = JSONObject().put("id",id).put("key",key).put("name",name).put("platform",platform)
        .put("code",code).put("romName",romName).put("cover",cover).put("genre",genre).put("aliases",JSONArray(aliases))
        .put("tracking",tracking).put("local",pcLocal)
}
data class RomFile(val code:String,val name:String,val uri:Uri)

class LibraryStore(val context:Context,val preferenceName:String="pyretro") {
    companion object { const val COVER_CACHE_LIMIT=1500 }
    val prefs=context.getSharedPreferences(preferenceName,Context.MODE_PRIVATE)
    val folders=linkedMapOf("NDS" to "Nintendo DS", "3DS" to "Nintendo 3DS", "PS" to "PlayStation", "PSP" to "PSP",
        "FC" to "NES", "SFC" to "Super Nintendo", "GB" to "Game Boy", "GBC" to "Game Boy Color", "GBA" to "Game Boy Advance",
        "MD" to "Mega Drive", "SMS" to "Master System", "GG" to "Game Gear", "N64" to "Nintendo 64", "PCE" to "PC Engine", "PCECD" to "PC Engine CD", "ARCADE" to "Arcade")
    private val extensions=mapOf("NDS" to setOf("nds","zip","7z"),"3DS" to setOf("3ds","cci","cxi","app"),
        "PS" to setOf("chd","pbp","cue","m3u"),"PSP" to setOf("iso","cso","chd","pbp"),
        "FC" to setOf("nes","zip"),"SFC" to setOf("sfc","smc","zip"),"GB" to setOf("gb","zip"),
        "GBC" to setOf("gbc","zip"),"GBA" to setOf("gba","zip"),"MD" to setOf("md","gen","zip"),
        "SMS" to setOf("sms","zip"),"GG" to setOf("gg","zip"),"N64" to setOf("n64","z64","v64","zip"),"PCE" to setOf("pce","zip"),"PCECD" to setOf("chd","cue","m3u"),"ARCADE" to setOf("zip","7z"))
    @Volatile var online=false
    private var csrf=""
    fun base():String=prefs.getString("server","")!!.trimEnd('/')
    fun setBase(value:String) {
        if(value.isNotBlank()) { val url=URL(value); require(url.protocol=="https" && url.host.isNotEmpty() && url.userInfo==null && url.ref==null) { "Use o endereço HTTPS do PyRetro, sem senha na URL." } }
        val normalized=value.trim().trimEnd('/');val changed=normalized!=base()
        val edit=prefs.edit().putString("server",normalized)
        if(changed) {
            listOf("last-contact","last-attempt","last-attempt-ok","tracking-sync-at","tracking-sync-result").forEach(edit::remove)
            prefs.all.keys.filter { it.startsWith("conflict:") }.forEach(edit::remove)
        }
        edit.apply();csrf="";online=false
    }
    private fun contact(server:String,success:Boolean) {
        if(base()!=server)return
        val now=System.currentTimeMillis();val edit=prefs.edit().putLong("last-attempt",now).putBoolean("last-attempt-ok",success)
        if(success)edit.putLong("last-contact",now)
        edit.apply();online=success
    }
    fun checkConnection() {
        val server=base()
        try {
            require(JSONObject(request("/api/csrf",recordContact=false)).optString("token").isNotBlank()) { "O endereço não respondeu como servidor PyRetro." }
            contact(server,true)
        }
        catch(error:Exception) { contact(server,false);throw error }
    }
    /** Sondagem silenciosa: só atualiza [online] em memória, sem gravar registros de contato
     *  (esses ficam para o teste explícito da central). */
    fun probe():Boolean {
        val server=base();if(server.isBlank())return false
        val ok=runCatching { JSONObject(request("/api/csrf",recordContact=false)).optString("token").isNotBlank() }.getOrDefault(false)
        if(base()==server)online=ok
        return ok
    }
    fun request(path:String,body:JSONObject?=null,recordContact:Boolean=true):String {
        require(base().isNotBlank()) { "Configure o endereço HTTPS do notebook. O modo offline continua disponível." }
        val server=base()
        fun send(token:String):Pair<Int,String> {
            val connection=URL(server+path).openConnection() as HttpURLConnection
            connection.connectTimeout=15000;connection.readTimeout=60000;connection.instanceFollowRedirects=false
            try {
                if(body!=null) { connection.requestMethod="POST";connection.doOutput=true;connection.setRequestProperty("Content-Type","application/json");connection.setRequestProperty("X-PyRetro-CSRF",token);connection.outputStream.use { it.write(body.toString().toByteArray()) } }
                val status=connection.responseCode
                val input=if(status in 200..299)connection.inputStream else connection.errorStream
                val bytes=input?.use { bounded(it,20*1024*1024) } ?: byteArrayOf()
                return status to bytes.toString(Charsets.UTF_8)
            } catch(error:Exception) { if(recordContact)contact(server,false);throw error } finally { connection.disconnect() }
        }
        if(body!=null && csrf.isEmpty())csrf=JSONObject(request("/api/csrf")).getString("token")
        var result=send(csrf)
        if(body!=null && result.first==403) { csrf=JSONObject(request("/api/csrf")).getString("token");result=send(csrf) }
        if(recordContact)contact(server,result.first in 200..299)
        require(result.first in 200..299) { runCatching { JSONObject(result.second).optString("error","Falha HTTP ${result.first}") }.getOrDefault("Falha HTTP ${result.first}") }
        return result.second
    }
    fun parse(array:JSONArray):List<Game> = (0 until array.length()).map { i ->
        val row=array.getJSONObject(i);val source=row.optJSONObject("tracking") ?: JSONObject()
        val tracking=JSONObject();for(field in listOf("iniciado","finalizado","platinado"))tracking.put(field,source.optBoolean(field))
        if(source.has("nota"))tracking.put("nota",source.opt("nota"))
        val aliases=row.optJSONArray("aliases") ?: source.optJSONArray("nomes_alt") ?: JSONArray()
        val id=if(row.isNull("id"))"" else row.optString("id")
        Game(id,row.getString("key"),row.getString("name"),row.getString("platform"),row.optString("mobileCode",row.optString("code")),
            row.optString("romName",row.getString("name")),row.optString("cover").takeUnless { it=="null" } ?: "",row.optString("genre",source.optString("genero")),
            (0 until aliases.length()).map { aliases.getString(it) },tracking,row.optBoolean("local"))
    }
    fun cached():List<Game> = runCatching { parse(JSONArray(File(context.filesDir,"catalog.json").readText())) }.getOrDefault(emptyList())
    fun refresh():List<Game> {
        val games=parse(JSONArray(request("/api/tv/catalog")))
        saveCatalog(games)
        prefs.edit().putLong("updated",System.currentTimeMillis()).apply();online=true;return games
    }
    private fun saveCatalog(games:List<Game>) {
        val temporary=File(context.filesDir,"catalog.tmp");temporary.writeText(JSONArray(games.map { it.cache() }).toString())
        require(temporary.renameTo(File(context.filesDir,"catalog.json"))) { "Falha ao guardar catálogo." }
    }
    fun extensionsFor(code:String)=extensions[code] ?: emptySet()
    fun accepts(code:String,name:String):Boolean=name.substringAfterLast('.').lowercase() in (extensions[code] ?: emptySet())
    fun tree(code:String):Uri? {
        prefs.getString("tree:$code",null)?.let { return Uri.parse(it) }
        val root=prefs.getString("tree:ROOT",null)?.let(Uri::parse) ?: return null
        return DocumentsContract.buildDocumentUriUsingTree(root,documentId(root)+"/"+code)
    }
    fun documentId(uri:Uri):String = if(DocumentsContract.isDocumentUri(context,uri))DocumentsContract.getDocumentId(uri) else DocumentsContract.getTreeDocumentId(uri)
    fun saveTree(code:String,uri:Uri) { prefs.edit().putString("tree:$code",uri.toString()).apply() }
    fun files(code:String,strict:Boolean=false):List<RomFile> {
        val root=tree(code) ?: if(strict)error("Selecione a pasta de ROMs.") else return emptyList();val result=mutableListOf<RomFile>();var visited=0
        fun scan(document:String,depth:Int) {
            if(strict)require(depth<=16 && result.size<20000) { "Pasta excede os limites da análise." } else if(depth>2 || result.size>=20000)return
            val children=DocumentsContract.buildChildDocumentsUriUsingTree(root,document)
            context.contentResolver.query(children,arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE),null,null,null)?.use { cursor ->
                while(cursor.moveToNext()) {
                    if(strict)require(result.size<20000 && ++visited<=50000) { "Pasta excede os limites da análise." } else if(result.size>=20000)return
                    val id=cursor.getString(0);val name=cursor.getString(1)
                    if(cursor.getString(2)==DocumentsContract.Document.MIME_TYPE_DIR)scan(id,depth+1)
                    else if(accepts(code,name) && (cursor.isNull(3) || cursor.getLong(3)>0))result.add(RomFile(code,name,DocumentsContract.buildDocumentUriUsingTree(root,id)))
                }
            } ?: if(strict)error("Pasta indisponível; selecione novamente a concessão.") else Unit
        }
        if(strict)require(SafStorage(this).folder(root,false)!=null) { "Pasta de ROMs indisponível." }
        scan(documentId(root),0);return result
    }
    fun bind(catalog:List<Game>,roms:List<RomFile>):List<Game> {
        val games=(catalog+CloudIndex(this).extra(catalog)).map { it.copy(localUri=null) }.toMutableList();val used=mutableSetOf<Uri>()
        val matches=games.associate { game ->
            val available=roms.filter { it.code==game.code }
            val wanted=(game.aliases+game.name+GameLogic.fileLabel(game.romName.substringAfterLast('/'))).map(GameLogic::normalized).toSet()
            game.key to available.filter { rom -> GameLogic.normalized(GameLogic.fileLabel(rom.name)) in wanted }
        }
        val owners=matches.values.flatten().groupingBy { it.uri }.eachCount()
        for(game in games) {
            val pinned=prefs.getString("rom:${game.key}",null)
            game.localUri=(if(pinned!=null)Uri.parse(pinned).takeIf(::localReadable) else null) ?: matches[game.key]?.singleOrNull()?.takeIf { owners[it.uri]==1 }?.uri
            game.localUri?.let(used::add)
        }
        for(rom in roms.filter { it.uri !in used })games.add(Game("",GameLogic.localKey(rom.code,rom.uri.toString()),GameLogic.fileLabel(rom.name),folders[rom.code] ?: rom.code,rom.code,rom.name,localUri=rom.uri))
        return games.sortedBy { it.name.lowercase() }
    }
    private fun localReadable(uri:Uri):Boolean = uri.authority=="com.android.externalstorage.documents" && runCatching {
        context.contentResolver.query(uri,arrayOf(OpenableColumns.SIZE),null,null,null)?.use { it.moveToFirst() && (it.isNull(0) || it.getLong(0)>0) } ?: false
    }.getOrDefault(false)
    fun displayName(uri:Uri):String=context.contentResolver.query(uri,arrayOf(OpenableColumns.DISPLAY_NAME),null,null,null)?.use { if(it.moveToFirst())it.getString(0) else "ROM" } ?: "ROM"
    fun removeLocal(game:Game,expected:RomStamp?=null) {
        val uri=game.localUri ?: error("Este jogo não tem ROM no celular.")
        require(uri.authority=="com.android.externalstorage.documents") { "Somente a cópia local pode ser removida." }
        val name=displayName(uri)
        require(accepts(game.code,name) && name.substringAfterLast('.').lowercase() !in setOf("cue","m3u")) { "CUE/M3U têm arquivos associados. Remova o conjunto pelo gerenciador do notebook, após conferir as faixas/discos." }
        require(files(game.code).any { documentId(it.uri)==documentId(uri) }) { "Arquivo fora da pasta local escolhida. Nenhum arquivo foi removido." }
        require(!DownloadQueue.get(this).contains(game.key)) { "Retire este jogo da fila de downloads antes de remover a ROM." }
        synchronized(SpaceStore.mutationLock) {
            require(!SpaceStore(this).pinned(game)) { "Jogo fixado para manter baixado. Desfixe antes de remover a ROM." }
            if(expected!=null)require(SpaceStore(this).stamp(uri)==expected) { "ROM mudou desde a análise. Atualize a lista antes de remover." }
            require(DocumentsContract.deleteDocument(context.contentResolver,uri)) { "Não foi possível remover a ROM." }
        }
        prefs.edit().remove("rom:${game.key}").apply();game.localUri=null
    }
    fun download(game:Game,progress:(Long)->Unit):Uri = DownloadStore(this).download(game,progress=progress)
    fun tracking(game:Game):JSONObject {
        val value=JSONObject(game.tracking.toString());val queued=prefs.getString("pending:${game.key}",null)?.let(::JSONObject)?.optJSONObject("campos")
        queued?.keys()?.forEach { value.put(it,queued.opt(it)) };return value
    }
    fun setProgress(game:Game,field:String,value:Boolean) {
        val stored=prefs.getString("pending:${game.key}",null)?.let(::JSONObject) ?: JSONObject().put("key",game.key).put("id",game.id).put("campos",JSONObject()).put("base",JSONObject())
        val fields=stored.getJSONObject("campos");val base=stored.getJSONObject("base")
        for((name,state) in GameLogic.progress(field,value)) { if(!base.has(name))base.put(name,game.tracking.optBoolean(name));fields.put(name,state) }
        val edit=prefs.edit()
        if(fields.keys().asSequence().all { fields.optBoolean(it)==base.optBoolean(it) })edit.remove("pending:${game.key}")
        else edit.putString("pending:${game.key}",stored.toString())
        edit.apply()
    }
    fun addTime(game:Game,minutes:Int) {
        val event=UUID.randomUUID().toString();val value=JSONObject().put("key",game.key).put("minutes",minutes).put("event",event)
        prefs.edit().putLong("time:${game.key}",prefs.getLong("time:${game.key}",0)+minutes*60L).putString("time-event:$event",value.toString()).apply()
    }
    fun pending():Int=prefs.all.keys.count { it.startsWith("pending:") || it.startsWith("time-event:") }
    fun synchronize():String {
        val fresh=refresh().associateBy { it.key };var sent=0;var conflicts=0
        fun conflict(key:String,raw:String) { conflicts++;prefs.edit().putString("conflict:$key",raw).apply() }
        // O catálogo é regravado mesmo se a rede cair no meio: o que já foi enviado sai das
        // pendências e precisa aparecer no cache, senão o offline mostraria o estado antigo.
        try {
            for((key,raw) in prefs.all.filter { it.key.startsWith("pending:") || it.key.startsWith("time-event:") }) {
                val payload=JSONObject(raw as String);val game=fresh[payload.getString("key")]
                if(game==null) { conflict(key,raw);continue }
                try {
                    if(key.startsWith("pending:")) {
                        val fields=payload.getJSONObject("campos");val baseline=payload.getJSONObject("base")
                        if(fields.keys().asSequence().any { field -> game.tracking.optBoolean(field)!=baseline.optBoolean(field) && game.tracking.optBoolean(field)!=fields.optBoolean(field) }) { conflict(key,raw);continue }
                        if(game.id.isBlank()) { conflict(key,raw);continue }
                        request("/api/library/edit",JSONObject().put("id",game.id).put("campos",fields).put("expected",baseline))
                        fields.keys().forEach { field -> game.tracking.put(field,fields.get(field)) }
                    } else request("/api/tv/playtime",payload)
                } catch(rejected:IllegalArgumentException) { conflict(key,raw);continue } // recusa HTTP (409/400): preserva e segue
                if(prefs.getString(key,null)==raw)prefs.edit().remove(key).remove("conflict:$key").apply();sent++
            }
        } finally { saveCatalog(fresh.values.toList()) }
        val result="$sent atualização(ões) enviada(s). $conflicts pendência(s) preservada(s) para conferir no notebook."
        prefs.edit().putLong("tracking-sync-at",System.currentTimeMillis()).putString("tracking-sync-result",result).apply()
        return result
    }
    fun cover(game:Game):File? {
        if(game.cover.isBlank() || !game.cover.startsWith('/'))return null
        val url=base()+game.cover
        // Chave só pelo caminho (com ?v=mtime): trocar LAN ↔ Tailscale não esvazia o cache offline.
        val name=MessageDigest.getInstance("SHA-256").digest(game.cover.toByteArray()).joinToString("") { "%02x".format(it) }
        val directory=File(context.cacheDir,"covers").apply { mkdirs() };val file=File(directory,name)
        if(file.exists()) { file.setLastModified(System.currentTimeMillis());return file }
        if(!online || base().isBlank())return null
        val connection=URL(url).openConnection() as HttpURLConnection;connection.connectTimeout=10000;connection.readTimeout=15000;connection.instanceFollowRedirects=false
        try {
            require(connection.responseCode==200)
            val bytes=connection.inputStream.use { bounded(it,8*1024*1024) }
            val tmp=File.createTempFile("cover-",".tmp",directory);tmp.writeBytes(bytes)
            if(!tmp.renameTo(file)) { tmp.delete();return null }
            directory.listFiles()?.sortedBy { it.lastModified() }?.dropLast(COVER_CACHE_LIMIT)?.forEach { it.delete() }
            return file
        } finally { connection.disconnect() }
    }
    private fun bounded(input:InputStream,limit:Int):ByteArray {
        val out=ByteArrayOutputStream();val buffer=ByteArray(65536)
        while(true) { val count=input.read(buffer);if(count<0)break;require(out.size()+count<=limit) { "Resposta grande demais." };out.write(buffer,0,count) }
        return out.toByteArray()
    }
}
