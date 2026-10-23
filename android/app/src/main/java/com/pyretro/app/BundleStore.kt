package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import org.json.JSONObject
import java.io.File
import java.net.URLDecoder
import java.net.URLEncoder
import java.security.MessageDigest

/** Arquivo de um conjunto de discos (contrato `docs/mobile-rom-bundles.md`, versão 1). */
data class BundleMember(val file:String,val size:Long,val etag:String,val descriptor:Boolean)
/** Conjunto vinculado ao jogo: `pyretro-bundle:<código>/<entry>?id=…&size=…` em `cloud:<chave>`. */
data class BundleRef(val code:String,val entry:String,val id:String,val size:Long) {
    fun encoded()="${BundleRules.PREFIX}${enc(code)}/${enc(entry)}?id=${enc(id)}&size=$size"
    private fun enc(value:String)=URLEncoder.encode(value,"UTF-8")
}

/** Regras sem Android: origem guardada, caminhos seguros e ordem de publicação. */
object BundleRules {
    const val PREFIX="pyretro-bundle:"
    val DESCRIPTORS=setOf("cue","m3u","gdi")
    fun isDescriptor(name:String)=name.substringAfterLast('.').lowercase() in DESCRIPTORS
    /** Caminho relativo à pasta do sistema, sem `..`, barras invertidas ou partes vazias. */
    fun safe(path:String)=path.isNotBlank() && !path.contains('\\') && !path.startsWith('/') && path.split('/').none { it.isEmpty() || it=="." || it==".." }
    fun parse(value:String?):BundleRef? {
        if(value==null || !value.startsWith(PREFIX))return null
        return runCatching {
            val body=value.removePrefix(PREFIX);val path=body.substringBefore('?')
            val query=body.substringAfter('?',"").split('&').filter { it.contains('=') }.associate { it.substringBefore('=') to dec(it.substringAfter('=')) }
            val code=dec(path.substringBefore('/'));val entry=dec(path.substringAfter('/',""))
            require(code.isNotEmpty() && safe(entry) && isDescriptor(entry))
            BundleRef(code,entry,query.getValue("id").also { require(it.matches(Regex("[0-9a-f]{64}"))) },query.getValue("size").toLong().also { require(it>0) })
        }.getOrNull()
    }
    /** Dependências primeiro, descritores depois e o `entry` por último: o emulador nunca vê um
     *  descritor apontando para faixa que ainda não chegou. */
    fun publishOrder(members:List<BundleMember>,entry:String):List<BundleMember> {
        require(members.all { safe(it.file) } && members.map { it.file }.distinct().size==members.size) { "Conjunto com caminho inválido ou repetido." }
        require(members.count { it.file==entry }==1) { "O conjunto não traz o arquivo principal." }
        return members.filter { !it.descriptor }+members.filter { it.descriptor && it.file!=entry }+members.filter { it.file==entry }
    }
    private fun dec(value:String)=URLDecoder.decode(value,"UTF-8")
    /** Referências de um descritor, como `core/rom_bundles.references` (CUE FILE, M3U, GDI). */
    fun references(text:String,extension:String):List<String> {
        require(text.toByteArray().size<=1024*1024) { "Descritor grande demais." }
        val lines=text.removePrefix("\uFEFF").lines()
        val refs=when(extension.lowercase()) {
            "cue" -> lines.filter { Regex("^\\s*FILE\\s",RegexOption.IGNORE_CASE).containsMatchIn(it) }.map { line ->
                val m=Regex("^\\s*FILE\\s+(?:\"([^\"]*)\"|(\\S+))\\s+\\S+\\s*$",RegexOption.IGNORE_CASE).find(line) ?: throw IllegalArgumentException("Referência FILE inválida no CUE.")
                m.groupValues[1].ifEmpty { m.groupValues[2] } }
            "m3u" -> lines.map { it.trim() }.filter { it.isNotEmpty() && !it.startsWith("#") }
            "gdi" -> { val rows=lines.filter { it.isNotBlank() };val count=rows.firstOrNull()?.trim()?.toIntOrNull() ?: throw IllegalArgumentException("GDI inválido.")
                rows.drop(1).map { line -> val m=Regex("^\\s*\\d+\\s+\\d+\\s+\\d+\\s+\\d+\\s+(?:\"([^\"]*)\"|(\\S+))\\s+-?\\d+\\s*$").find(line) ?: throw IllegalArgumentException("Faixa GDI inválida.")
                    m.groupValues[1].ifEmpty { m.groupValues[2] } }.also { require(it.size==count) { "Número de faixas GDI inválido." } } }
            else -> emptyList()
        }
        require(refs.isNotEmpty()) { "Descritor sem arquivos associados." }
        require(refs.all(::safe)) { "Referência de disco inválida." }
        return refs.distinct()
    }
    private fun join(parent:String,ref:String)=(if(parent.isEmpty())ref else "$parent/$ref").split('/').fold(mutableListOf<String>()) { acc,part -> if(part=="..") { require(acc.isNotEmpty()) { "Referência fora da pasta do sistema." };acc.removeAt(acc.size-1) } else acc.add(part);acc }.joinToString("/")
    /** Arquivos de um conjunto que existem na pasta (o próprio descritor incluso). `read` devolve o texto
     *  de um descritor ou falha; ciclo e profundidade acima de 16 são erro. */
    fun members(entry:String,exists:(String)->Boolean,read:(String)->String):Set<String> {
        val out=linkedSetOf<String>()
        fun visit(path:String,depth:Int,active:Set<String>) {
            require(depth<=16 && path !in active) { "Referência circular ou funda demais." }
            if(path in out || !exists(path))return
            out.add(path)
            if(isDescriptor(path))for(ref in references(read(path),path.substringAfterLast('.')))visit(join(path.substringBeforeLast('/',""),ref),depth+1,active+path)
        }
        visit(entry,0,emptySet());return out
    }
    /** Prévia de remoção no celular: o que é só deste conjunto sai; o que outro descritor da pasta usa
     *  fica. Descritor ilegível em qualquer lugar = não dá para provar exclusividade, nada sai. */
    fun removalPlan(entry:String,inventory:Set<String>,read:(String)->String):BundleRemoval {
        val mine=members(entry,{ it in inventory },read)
        val protected=mutableSetOf<String>();var complete=true
        for(other in inventory.filter { isDescriptor(it) && it !in mine })
            runCatching { members(other,{ it in inventory },read) }.onSuccess { protected.addAll(it intersect mine) }.onFailure { complete=false }
        if(!complete)protected.addAll(mine)
        // Ordem de exclusão: principal primeiro, depois outros descritores, por fim as faixas.
        val remove=(mine-protected).sortedWith(compareBy({ it!=entry },{ !isDescriptor(it) },{ it }))
        return BundleRemoval(remove,(mine intersect protected).sorted(),complete)
    }
}
data class BundleRemoval(val remove:List<String>,val preserve:List<String>,val complete:Boolean)

