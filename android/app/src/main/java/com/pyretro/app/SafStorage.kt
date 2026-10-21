package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/** Operações locais limitadas à concessão SAF, com publicação e histórico. */
class SafStorage(private val store:LibraryStore,private val maxBytes:Long=512L*1024*1024) {
    private val resolver=store.context.contentResolver
    fun hash(file:File):String=file.inputStream().use { input ->
        val digest=MessageDigest.getInstance("SHA-256");val buffer=ByteArray(1024*1024)
        while(true) { val n=input.read(buffer);if(n<0)break;digest.update(buffer,0,n) }
        digest.digest().joinToString("") { "%02x".format(it) }
    }
    fun read(uri:Uri,max:Long):ByteArray {
        val output=java.io.ByteArrayOutputStream();val buffer=ByteArray(65536)
        resolver.openInputStream(uri).use { input -> requireNotNull(input);while(true) { val n=input.read(buffer);if(n<0)break;require(output.size().toLong()+n<=max) { "Arquivo excede o limite de leitura." };output.write(buffer,0,n) } }
        return output.toByteArray()
    }
    fun hash(bytes:ByteArray):String=MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    fun fingerprint(uri:Uri):SyncFile {
        fun metadata():Pair<Long,Long> = resolver.query(uri,arrayOf(DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED),null,null,null)?.use { c -> require(c.moveToFirst()) { "Arquivo desapareceu." };c.getLong(0) to c.getLong(1) } ?: error("Sem permissão para ler o arquivo.")
        val before=metadata();require(before.first<=maxBytes) { "Arquivo excede o limite deste grupo." }
        val digest=MessageDigest.getInstance("SHA-256");var total=0L
        resolver.openInputStream(uri).use { source -> requireNotNull(source);val buffer=ByteArray(1024*1024);while(true) { val n=source.read(buffer);if(n<0)break;total+=n;require(total<=maxBytes);digest.update(buffer,0,n) } }
        require(metadata()==before && total==before.first) { "Arquivo mudou durante a leitura. Feche o emulador e analise novamente." }
        return SyncFile(uri,digest.digest().joinToString("") { "%02x".format(it) },total,before.second)
    }
    fun children(root:Uri,parent:Uri):Map<String,Uri> {
        val result=linkedMapOf<String,Uri>();val query=DocumentsContract.buildChildDocumentsUriUsingTree(root,store.documentId(parent))
        resolver.query(query,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_DOCUMENT_ID),null,null,null)?.use { c -> while(c.moveToNext()) { val name=c.getString(0);require(name !in result) { "Dois arquivos têm o mesmo nome; análise cancelada." };result[name]=DocumentsContract.buildDocumentUriUsingTree(root,c.getString(1)) } } ?: error("Selecione novamente a pasta: permissão indisponível.")
        return result
    }
    fun folder(root:Uri,create:Boolean):Uri? {
        require(root.authority=="com.android.externalstorage.documents") { "Escolha uma pasta local." }
        val granted=DocumentsContract.getTreeDocumentId(root);val target=store.documentId(root)
        require(target==granted || target.startsWith(granted+"/"))
        var current=DocumentsContract.buildDocumentUriUsingTree(root,granted)
        for(part in target.removePrefix(granted).trimStart('/').split('/').filter { it.isNotEmpty() }) {
            val found=children(root,current)[part]
            if(found!=null)current=found else {
                if(!create)return null
                current=DocumentsContract.createDocument(resolver,current,DocumentsContract.Document.MIME_TYPE_DIR,part) ?: error("Não foi possível criar a pasta.")
            }
        }
        return current
    }
    fun publish(root:Uri,parent:Uri,name:String,temp:File,expected:String,expectedLocal:String?,onStage:(Uri)->Unit={}) {
        require(root.authority=="com.android.externalstorage.documents")
        require(name.isNotEmpty() && name !in listOf(".","..") && !name.contains('/') && !name.contains('\\'))
        require(hash(temp)==expected) { "Checksum do arquivo recebido não confere." }
            val existing=children(root,parent)[name]
            require(existing?.let { fingerprint(it).sha256 }==expectedLocal) { "Arquivo local mudou depois da análise." }
            val stage=DocumentsContract.createDocument(resolver,parent,"application/octet-stream",".pyretro-stage-${UUID.randomUUID()}") ?: error("Não foi possível preparar o arquivo.")
            var previous:Uri?=null;var published=false
            try {
                onStage(stage)
                resolver.openOutputStream(stage,"w").use { output -> requireNotNull(output);temp.inputStream().use { it.copyTo(output,1024*1024) } }
                require(fingerprint(stage).sha256==expected) { "Cópia local incompleta." }
                val latest=children(root,parent)[name]
                require(latest?.let { fingerprint(it).sha256 }==expectedLocal) { "Arquivo mudou antes da conclusão." }
                if(latest!=null) {
                    previous=DocumentsContract.renameDocument(resolver,latest,".pyretro-previous-${System.currentTimeMillis()}-${UUID.randomUUID()}-$name") ?: error("Não foi possível preservar a versão anterior.")
                    require(fingerprint(previous).sha256==expectedLocal) { "Arquivo mudou ao guardar a versão anterior." }
                }
                require(children(root,parent)[name]==null) { "Outro processo criou o arquivo; versões preservadas." }
                val ready=DocumentsContract.renameDocument(resolver,stage,name) ?: error("Não foi possível concluir o arquivo.")
                require(store.displayName(ready)==name && fingerprint(ready).sha256==expected) { "Destino mudou; confira as versões preservadas na pasta." };published=true
            } finally {
                if(!published) {
                    runCatching { DocumentsContract.deleteDocument(resolver,stage) }
                    if(previous!=null && children(root,parent)[name]==null)runCatching { DocumentsContract.renameDocument(resolver,previous,name) }
                }
            }
    }
}
