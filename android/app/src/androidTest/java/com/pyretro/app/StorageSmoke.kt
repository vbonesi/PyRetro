package com.pyretro.app

import android.app.Activity
import android.app.Instrumentation
import android.os.Bundle
import android.provider.DocumentsContract
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/** Usa somente uma pasta própria de teste, criada dentro da concessão Jogos. */
class StorageSmoke:Instrumentation() {
    override fun onCreate(arguments:Bundle?) { super.onCreate(arguments);start() }
    override fun onStart() {
        val result=Bundle();var testRoot:android.net.Uri?=null;var temp:File?=null
        val resolver=targetContext.contentResolver
        try {
            val store=LibraryStore(targetContext);val tree=store.prefs.getString("tree:ROOT",null)?.let(android.net.Uri::parse) ?: error("Conceda Pasta Jogos no app antes do teste.")
            val parent=DocumentsContract.buildDocumentUriUsingTree(tree,store.documentId(tree))
            val name=".pyretro-storage-test-"+UUID.randomUUID()
            testRoot=DocumentsContract.createDocument(resolver,parent,DocumentsContract.Document.MIME_TYPE_DIR,name) ?: error("Não foi possível criar a pasta de teste.")
            val sync=FileSync(store,"file-sync-smoke");sync.setTree("retro-saves",testRoot)
            temp=File.createTempFile("sync-smoke-",".tmp",targetContext.cacheDir)
            fun hash(value:String)=MessageDigest.getInstance("SHA-256").digest(value.toByteArray()).joinToString("") { "%02x".format(it) }
            temp.writeText("first");sync.install("retro-saves","Synthetic.srm",temp,hash("first"),null)
            check(sync.local("retro-saves").getValue("Synthetic.srm").sha256==hash("first"))
            temp.writeText("second");sync.install("retro-saves","Synthetic.srm",temp,hash("second"),hash("first"))
            check(sync.local("retro-saves").size==1)
            check(sync.local("retro-saves").getValue("Synthetic.srm").sha256==hash("second"))
            val children=DocumentsContract.buildChildDocumentsUriUsingTree(testRoot,store.documentId(testRoot));var history=0
            resolver.query(children,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_DOCUMENT_ID),null,null,null)!!.use { c ->
                while(c.moveToNext())if(c.getString(0).startsWith(".pyretro-previous-")) {
                    val uri=DocumentsContract.buildDocumentUriUsingTree(testRoot,c.getString(1))
                    check(resolver.openInputStream(uri)!!.bufferedReader().use { it.readText() }=="first");history++
                }
            }
            check(history==1)
            temp.writeText("third")
            var refused=false;try { sync.install("retro-saves","Synthetic.srm",temp,hash("third"),hash("first")) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            check(sync.local("retro-saves").getValue("Synthetic.srm").sha256==hash("second"))
            refused=false;try { sync.install("retro-saves","Synthetic.srm",temp,hash("wrong"),hash("second")) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            val derived=FileSync(store,"file-sync-smoke-derived");derived.setTree("retroarch",testRoot)
            check(derived.local("retro-saves").isEmpty())
            // A análise da pasta derivada não cria saves/; só aplicar cria o destino.
            resolver.query(children,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME),null,null,null)!!.use { c ->
                while(c.moveToNext())check(c.getString(0)!="saves")
            }
            temp.writeText("derived");derived.install("retro-saves","core/First.srm",temp,hash("derived"),null)
            check(derived.local("retro-saves").getValue("core/First.srm").sha256==hash("derived"))
            result.putString("stream","PASS: criação, substituição com histórico, conflito, checksum e pasta derivada vazia; saves reais intocados.")
        } catch(error:Throwable) { result.putString("stream","FAIL: "+error.stackTraceToString()) }
        finally {
            temp?.delete();targetContext.getSharedPreferences("file-sync-smoke",0).edit().clear().commit()
            targetContext.getSharedPreferences("file-sync-smoke-derived",0).edit().clear().commit()
            if(testRoot!=null)runCatching { check(DocumentsContract.deleteDocument(resolver,testRoot)) }.onFailure { result.putString("stream","FAIL limpeza: "+it.message) }
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
