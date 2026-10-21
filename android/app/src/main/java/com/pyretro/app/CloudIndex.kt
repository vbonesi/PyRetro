package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import org.json.JSONArray
import org.json.JSONObject

data class CloudPlan(val code:String,val sources:JSONArray,val files:List<JSONObject>,val matches:Map<String,String>,val ambiguous:Int)

class CloudIndex(private val store:LibraryStore) {
    private val resolver=store.context.contentResolver
    fun sources(code:String)=JSONArray(store.prefs.getString("cloud-sources:$code","[]")!!)
    fun analyze(code:String,sources:JSONArray,catalog:List<Game>):CloudPlan {
        require(code in store.folders && sources.length() in 1..20000) { "Selecione arquivos ou uma pasta de origem primeiro (até 20 mil itens)." }
        val files=linkedMapOf<String,JSONObject>();var visited=0
        fun add(uri:Uri,name:String,size:Long) {
            if(store.accepts(code,name))files[uri.toString()]=JSONObject().put("uri",uri.toString()).put("name",name).put("size",size)
        }
        fun scan(root:Uri,document:String,depth:Int) {
            require(depth<=12) { "Pasta da nuvem com níveis demais." }
            val query=DocumentsContract.buildChildDocumentsUriUsingTree(root,document)
            resolver.query(query,arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE),null,null,null)?.use { c ->
                while(c.moveToNext()) {
                    require(++visited<=20000) { "Índice excede 20 mil itens. Escolha uma pasta menor." }
                    val name=c.getString(1);if(name.startsWith('.'))continue
                    val id=c.getString(0);val uri=DocumentsContract.buildDocumentUriUsingTree(root,id)
                    if(c.getString(2)==DocumentsContract.Document.MIME_TYPE_DIR)scan(root,id,depth+1)
                    else add(uri,name,if(c.isNull(3))-1 else c.getLong(3))
                }
            } ?: error("Provedor não disponibilizou esta pasta. Use a seleção de arquivos em lote.")
        }
        for(i in 0 until sources.length()) {
            val source=sources.getJSONObject(i);val uri=Uri.parse(source.getString("uri"))
            require(uri.scheme=="content")
            if(source.getBoolean("tree"))scan(uri,store.documentId(uri),0)
            else resolver.query(uri,arrayOf(OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE),null,null,null)?.use { c ->
                require(c.moveToFirst()) { "Arquivo indisponível. Índice anterior preservado." };add(uri,c.getString(0),if(c.isNull(1))-1 else c.getLong(1))
            } ?: error("Permissão indisponível. Selecione novamente a origem.")
        }
        val wanted=catalog.filter { it.code==code }.associate { game -> game.key to (game.aliases+game.name+GameLogic.fileLabel(game.romName.substringAfterLast('/'))).map(GameLogic::normalized).toSet() }
        val names=files.mapValues { it.value.getString("name") };val matches=CatalogRules.match(wanted,names)
        val ambiguous=wanted.count { (key,titles) -> key !in matches && names.values.any { GameLogic.normalized(GameLogic.fileLabel(it)) in titles } }
        return CloudPlan(code,sources,files.values.toList(),matches,ambiguous)
    }
    fun apply(plan:CloudPlan) {
        val edit=store.prefs.edit()
        // Apenas vínculos automáticos deste sistema: escolhas manuais prevalecem.
        for((key,value) in store.prefs.all.filterKeys { it.startsWith("cloud-auto:${plan.code}:") }) {
            val gameKey=key.removePrefix("cloud-auto:${plan.code}:")
            if(store.prefs.getString("cloud:$gameKey",null)==value)edit.remove("cloud:$gameKey")
            edit.remove(key)
        }
        fun bind(key:String,uri:String) {
            val current=store.prefs.getString("cloud:$key",null)
            val auto=store.prefs.getString("cloud-auto:${plan.code}:$key",null)
            if(current==null || current==auto)edit.putString("cloud:$key",uri).putString("cloud-auto:${plan.code}:$key",uri)
        }
        for((key,uri) in plan.matches)bind(key,uri)
        for(file in plan.files)bind(GameLogic.localKey("cloud-${plan.code}",file.getString("uri")),file.getString("uri"))
        edit.putString("cloud-sources:${plan.code}",plan.sources.toString()).putString("cloud-records:${plan.code}",JSONArray(plan.files).toString())
        require(edit.commit()) { "Não foi possível guardar o índice." }
    }
    fun extra(catalog:List<Game>):List<Game> {
        val linked=catalog.mapNotNull { store.prefs.getString("cloud:${it.key}",null) }.toSet()
        return store.folders.keys.flatMap { code ->
            val rows=JSONArray(store.prefs.getString("cloud-records:$code","[]")!!)
            (0 until rows.length()).map { rows.getJSONObject(it) }.filter { it.getString("uri") !in linked }.map { row ->
                Game("",GameLogic.localKey("cloud-$code",row.getString("uri")),GameLogic.fileLabel(row.getString("name")),store.folders.getValue(code),code,row.getString("name"))
            }
        }
    }
}
