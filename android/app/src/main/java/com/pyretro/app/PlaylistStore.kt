package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

data class PlaylistPlan(val code:String,val root:Uri,val romTree:String,val name:String,val expected:String?,val json:String,val paths:Set<String>,val added:Int,val removed:Int)

data class PlaylistVersion(val root:Uri,val name:String,val file:SyncFile,val current:String?,val created:Long)

class PlaylistStore(private val store:LibraryStore) {
    private val storage=SafStorage(store)
    val names=linkedMapOf("FC" to "Nintendo - Nintendo Entertainment System","SFC" to "Nintendo - Super Nintendo Entertainment System","GB" to "Nintendo - Game Boy","GBC" to "Nintendo - Game Boy Color","GBA" to "Nintendo - Game Boy Advance","N64" to "Nintendo - Nintendo 64","NDS" to "Nintendo - Nintendo DS","MD" to "Sega - Mega Drive - Genesis","SMS" to "Sega - Master System - Mark III","GG" to "Sega - Game Gear","PCE" to "NEC - PC Engine - TurboGrafx 16","PCECD" to "NEC - PC Engine CD - TurboGrafx-CD","ARCADE" to "FBNeo - Arcade Games","PS" to "Sony - PlayStation")
    private fun root():Uri {
        val tree=FileSync(store).retroarchTree() ?: error("Escolha a pasta RetroArch em Saves, estados e runtime primeiro.")
        return DocumentsContract.buildDocumentUriUsingTree(tree,store.documentId(tree)+"/playlists")
    }
    private fun paths(code:String)=store.files(code,true).associateBy { PlaylistRules.path(store.documentId(it.uri)) }
    fun plan(code:String):PlaylistPlan {
        require(code in names)
        val root=root();val name=names.getValue(code)+".lpl";val folder=storage.folder(root,false)
        val current=folder?.let { storage.children(root,it)[name] };val info=current?.let(storage::fingerprint)
        require(info==null || info.size<=8*1024*1024) { "Playlist maior que 8 MB." }
        val old=current?.let { val bytes=storage.read(it,8L*1024*1024);require(storage.hash(bytes)==info!!.sha256) { "Playlist mudou durante a leitura; analise novamente." };JSONObject(bytes.toString(Charsets.UTF_8)) } ?: JSONObject().put("version","1.5").put("default_core_path","").put("default_core_name","")
        val entries=old.optJSONArray("items") ?: if(current==null)JSONArray() else error("Formato de playlist não suportado; arquivo preservado.")
        require(entries.length()<=20000)
        val local=paths(code);val romTree=store.tree(code) ?: error("Escolha a pasta de ROMs.")
        val prefix=PlaylistRules.path(store.documentId(romTree));val original=(0 until entries.length()).map { entries.getJSONObject(it) }
        val removed=PlaylistRules.removed(original.map { it.getString("path") },local.keys,prefix,store.extensionsFor(code))
        val kept=original.filter { it.getString("path") !in removed };val known=kept.map { it.getString("path") }.toSet();val output=JSONArray(kept)
        for((path,rom) in local)if(path !in known)output.put(JSONObject().put("path",path).put("label",GameLogic.fileLabel(rom.name)).put("core_path","DETECT").put("core_name","DETECT").put("crc32","00000000|crc").put("db_name",name))
        old.put("items",output)
        return PlaylistPlan(code,root,romTree.toString(),name,info?.sha256,old.toString(2),local.keys,local.keys.count { it !in known },removed.size)
    }
    fun apply(plan:PlaylistPlan,automatic:Boolean) {
        require(root()==plan.root && store.tree(plan.code).toString()==plan.romTree) { "Pastas mudaram; analise novamente." }
        require(paths(plan.code).keys==plan.paths) { "ROMs locais mudaram; analise novamente." }
        val temp=File.createTempFile("playlist-",".tmp",store.context.cacheDir)
        try {
            temp.writeText(plan.json)
            storage.publish(plan.root,storage.folder(plan.root,true)!!,plan.name,temp,storage.hash(temp),plan.expected)
            store.prefs.edit().putBoolean("playlist-auto:${plan.code}",automatic).putString("playlist-root:${plan.code}",plan.root.toString()+"|"+plan.romTree).putString("playlist-last","${plan.name}: ${plan.paths.size} ROMs locais conferidas.").apply()
        } finally { temp.delete() }
    }
    fun versions(code:String):List<PlaylistVersion> {
        val root=root();val folder=storage.folder(root,false) ?: return emptyList();val name=names.getValue(code)+".lpl"
        val files=storage.children(root,folder);val current=files[name]?.let(storage::fingerprint)?.sha256
        val pattern=Regex("\\.pyretro-previous-([0-9]+)-[0-9a-f-]{36}-"+Regex.escape(name))
        return files.mapNotNull { (label,uri) -> pattern.matchEntire(label)?.let { PlaylistVersion(root,name,storage.fingerprint(uri),current,it.groupValues[1].toLong()) } }.sortedByDescending { it.created }
    }
    fun restore(version:PlaylistVersion,code:String) {
        require(root()==version.root && version.name==names.getValue(code)+".lpl") { "Pasta mudou; abra novamente o histórico." }
        val temp=File.createTempFile("playlist-restore-",".tmp",store.context.cacheDir)
        try {
            require(version.file.size<=8*1024*1024)
            store.context.contentResolver.openInputStream(version.file.uri)!!.use { input -> temp.outputStream().use { output -> val buffer=ByteArray(65536);var count=0L;while(true) { val n=input.read(buffer);if(n<0)break;count+=n;require(count<=8*1024*1024);output.write(buffer,0,n) } } }
            storage.publish(version.root,storage.folder(version.root,false)!!,version.name,temp,version.file.sha256,version.current)
            store.prefs.edit().putBoolean("playlist-auto:$code",false).putString("playlist-last","Playlist restaurada; atualização automática desativada até nova análise.").apply()
        } finally { temp.delete() }
    }
    fun afterChange(code:String):String {
        if(!store.prefs.getBoolean("playlist-auto:$code",false))return ""
        return runCatching {
            val plan=plan(code)
            require(store.prefs.getString("playlist-root:$code",null)==plan.root.toString()+"|"+plan.romTree) { "Pastas mudaram: reative a atualização de playlists." }
            apply(plan,true);"Playlist atualizada."
        }.getOrElse { val message="ROM atualizada; playlist pendente: "+it.message;store.prefs.edit().putString("playlist-last",message).apply();message }
    }
}
