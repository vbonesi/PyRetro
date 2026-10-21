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
    private var statusSuite=false
    private var connectionTest=false
    override fun onCreate(arguments:Bundle?) { super.onCreate(arguments);statusSuite=arguments?.getString("suite")=="status";connectionTest=arguments?.getString("connection")=="true";start() }
    override fun onStart() {
        if(statusSuite) { StatusSmoke(this,connectionTest).run();return }
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
            val savedVersion=sync.localHistory("retro-saves").single()
            sync.restoreLocal(savedVersion)
            check(sync.local("retro-saves").getValue("Synthetic.srm").sha256==hash("first"))
            refused=false;try { sync.restoreLocal(savedVersion) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            check(sync.localHistory("retro-saves").any { it.file.sha256==hash("second") })
            val derived=FileSync(store,"file-sync-smoke-derived");derived.setTree("retroarch",testRoot)
            check(derived.local("retro-saves").isEmpty())
            // A análise da pasta derivada não cria saves/; só aplicar cria o destino.
            resolver.query(children,arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME),null,null,null)!!.use { c ->
                while(c.moveToNext())check(c.getString(0)!="saves")
            }
            temp.writeText("derived");derived.install("retro-saves","core/First.srm",temp,hash("derived"),null)
            check(derived.local("retro-saves").getValue("core/First.srm").sha256==hash("derived"))
            // Fixture isolada para nuvem, download e playlist; nenhum pref real é alterado.
            val fixture=LibraryStore(targetContext,"storage-smoke-catalog")
            fixture.saveTree("ROOT",testRoot)
            check(fixture.documentId(fixture.tree("FC")!!)==store.documentId(testRoot)+"/FC")
            FileSync(fixture).setTree("retroarch",DocumentsContract.buildDocumentUriUsingTree(testRoot,store.documentId(testRoot)+"/RetroArch"))
            val sourceFolder=DocumentsContract.createDocument(resolver,testRoot,DocumentsContract.Document.MIME_TYPE_DIR,"sources")!!
            val sourceName="CloudSynthetic-"+UUID.randomUUID()
            val source=DocumentsContract.createDocument(resolver,sourceFolder,"application/octet-stream",sourceName+".nes")!!
            val payload=ByteArray(700000) { (it%251).toByte() }
            resolver.openOutputStream(source,"w")!!.use { it.write(payload) }
            val game=Game("fixture","fixture:FC:synthetic",sourceName,"NES","FC",sourceName+".nes")
            val index=CloudIndex(fixture)
            val indexPlan=index.analyze("FC",org.json.JSONArray().put(org.json.JSONObject().put("uri",source.toString()).put("tree",false)),listOf(game))
            check(indexPlan.matches[game.key]==source.toString());index.apply(indexPlan)
            check(index.extra(listOf(game)).isEmpty())
            var paused=false
            try { DownloadStore(fixture).download(game) { if(it>0)DownloadStore.pause() } } catch(_:ResumableCopy.Paused) { paused=true };check(paused)
            check(DownloadStore(fixture).jobs().single().getLong("bytes") in 1 until payload.size.toLong())
            val downloaded=DownloadStore(fixture).download(game) {};game.localUri=downloaded
            check(DownloadStore(fixture).jobs().isEmpty())
            check(SafStorage(fixture).read(downloaded,800000).contentEquals(payload))
            val playlists=PlaylistStore(fixture);val initial=playlists.plan("FC");check(initial.added==1)
            playlists.apply(initial,true)
            val playlistParent=SafStorage(fixture).folder(initial.root,false)!!
            val playlistFile=SafStorage(fixture).children(initial.root,playlistParent).getValue(initial.name)
            val json=org.json.JSONObject(SafStorage(fixture).read(playlistFile,800000).toString(Charsets.UTF_8))
            json.getJSONArray("items").getJSONObject(0).put("core_path","my-custom-core").put("label","My label")
            json.getJSONArray("items").put(org.json.JSONObject().put("path","/another/root/preserve.nes").put("label","Keep outside"))
            json.getJSONArray("items").put(org.json.JSONObject().put("path",PlaylistRules.path(fixture.documentId(fixture.tree("FC")!!))+"/missing.nes").put("label","Missing"))
            temp.writeText(json.toString())
            SafStorage(fixture).publish(initial.root,playlistParent,initial.name,temp,SafStorage(fixture).hash(temp),SafStorage(fixture).fingerprint(playlistFile).sha256)
            val update=playlists.plan("FC");check(update.added==0 && update.removed==1)
            val resultJson=org.json.JSONObject(update.json);check(resultJson.getJSONArray("items").length()==2)
            check(resultJson.getJSONArray("items").getJSONObject(0).getString("core_path")=="my-custom-core")
            playlists.apply(update,true)
            val playlistVersion=playlists.versions("FC").first();playlists.restore(playlistVersion,"FC")
            check(!fixture.prefs.getBoolean("playlist-auto:FC",true))
            fixture.removeLocal(game);check(fixture.files("FC",true).isEmpty())
            QueueSpaceSmoke.run(fixture,sourceFolder)
            result.putString("stream","PASS: SAF/histórico/conflitos/checksum/playlists, fila sequencial com pausa/retomada/reordenação, deduplicação, espaço e fixação/revalidação de remoção; somente fixtures próprias.")
        } catch(error:Throwable) { result.putString("stream","FAIL: "+error.stackTraceToString()) }
        finally {
            temp?.delete();targetContext.getSharedPreferences("file-sync-smoke",0).edit().clear().commit()
            targetContext.getSharedPreferences("file-sync-smoke-derived",0).edit().clear().commit()
            targetContext.getSharedPreferences("storage-smoke-catalog",0).edit().clear().commit()
            targetContext.getSharedPreferences("storage-smoke-catalog-file-sync",0).edit().clear().commit()
            File(targetContext.filesDir,"storage-smoke-catalog-downloads").deleteRecursively()
            if(testRoot!=null)runCatching { check(DocumentsContract.deleteDocument(resolver,testRoot)) }.onFailure { result.putString("stream","FAIL limpeza: "+it.message) }
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
