package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.ZipInputStream
import java.util.zip.ZipFile

/** Pacotes ZIP locais funcionam offline; RAR/7z e catálogo são preparados pelo PC. */
class TextureStore(private val store:LibraryStore) {
    private val resolver=store.context.contentResolver
    private val limit=12L*1024*1024*1024
    private fun connection(path:String):HttpURLConnection=(URL(store.base()+path).openConnection() as HttpURLConnection).apply {
        connectTimeout=15000;readTimeout=600000;instanceFollowRedirects=false
    }
    fun catalog():org.json.JSONArray {
        val data=store.request("/api/mobile/textures")
        store.prefs.edit().putString("textures-catalog",data).apply();return org.json.JSONArray(data)
    }
    fun cached()=org.json.JSONArray(store.prefs.getString("textures-catalog","[]"))
    fun local(uri:Uri,code:String,id:String,progress:(String)->Unit):Int {
        if(!store.displayName(uri).endsWith(".zip",true)) {
            val token=upload(uri,progress)
            val prepared=prepare(JSONObject().put("upload",token).put("sistema",code).put("id_jogo",id),progress)
            try { return install(prepared.first,code,id,progress) } finally { prepared.first.delete() }
        }
        val archive=File.createTempFile("texture-local-",".zip",store.context.cacheDir)
        try {
            resolver.openInputStream(uri).use { input -> requireNotNull(input);archive.outputStream().use { output -> val buffer=ByteArray(65536);var total=0L;while(true){val n=input.read(buffer);if(n<0)break;total+=n;require(total<=limit);output.write(buffer,0,n)} } }
            return install(archive,code,id,progress)
        } finally { archive.delete() }
    }
    fun upload(uri:Uri,progress:(String)->Unit):String {
        val archive=File.createTempFile("texture-upload-",".tmp",store.context.cacheDir)
        try {
            resolver.openInputStream(uri).use { input -> requireNotNull(input);archive.outputStream().use { output -> val buffer=ByteArray(1024*1024);var size=0L;while(true) { val n=input.read(buffer);if(n<0)break;size+=n;require(size<=limit) { "Pacote maior que 12 GB." };output.write(buffer,0,n) } } }
            val name=store.displayName(uri);val token=JSONObject(store.request("/api/csrf")).getString("token")
            val conn=connection("/api/texturas/upload?filename="+Uri.encode(name))
            try {
                conn.requestMethod="POST";conn.doOutput=true;conn.setFixedLengthStreamingMode(archive.length());conn.setRequestProperty("X-PyRetro-CSRF",token);conn.setRequestProperty("Content-Type","application/octet-stream")
                progress("Enviando pacote ao notebook para preparar…");conn.outputStream.use { out -> archive.inputStream().use { it.copyTo(out,1024*1024) } }
                require(conn.responseCode==200) { "Falha ao enviar pacote: HTTP ${conn.responseCode}" }
                return JSONObject(conn.inputStream.bufferedReader().use { it.readText() }).getString("upload")
            } finally { conn.disconnect() }
        } finally { archive.delete() }
    }
    fun prepare(body:JSONObject,progress:(String)->Unit):Pair<File,JSONObject> {
        val job=JSONObject(store.request("/api/mobile/textures/prepare",body)).getString("job")
        val conn=connection("/api/fetch/stream?job="+Uri.encode(job));var result:JSONObject?=null
        try {
            require(conn.responseCode==200) { "Não foi possível acompanhar a preparação." }
            conn.inputStream.bufferedReader().useLines { lines -> lines.forEach { line ->
                if(line.startsWith("data:")) {
                    val event=JSONObject(line.substringAfter(':').trim())
                    when(event.optString("type")) {
                        "error" -> error(event.optString("message","Falha ao preparar pacote"))
                        "progress" -> progress(event.optString("status")+if(event.has("feito"))" · ${event.optLong("feito")/1024/1024} MB" else "")
                        "done" -> result=event.getJSONObject("result")
                    }
                }
            } }
        } finally { conn.disconnect() }
        val ready=result ?: error("Preparação não concluiu. Tente novamente.")
        val path=ready.getString("url");require(path.startsWith("/api/mobile/textures/bundle/"))
        val out=File.createTempFile("textures-",".zip",store.context.cacheDir);val download=connection(path)
        try {
            require(download.responseCode==200) { "Falha no download do pacote." }
            progress("Recebendo texturas do notebook…");download.inputStream.use { input -> out.outputStream().use { output -> val buffer=ByteArray(1024*1024);var total=0L;while(true) { val count=input.read(buffer);if(count<0)break;total+=count;require(total<=limit);output.write(buffer,0,count) } } }
            return out to ready
        } catch(error:Exception) { out.delete();throw error } finally { download.disconnect() }
    }
    fun install(zip:File,code:String,id:String,progress:(String)->Unit):Int {
        require(code in setOf("PSP","3DS")) { "Instalação nativa de texturas disponível em PSP e 3DS." }
        require(if(code=="PSP")Regex("[A-Z]{4}[0-9]{5}").matches(id) else Regex("[0-9A-F]{16}").matches(id)) { "ID do jogo inválido." }
        val tree=store.tree(code) ?: error("Escolha a pasta de $code em Opções primeiro.")
        require(tree.authority=="com.android.externalstorage.documents") { "Escolha a pasta local do emulador." }
        ZipFile(zip).use { archive -> require(archive.size() in 1..50000) { "Pacote vazio ou com arquivos demais." };val declared=archive.entries().asSequence().sumOf { it.size.coerceAtLeast(0) };require(declared<=limit) { "Pacote extraído grande demais." } }
        val staging=File(store.context.cacheDir,"textures-stage-"+UUID.randomUUID()).apply { mkdirs() }
        try {
            var total=0L;var count=0
            ZipInputStream(zip.inputStream().buffered()).use { input ->
                while(true) {
                    val entry=input.nextEntry ?: break
                    val name=entry.name.replace('\\','/');require(!name.startsWith('/') && name.split('/').none { it==".." } && !name.contains(':')) { "Caminho inseguro no pacote." }
                    if(entry.isDirectory)continue
                    require(++count<=50000) { "Arquivos demais no pacote." }
                    val out=File(staging,name);out.parentFile!!.mkdirs()
                    out.outputStream().use { output -> val buffer=ByteArray(65536);while(true) { val n=input.read(buffer);if(n<0)break;total+=n;require(total<=limit) { "Pacote extraído grande demais." };output.write(buffer,0,n) } }
                }
            }
            val root=staging.walkTopDown().maxDepth(5).firstOrNull { it.isDirectory && it.name.equals(id,true) } ?: staging
            val paths=root.walkTopDown().filter { it.isFile && it.extension.lowercase() in setOf("png","dds","ktx","ktx2","ini","txt") }.toList()
            require(paths.isNotEmpty()) { "Nenhuma textura encontrada." }
            val base=if(code=="PSP")listOf("PSP","TEXTURES",id) else listOf("load","textures",id)
            val dirs=mutableMapOf<String,Uri>("" to DocumentsContract.buildDocumentUriUsingTree(tree,store.documentId(tree)))
            fun children(parent:Uri):Map<String,Uri> {
                val result=mutableMapOf<String,Uri>();resolver.query(DocumentsContract.buildChildDocumentsUriUsingTree(tree,DocumentsContract.getDocumentId(parent)),arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME),null,null,null)?.use { cursor -> while(cursor.moveToNext())result[cursor.getString(1)]=DocumentsContract.buildDocumentUriUsingTree(tree,cursor.getString(0)) };return result
            }
            fun directory(parts:List<String>):Uri {
                var key="";var current=dirs.getValue("")
                for(part in parts) { key+="/$part";current=dirs.getOrPut(key) { children(current)[part] ?: DocumentsContract.createDocument(resolver,current,DocumentsContract.Document.MIME_TYPE_DIR,part) ?: error("Não foi possível criar pasta de texturas.") } };return current
            }
            fun hash(file:File)=MessageDigest.getInstance("SHA-256").let { digest -> file.inputStream().use { stream -> val buffer=ByteArray(65536);while(true){val n=stream.read(buffer);if(n<0)break;digest.update(buffer,0,n)} };digest.digest() }
            val plan=paths.map { file ->
                val parts=file.relativeTo(root).invariantSeparatorsPath.split('/');val parent=directory(base+parts.dropLast(1));val existing=children(parent)[parts.last()]
                if(existing!=null) {
                    val digest=MessageDigest.getInstance("SHA-256");resolver.openInputStream(existing).use { stream -> requireNotNull(stream);val buffer=ByteArray(65536);while(true){val n=stream.read(buffer);if(n<0)break;digest.update(buffer,0,n)} }
                    require(digest.digest().contentEquals(hash(file))) { "Já existe textura diferente: ${parts.last()}. Nenhum arquivo existente foi substituído." }
                }
                Triple(file,parent,existing)
            }
            var copied=0
            for((file,parent,existing) in plan)if(existing==null) {
                progress("Instalando texturas: ${copied+1}/${plan.size}")
                val tmp=DocumentsContract.createDocument(resolver,parent,"application/octet-stream",".pyretro-${UUID.randomUUID()}.part") ?: error("Falha ao criar textura.")
                try {
                    resolver.openOutputStream(tmp,"w").use { output -> requireNotNull(output);file.inputStream().use { it.copyTo(output) } }
                    require(children(parent)[file.name]==null) { "Destino mudou durante a cópia; arquivo existente preservado." }
                    DocumentsContract.renameDocument(resolver,tmp,file.name) ?: error("Falha ao concluir textura.");copied++
                } catch(error:Exception) { runCatching { DocumentsContract.deleteDocument(resolver,tmp) };throw error }
            }
            return copied
        } finally { staging.deleteRecursively() }
    }
}
