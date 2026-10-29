package com.pyretro.app
import android.app.Activity
import android.app.Instrumentation
import android.os.Bundle
import android.provider.DocumentsContract
import org.json.JSONObject
import java.util.UUID

class RemovalSmoke(private val runner:Instrumentation) {
    fun run() {
        val context=runner.targetContext;val resolver=context.contentResolver;val name="removal-smoke-"+UUID.randomUUID();val store=LibraryStore(context,name);val result=Bundle()
        var root:android.net.Uri?=null;var ok=false
        try {
            val real=LibraryStore(context);val granted=real.tree("ROOT") ?: error("Escolha a pasta Jogos no app.")
            root=DocumentsContract.createDocument(resolver,DocumentsContract.buildDocumentUriUsingTree(granted,real.documentId(granted)),DocumentsContract.Document.MIME_TYPE_DIR,".pyretro-$name")!!
            store.saveTree("ROOT",root)
            val system=DocumentsContract.createDocument(resolver,root,DocumentsContract.Document.MIME_TYPE_DIR,"FC")!!
            val rom=DocumentsContract.createDocument(resolver,system,"application/octet-stream","Synthetic.nes")!!
            resolver.openOutputStream(rom,"w")!!.use { it.write("synthetic".toByteArray()) }
            val game=Game("","fixture","Synthetic","NES","FC","Synthetic.nes",localUri=rom)
            val removal=RomRemoval(store);val plan=removal.plan(game,"local");check(plan.local.size==1 && plan.blocked.isEmpty())
            val done=removal.apply(game,plan);check(done.all { it.second.isSuccess });check(store.files("FC").isEmpty())
            val record=store.prefs.all.keys.single { it.startsWith("rom-trash:") };removal.restore(record.removePrefix("rom-trash:"))
            val restored=store.files("FC").single();check(String(SafStorage(store).read(restored.uri,100))=="synthetic")
            val started=game.copy(tracking=JSONObject().put("iniciado",true),localUri=restored.uri)
            val blocked=removal.plan(started,"local");check(blocked.blocked.isNotEmpty());check(runCatching { removal.apply(started,blocked) }.isFailure)
            result.putString("stream","PASS: prévia SAF, lixeira/recuperação, arquivo idêntico e proteção de iniciado; só fixture própria.\n");ok=true
        } catch(error:Throwable) { result.putString("stream","FAIL: ${error.stackTraceToString()}\n") }
        finally { root?.let { DocumentsContract.deleteDocument(resolver,it) };store.closeJournal();context.deleteDatabase(name+"-library.db");context.deleteSharedPreferences(name) }
        runner.finish(if(ok)Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
