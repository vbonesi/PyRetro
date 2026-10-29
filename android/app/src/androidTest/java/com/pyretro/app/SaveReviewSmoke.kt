package com.pyretro.app

import android.app.Activity
import android.app.AlertDialog
import android.app.Instrumentation
import android.content.Intent
import android.os.Bundle
import android.provider.DocumentsContract
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import java.util.UUID

/** Tela real com SAF descartável e nuvem em memória; provoca falhas sem atingir saves reais. */
class SaveReviewSmoke(private val runner:Instrumentation) {
    fun run()=with(runner) {
        val result=Bundle();val name="save-review-"+UUID.randomUUID();val fixture=LibraryStore(targetContext,name)
        val real=LibraryStore(targetContext);real.cloudLibrary
        val visual=real.prefs.all.filterKeys { it.startsWith("ui:") };val realCloud=targetContext.getSharedPreferences("cloud-sync",0).all.toMap()
        val memory=MemoryCloudStorage();var readFailure=true;var writeFailure=false
        val cloud=object:CloudStorage by memory {
            override fun list(prefix:String):List<CloudEntry> { if(readFailure)error("rede fictícia indisponível");return memory.list(prefix) }
            override fun put(path:String,data:ByteArray,overwrite:Boolean) { if(writeFailure)error("envio fictício recusado");memory.put(path,data,overwrite) }
        }
        var activity:MainActivity?=null;var root:android.net.Uri?=null
        fun field(name:String)=MainActivity::class.java.getDeclaredField(name).apply { isAccessible=true }
        fun nodes(v:View):List<View> = listOf(v)+if(v is ViewGroup)(0 until v.childCount).flatMap { nodes(v.getChildAt(it)) } else emptyList()
        fun views():List<View> { var out=emptyList<View>();runOnMainSync { out=(field("dialog").get(activity) as? AlertDialog)?.window?.decorView?.let(::nodes).orEmpty() };return out }
        fun contains(text:String)=views().filterIsInstance<TextView>().any { it.text.toString().contains(text) }
        fun await(text:String) { repeat(150) { waitForIdleSync();if(contains(text))return;Thread.sleep(100) };error("Texto esperado ausente: $text") }
        fun click(prefix:String) { val button=views().filterIsInstance<Button>().first { it.isEnabled && it.text.toString().startsWith(prefix) };runOnMainSync { button.performClick() };waitForIdleSync() }
        try {
            val granted=real.tree("ROOT") ?: error("Escolha a pasta Jogos no app antes do teste.")
            root=DocumentsContract.createDocument(targetContext.contentResolver,DocumentsContract.buildDocumentUriUsingTree(granted,real.documentId(granted)),DocumentsContract.Document.MIME_TYPE_DIR,".pyretro-$name")!!
            val system=DocumentsContract.createDocument(targetContext.contentResolver,root,DocumentsContract.Document.MIME_TYPE_DIR,"SFC")!!
            val file=DocumentsContract.createDocument(targetContext.contentResolver,system,"application/octet-stream","Synthetic.srm")!!
            targetContext.contentResolver.openOutputStream(file,"w")!!.use { it.write("synthetic save".toByteArray()) }
            FileSync(fixture).setTree("retro-saves",root)
            MainActivity.automaticUpdates=false
            activity=startActivitySync(Intent(targetContext,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) as MainActivity
            runOnMainSync {
                field("store").set(activity,fixture);field("saveStorageOverride").set(activity,cloud)
                MainActivity::class.java.declaredMethods.single { it.name=="cloudSaves" && it.parameterCount==3 }.apply { isAccessible=true }.invoke(activity,"Nuvem sintética",null,false)
            }
            await("rede fictícia indisponível");readFailure=false;click("Comparar novamente");await("Sincronizar agora")
            writeFailure=true;click("Sincronizar agora");await("envio fictício recusado")
            check((field("dialog").get(activity) as AlertDialog).isShowing)
            writeFailure=false;click("Sincronizar agora");await("Tudo em dia com a nuvem")
            check(memory.files.keys.any { it.startsWith("saves/blobs/") });check(FileSync(fixture).local("retro-saves").getValue("SFC/Synthetic.srm").sha256==CloudRules.sha256("synthetic save".toByteArray()))
            check(targetContext.getSharedPreferences("cloud-sync",0).all==realCloud)
            result.putString("stream","PASS: falha de consulta, falha de envio, diálogo preservado, retry e sucesso na tela real; SAF próprio e nuvem em memória.\n")
        } catch(error:Throwable) { result.putString("stream","FAIL: ${error.stackTraceToString()}\n") }
        finally {
            activity?.let { runOnMainSync { it.finish() };waitForIdleSync() };fixture.closeJournal();real.closeJournal()
            root?.let { DocumentsContract.deleteDocument(targetContext.contentResolver,it) }
            val edit=real.prefs.edit();real.prefs.all.keys.filter { it.startsWith("ui:") }.forEach(edit::remove)
            visual.forEach { (k,v) -> when(v) { is String -> edit.putString(k,v);is Int -> edit.putInt(k,v);is Long -> edit.putLong(k,v);is Boolean -> edit.putBoolean(k,v) } };edit.commit()
            targetContext.deleteSharedPreferences(name);targetContext.deleteSharedPreferences(name+"-file-sync");targetContext.deleteSharedPreferences(name+"-cloud-sync");targetContext.deleteDatabase(name+"-library.db")
            MainActivity.automaticUpdates=true
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
