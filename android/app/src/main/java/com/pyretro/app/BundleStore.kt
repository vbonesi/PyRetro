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
}

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
