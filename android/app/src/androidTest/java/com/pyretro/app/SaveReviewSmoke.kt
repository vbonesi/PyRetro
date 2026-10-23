package com.pyretro.app

import android.app.Activity
import android.app.AlertDialog
import android.app.Instrumentation
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import java.io.File

/** Renderiza planos falsos: sem consulta/sync real e sem acionar botões de gravação. */
class SaveReviewSmoke(private val runner:Instrumentation) {
    fun run()=with(runner) {
        val result=Bundle();var activity:MainActivity?=null
        val prefs=LibraryStore(targetContext).prefs
        val ui=prefs.all.filterKeys { it.startsWith("ui:") }
        fun texts(view:View):List<String> = (if(view is TextView)listOf(view.text.toString()) else emptyList())+
            if(view is ViewGroup)(0 until view.childCount).flatMap { texts(view.getChildAt(it)) } else emptyList()
        try {
            MainActivity.automaticUpdates=false
            activity=startActivitySync(Intent(targetContext,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) as MainActivity
            val method=MainActivity::class.java.declaredMethods.single { it.name=="reviewGameSaves" && it.parameterCount==4 }.apply { isAccessible=true }
            val dialogField=MainActivity::class.java.getDeclaredField("dialog").apply { isAccessible=true }
            fun review(plans:Result<List<SyncPlan>>?,drive:Boolean):String {
                var shown=""
                runOnMainSync {
                    method.invoke(activity,Game("fixture","fixture","Jogo de teste","Super Nintendo","SFC"),emptyList<Pair<String,Long>>(),plans,drive)
                    shown=texts((dialogField.get(activity) as AlertDialog).window!!.decorView).joinToString("\n")
                };waitForIdleSync();return shown
            }
            val drive=review(Result.success(listOf(SyncPlan("retro-saves","drive:fixture","fixture",emptyList()))),false)
            check(drive.contains("Iguais no celular e no Drive.") && !drive.contains("notebook",true))
            uiAutomation.takeScreenshot().let { image -> File(targetContext.cacheDir,"save-review-smoke.png").outputStream().use { image.compress(Bitmap.CompressFormat.PNG,100,it) };image.recycle() }
            val failed=review(Result.failure(IllegalStateException("rede fictícia")),true)
            check(failed.contains("Não foi possível comparar com o Drive") && !failed.contains("notebook",true))
            check(review(null,false).contains("Configure o notebook para comparar."))
            check(review(Result.failure(IllegalStateException("rede fictícia")),false).contains("Notebook offline"))
            result.putString("stream","PASS: ficha no aparelho com Drive igual/erro e notebook ausente/offline; planos sintéticos, sem transferência.")
        } catch(error:Throwable) { result.putString("stream","FAIL: "+error.stackTraceToString()) }
        finally {
            activity?.let { runOnMainSync { it.finish() };waitForIdleSync() }
            val edit=prefs.edit();prefs.all.keys.filter { it.startsWith("ui:") }.forEach(edit::remove)
            ui.forEach { (k,v) -> when(v) { is String -> edit.putString(k,v);is Int -> edit.putInt(k,v);is Long -> edit.putLong(k,v);is Boolean -> edit.putBoolean(k,v) } };edit.commit()
            MainActivity.automaticUpdates=true
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
