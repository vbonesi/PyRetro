package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import org.json.JSONObject
import java.io.File
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID

data class SyncFile(val uri:Uri,val sha256:String,val size:Long,val modified:Long)
data class SyncRow(val path:String,val local:SyncFile?,val remote:JSONObject?,val kind:String,var choice:String=kind)
data class SyncPlan(val group:String,val rootTag:String,val identity:String,val rows:List<SyncRow>)

class FileSync(private val store:LibraryStore,preferenceName:String="file-sync") {
    private val resolver=store.context.contentResolver
    private val prefs=store.context.getSharedPreferences(preferenceName,0)
    private val limit=512L*1024*1024
    val groups=linkedMapOf("retro-saves" to "RetroArch · saves","retro-states" to "RetroArch · estados","retro-runtime" to "RetroArch · runtime","psp-saves" to "PPSSPP · saves","psp-states" to "PPSSPP · estados","3ds-saves" to "3DS · saves SDMC")
    fun tree(group:String):Uri? {
        prefs.getString("tree:$group",null)?.let { return Uri.parse(it) }
        val root=when {
            group.startsWith("retro-") -> prefs.getString("retroarch-tree",null)?.let(Uri::parse)
            group.startsWith("psp-") -> store.tree("PSP")
            group=="3ds-saves" -> store.tree("3DS")
            else -> null
        } ?: return null
        val suffix=when(group) { "retro-saves" -> "saves";"retro-states" -> "states";"retro-runtime" -> "playlists/logs";"psp-saves" -> "PSP/SAVEDATA";"psp-states" -> "PSP/PPSSPP_STATE";else -> "sdmc" }
        return DocumentsContract.buildDocumentUriUsingTree(root,store.documentId(root)+"/"+suffix)
    }
    fun setTree(group:String,uri:Uri) {
        require(group=="retroarch" || group in groups)
        require(uri.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local; o notebook é a outra ponta da sincronização." }
        prefs.edit().putString(if(group=="retroarch")"retroarch-tree" else "tree:$group",uri.toString()).apply()
    }
    fun lastResult()=prefs.getString("last-result","Ainda não sincronizado.")!!
    private fun hex(bytes:ByteArray)=bytes.joinToString("") { "%02x".format(it) }
    private fun sha(value:String)=hex(MessageDigest.getInstance("SHA-256").digest(value.toByteArray()))
    private fun fingerprint(uri:Uri):SyncFile {
        fun metadata():Pair<Long,Long> = resolver.query(uri,arrayOf(DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED),null,null,null)?.use { c -> require(c.moveToFirst()) { "Arquivo desapareceu." };c.getLong(0) to c.getLong(1) } ?: error("Sem permissão para ler o arquivo.")
        val before=metadata();require(before.first<=limit) { "Arquivo maior que 512 MB." }
        val digest=MessageDigest.getInstance("SHA-256");var total=0L
        resolver.openInputStream(uri).use { source -> requireNotNull(source);val buffer=ByteArray(1024*1024);while(true) { val n=source.read(buffer);if(n<0)break;total+=n;require(total<=limit);digest.update(buffer,0,n) } }
        require(metadata()==before && total==before.first) { "Arquivo mudou durante a leitura. Feche o emulador e analise novamente." }
        return SyncFile(uri,hex(digest.digest()),total,before.second)
    }
    private fun children(root:Uri,parent:Uri):Map<String,Uri> {
        val result=linkedMapOf<String,Uri>();val query=DocumentsContract.buildChildDocumentsUriUsingTree(root,store.documentId(parent))
        resolver.query(query,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_DOCUMENT_ID),null,null,null)?.use { c -> while(c.moveToNext()) { val name=c.getString(0);require(name !in result) { "Dois arquivos têm o mesmo nome; análise cancelada." };result[name]=DocumentsContract.buildDocumentUriUsingTree(root,c.getString(1)) } } ?: error("Selecione novamente a pasta: permissão indisponível.")
        return result
    }
    /** Pastas padrão podem ainda não existir; a análise nunca as cria. */
    private fun folder(group:String,create:Boolean):Uri? {
        val root=tree(group) ?: error("Escolha a pasta de ${groups[group]}.")
        require(root.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local no celular." }
        val granted=DocumentsContract.getTreeDocumentId(root);val target=store.documentId(root)
        require(target==granted || target.startsWith(granted+"/")) { "Destino fora da pasta concedida." }
        var current=DocumentsContract.buildDocumentUriUsingTree(root,granted)
        val parts=target.removePrefix(granted).trimStart('/').split('/').filter { it.isNotEmpty() }
        for(part in parts) {
            val found=children(root,current)[part]
            if(found!=null)current=found
            else {
                if(!create)return null
                current=DocumentsContract.createDocument(resolver,current,DocumentsContract.Document.MIME_TYPE_DIR,part) ?: error("Não foi possível criar a pasta do grupo.")
            }
        }
        return current
    }
    fun local(group:String):Map<String,SyncFile> {
        require(group in groups);val tree=tree(group) ?: error("Escolha a pasta de ${groups[group]}.");val result=linkedMapOf<String,SyncFile>()
        require(tree.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local no celular." }
        fun scan(parent:Uri,prefix:String,depth:Int) {
            require(depth<=16) { "Pasta com níveis demais." }
            val query=DocumentsContract.buildChildDocumentsUriUsingTree(tree,store.documentId(parent))
            resolver.query(query,arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE),null,null,null)?.use { c ->
                while(c.moveToNext()) {
                    val name=c.getString(1);if(name.startsWith(".pyretro-"))continue
                    val path=prefix+name;val uri=DocumentsContract.buildDocumentUriUsingTree(tree,c.getString(0))
                    if(c.getString(2)==DocumentsContract.Document.MIME_TYPE_DIR) {
                        if(group=="3ds-saves" && name in setOf("content","dbs","private"))continue
                        scan(uri,path+"/",depth+1)
                    } else if(SyncRules.accepted(group,path)) { require(result.size<20000);require(path !in result);result[path]=fingerprint(uri) }
                }
            } ?: error("Pasta indisponível: selecione-a novamente.")
        }
        folder(group,false)?.let { scan(it,"",0) };return result
    }
    fun analyze(group:String):SyncPlan {
        val tree=tree(group) ?: error("Selecione a pasta local primeiro.")
        val remote=JSONObject(store.request("/api/mobile/sync/manifest?group="+Uri.encode(group)))
        val tag=remote.getString("rootTag");val identity=sha(store.base()+"|"+group+"|"+tag+"|"+tree)
        val baseline=JSONObject(prefs.getString("baseline:$identity","{}")!!)
        val local=local(group);val other=linkedMapOf<String,JSONObject>();val array=remote.getJSONArray("files")
        for(i in 0 until array.length()) { val row=array.getJSONObject(i);val path=row.getString("path");require(SyncRules.accepted(group,path) && path !in other);other[path]=row }
        val rows=(local.keys+other.keys+baseline.keys().asSequence().toList()).sorted().map { path ->
            val left=local[path];val right=other[path];val previous=baseline.optString(path).takeIf { it.isNotBlank() }
            SyncRow(path,left,right,SyncRules.direction(left?.sha256,right?.getString("sha256"),previous))
        }
        return SyncPlan(group,tag,identity,rows)
    }
    private fun connection(path:String)= (URL(store.base()+path).openConnection() as HttpURLConnection).apply { connectTimeout=15000;readTimeout=600000;instanceFollowRedirects=false }
    private fun parameters(group:String,path:String)= "group="+Uri.encode(group)+"&path="+Uri.encode(path)
    private fun hash(file:File)=MessageDigest.getInstance("SHA-256").let { digest -> file.inputStream().use { input -> val buffer=ByteArray(1024*1024);while(true) { val n=input.read(buffer);if(n<0)break;digest.update(buffer,0,n) } };hex(digest.digest()) }
    private fun copyBounded(input:InputStream,output:java.io.OutputStream):Long {
        var total=0L;val buffer=ByteArray(1024*1024)
        while(true) { val n=input.read(buffer);if(n<0)break;total+=n;require(total<=limit);output.write(buffer,0,n) };return total
    }
    private fun upload(plan:SyncPlan,row:SyncRow) {
        val source=row.local ?: error("Sem versão local para enviar.")
        require(fingerprint(source.uri).sha256==source.sha256) { "Save local mudou depois da análise." }
        val temp=File.createTempFile("sync-send-",".tmp",store.context.cacheDir)
        try {
            resolver.openInputStream(source.uri).use { input -> requireNotNull(input);temp.outputStream().use { copyBounded(input,it) } };require(hash(temp)==source.sha256) { "Save mudou durante a cópia." }
            val query=parameters(plan.group,row.path)+"&rootTag="+plan.rootTag+"&expected="+(row.remote?.getString("sha256") ?: "-")+"&sha256="+source.sha256
            val token=JSONObject(store.request("/api/csrf")).getString("token");val conn=connection("/api/mobile/sync/file?"+query)
            try {
                conn.requestMethod="POST";conn.doOutput=true;conn.setFixedLengthStreamingMode(temp.length());conn.setRequestProperty("Content-Type","application/octet-stream");conn.setRequestProperty("X-PyRetro-CSRF",token)
                conn.outputStream.use { out -> temp.inputStream().use { it.copyTo(out,1024*1024) } }
                require(conn.responseCode==200) { "Notebook recusou: HTTP ${conn.responseCode}. Analise novamente; nenhuma versão local foi substituída." }
                val reply=JSONObject(conn.inputStream.bufferedReader().use { it.readText() });require(reply.getString("sha256")==source.sha256)
            } finally { conn.disconnect() }
        } finally { temp.delete() }
    }
    private fun parent(group:String,path:String):Pair<Uri,Uri> {
        val root=tree(group) ?: error("Pasta local indisponível.")
        require(root.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local no celular." }
        var current=folder(group,true) ?: error("Pasta local indisponível.")
        for(part in path.split('/').dropLast(1))current=children(root,current)[part] ?: DocumentsContract.createDocument(resolver,current,DocumentsContract.Document.MIME_TYPE_DIR,part) ?: error("Não foi possível criar a pasta do save.")
        return root to current
    }
    private fun download(plan:SyncPlan,row:SyncRow) {
        val source=row.remote ?: error("Sem versão no notebook.");val expected=source.getString("sha256")
        val temp=File.createTempFile("sync-get-",".tmp",store.context.cacheDir);val conn=connection("/api/mobile/sync/file?"+parameters(plan.group,row.path)+"&rootTag="+plan.rootTag+"&hash="+expected)
        try {
            require(conn.responseCode==200) { "Origem mudou no notebook: HTTP ${conn.responseCode}. Analise novamente." }
            val length=conn.inputStream.use { input -> temp.outputStream().use { copyBounded(input,it) } }
            require(length==source.getLong("size") && hash(temp)==expected) { "Transferência incompleta; save local preservado." }
            install(plan.group,row.path,temp,expected,row.local?.sha256)
        } finally { conn.disconnect();temp.delete() }
    }
    internal fun install(group:String,path:String,temp:File,expected:String,expectedLocal:String?) {
        require(SyncRules.accepted(group,path)) { "Arquivo não pertence ao grupo." }
        require(temp.length()<=limit && hash(temp)==expected) { "Checksum do arquivo recebido não confere." }
        val (root,parent)=parent(group,path);val name=path.substringAfterLast('/')
            val existing=children(root,parent)[name]
            require(existing?.let { fingerprint(it).sha256 }==expectedLocal) { "Save local mudou depois da análise." }
            val stage=DocumentsContract.createDocument(resolver,parent,"application/octet-stream",".pyretro-stage-${UUID.randomUUID()}") ?: error("Não foi possível preparar o save.")
            var previous:Uri?=null;var published=false
            try {
                resolver.openOutputStream(stage,"w").use { output -> requireNotNull(output);temp.inputStream().use { it.copyTo(output,1024*1024) } }
                require(fingerprint(stage).sha256==expected) { "Cópia local incompleta." }
                val latest=children(root,parent)[name]
                require(latest?.let { fingerprint(it).sha256 }==expectedLocal) { "Save mudou antes da conclusão." }
                if(latest!=null) {
                    previous=DocumentsContract.renameDocument(resolver,latest,".pyretro-previous-${System.currentTimeMillis()}-${UUID.randomUUID()}-$name") ?: error("Não foi possível preservar a versão anterior.")
                    require(fingerprint(previous).sha256==expectedLocal) { "Save mudou ao guardar a versão anterior." }
                }
                require(children(root,parent)[name]==null) { "Outro processo criou o save; versões preservadas." }
                val ready=DocumentsContract.renameDocument(resolver,stage,name) ?: error("Não foi possível concluir o save.")
                require(store.displayName(ready)==name && fingerprint(ready).sha256==expected) { "Destino mudou; confira as versões preservadas na pasta." };published=true
            } finally {
                if(!published) {
                    runCatching { DocumentsContract.deleteDocument(resolver,stage) }
                    if(previous!=null && children(root,parent)[name]==null)runCatching { DocumentsContract.renameDocument(resolver,previous,name) }
                }
            }
    }
    fun apply(plan:SyncPlan,progress:(String)->Unit):String {
        val fresh=JSONObject(store.request("/api/mobile/sync/manifest?group="+Uri.encode(plan.group)))
        require(fresh.getString("rootTag")==plan.rootTag) { "Pasta do notebook mudou. Analise novamente." }
        val identity=sha(store.base()+"|"+plan.group+"|"+plan.rootTag+"|"+tree(plan.group))
        require(identity==plan.identity) { "Pasta/endereço mudou. Analise novamente." }
        val baseline=JSONObject(prefs.getString("baseline:$identity","{}")!!);var sent=0;val errors=mutableListOf<String>();var ignored=0
        for(row in plan.rows) {
            try {
                when(row.choice) {
                    "upload" -> { progress("Enviando ${row.path}");upload(plan,row);baseline.put(row.path,row.local!!.sha256);sent++ }
                    "download" -> { progress("Recebendo ${row.path}");download(plan,row);baseline.put(row.path,row.remote!!.getString("sha256"));sent++ }
                    "same" -> { val hash=row.local?.sha256 ?: row.remote?.optString("sha256");if(hash!=null)baseline.put(row.path,hash) }
                    else -> ignored++
                }
                prefs.edit().putString("baseline:$identity",baseline.toString()).apply()
            } catch(error:Exception) { errors.add(row.path+": "+(error.message ?: "falha")) }
        }
        val result="$sent transferência(s) confirmada(s). $ignored conflito(s) adiado(s). ${errors.size} falha(s)."+if(errors.isEmpty())"" else "\n"+errors.take(30).joinToString("\n")
        prefs.edit().putString("last-result",result).apply();return result
    }
}