/** Download de um conjunto pelo notebook: cada arquivo para uma área privada (com retomada),
 *  tamanho conferido, colisões verificadas em todos os destinos antes de publicar qualquer um,
 *  e publicação na ordem de [BundleRules.publishOrder]. Nada existente é substituído. */
class BundleStore(private val store:LibraryStore,private val storage:SafStorage) {
    private fun enc(value:String)=URLEncoder.encode(value,"UTF-8")
    fun manifest(code:String,entry:String):Pair<String,List<BundleMember>> {
        val data=JSONObject(store.request("/api/mobile/rom/bundle?code=${enc(code)}&entry=${enc(entry)}"))
        require(data.optInt("version")==1) { "Versão de conjunto desconhecida; atualize o app." }
        val files=data.getJSONArray("files")
        return data.getString("id") to (0 until files.length()).map { files.getJSONObject(it) }.map { BundleMember(it.getString("file"),it.getLong("size"),it.getString("etag"),it.optBoolean("descriptor")) }
    }
    private fun dir(key:String)=File(store.context.filesDir,"bundles/"+MessageDigest.getInstance("SHA-256").digest(key.toByteArray()).joinToString("") { "%02x".format(it) }).apply { mkdirs() }
    fun discard(key:String) { dir(key).deleteRecursively() }
    fun partialBytes(key:String)=dir(key).listFiles().orEmpty().sumOf { it.length() }
    private fun fetch(ref:BundleRef,member:BundleMember,file:File,stop:()->Boolean,progress:(Long)->Unit):String {
        val offset=file.length()
        if(offset==member.size)return ResumableCopy.copy(java.io.ByteArrayInputStream(ByteArray(0)),file,member.size,cancelled=stop,progress=progress,resumed=true)
        val url=store.base()+"/api/mobile/rom/file?code=${enc(ref.code)}&entry=${enc(ref.entry)}&bundle=${enc(ref.id)}&file=${enc(member.file)}&etag=${enc(member.etag)}"
        val connection=java.net.URL(url).openConnection() as java.net.HttpURLConnection
        connection.connectTimeout=15000;connection.readTimeout=120000;connection.instanceFollowRedirects=false
        if(offset>0)connection.setRequestProperty("Range","bytes=$offset-")
        try {
            val status=try { connection.responseCode } catch(error:java.io.IOException) { throw java.io.IOException("Notebook indisponível. Ligue o Tailscale e continue a fila; as cópias parciais estão preservadas.",error) }
            if(status==409)error("O conjunto mudou no notebook/Drive. Descarte a cópia parcial em Downloads e baixe de novo.")
            require(status==200 || status==206) { runCatching { JSONObject(connection.errorStream.bufferedReader().readText()).optString("error") }.getOrNull()?.takeIf { it.isNotBlank() } ?: "Notebook recusou ${member.file} (HTTP $status)." }
            if(status==206)require(connection.getHeaderField("Content-Range")?.startsWith("bytes $offset-")==true) { "Resposta parcial inesperada; cópia preservada." }
            return connection.inputStream.use { ResumableCopy.copy(it,file,member.size,cancelled=stop,progress=progress,resumed=status==206) }
        } finally { connection.disconnect() }
    }
    private fun folder(tree:Uri,base:Uri,parts:List<String>,create:Boolean):Uri? {
        var current=base
        for(part in parts) current=storage.children(tree,current)[part] ?: if(create)(DocumentsContract.createDocument(store.context.contentResolver,current,DocumentsContract.Document.MIME_TYPE_DIR,part) ?: error("Não foi possível criar a pasta $part.")) else return null
        return current
    }
    /** Arquivos da pasta do sistema no celular (caminho relativo → Uri), até 4 níveis, sem ocultos. */
    private fun inventory(tree:Uri):Map<String,Uri> {
        val base=storage.folder(tree,false) ?: return emptyMap();val out=linkedMapOf<String,Uri>()
        fun scan(folder:Uri,prefix:String,depth:Int) {
            for((name,uri) in storage.children(tree,folder)) {
                if(name.startsWith("."))continue
                val isDir=store.context.contentResolver.getType(uri)==DocumentsContract.Document.MIME_TYPE_DIR
                if(isDir) { if(depth<4)scan(uri,"$prefix$name/",depth+1) } else { require(out.size<20000);out["$prefix$name"]=uri }
            }
        }
        scan(base,"",0);return out
    }
    /** Prévia de remoção de um conjunto no celular, refeita do zero a cada chamada. */
    fun removalPlan(tree:Uri,entryUri:Uri):Pair<String,BundleRemoval> {
        val files=inventory(tree)
        val entry=files.entries.firstOrNull { DocumentsContract.getDocumentId(it.value)==DocumentsContract.getDocumentId(entryUri) }?.key ?: error("O arquivo principal não está mais na pasta.")
        return entry to BundleRules.removalPlan(entry,files.keys) { path -> String(storage.read(files.getValue(path),1024*1024),Charsets.UTF_8) }
    }
    /** Remove exatamente a prévia confirmada; se algo mudou na pasta, não apaga nada. */
    fun remove(tree:Uri,entryUri:Uri,confirmed:BundleRemoval):Int {
        val (_,now)=removalPlan(tree,entryUri)
        require(now==confirmed && now.complete) { "A pasta mudou desde a prévia. Nada foi removido; abra a remoção de novo." }
        val files=inventory(tree);var removed=0
        for(path in now.remove) { require(DocumentsContract.deleteDocument(store.context.contentResolver,files.getValue(path))) { "Não foi possível remover $path; o resto foi mantido." };removed++ }
        return removed
    }
    /** Baixa e publica; devolve o Uri do arquivo principal (o que o emulador abre). */
    fun download(key:String,ref:BundleRef,tree:Uri,stop:()->Boolean,progress:(Long)->Unit):Uri {
        val (id,members)=manifest(ref.code,ref.entry)
        require(id==ref.id) { "O conjunto mudou desde que foi escolhido. Descarte a cópia parcial em Downloads e baixe de novo." }
        val ordered=BundleRules.publishOrder(members,ref.entry)
        require(members.sumOf { it.size }<=12L*1024*1024*1024) { "Conjunto acima do limite de 12 GB." }
        val staging=dir(key);val sums=mutableMapOf<String,String>();var done=0L
        for((index,member) in members.withIndex()) {
            val part=File(staging,"$index.part")
            sums[member.file]=fetch(ref,member,part,stop) { bytes -> progress(done+bytes) }
            if(stop())throw ResumableCopy.Paused()
            require(part.length()==member.size) { "${member.file} chegou incompleto; cópia preservada." }
            done+=member.size
        }
        val base=storage.folder(tree,true)!!
        // Colisões em todos os destinos antes de publicar: igual é reaproveitado, diferente cancela tudo.
        val existing=ordered.associateWith { member -> val parts=member.file.split('/')
            folder(tree,base,parts.dropLast(1),false)?.let { storage.children(tree,it)[parts.last()] } }
        for((member,uri) in existing) if(uri!=null)require(storage.fingerprint(uri).sha256==sums[member.file]) { "Já existe ${member.file} diferente no celular. Nenhum arquivo do conjunto foi substituído." }
        var entryUri:Uri?=null
        for(member in ordered) {
            val parts=member.file.split('/');val parent=folder(tree,base,parts.dropLast(1),true)!!
            val uri=existing[member] ?: run { storage.publish(tree,parent,parts.last(),File(staging,"${members.indexOf(member)}.part"),sums.getValue(member.file),null)
                storage.children(tree,parent)[parts.last()] ?: error("${member.file} não apareceu depois de publicado; cópias preservadas.") }
            if(member.file==ref.entry)entryUri=uri
        }
        discard(key)
        return requireNotNull(entryUri)
    }
}
