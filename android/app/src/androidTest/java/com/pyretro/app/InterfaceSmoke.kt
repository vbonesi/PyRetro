package com.pyretro.app

import android.app.Activity
import android.app.AlertDialog
import android.app.Instrumentation
import android.content.Intent
import android.content.pm.ActivityInfo
import android.graphics.Bitmap
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.widget.*
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

/** Navegação de consulta com jogos e preferências isolados. Não aciona jogos ou gravações reais.
 * Os achados de paridade são observações no relatório, separados das asserções de navegação. */
class InterfaceSmoke(private val runner:Instrumentation) {
    fun run()=with(runner) {
        val result=Bundle()
        val name="interface-smoke-"+UUID.randomUUID()
        val fixture=LibraryStore(targetContext,name)
        val real=LibraryStore(targetContext)
        val before=real.prefs.all.toMap()
        val directory=File(targetContext.cacheDir,name).apply { mkdirs() }
        val screens=JSONArray();val findings=JSONArray()
        var activity:MainActivity?=null
        var originalOrientation=ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        fun field(name:String)=MainActivity::class.java.getDeclaredField(name).apply { isAccessible=true }
        fun nodes(view:View):List<View> = listOf(view)+if(view is ViewGroup)(0 until view.childCount).flatMap { nodes(view.getChildAt(it)) } else emptyList()
        fun invoke(name:String) { runOnMainSync { MainActivity::class.java.getDeclaredMethod(name).apply { isAccessible=true }.invoke(activity) };waitForIdleSync() }
        fun dismiss() { if(activity==null)return;runOnMainSync { (field("dialog").get(activity) as? AlertDialog)?.dismiss() };waitForIdleSync() }
        fun texts(dialog:Boolean=true):List<String> {
            var labels=emptyList<String>()
            runOnMainSync {
                val root=if(dialog)(field("dialog").get(activity) as? AlertDialog)?.window?.decorView else activity!!.window.decorView
                labels=root?.let(::nodes).orEmpty().filterIsInstance<TextView>().filter { it.isShown }.map { it.text.toString() }
            }
            return labels
        }
        fun capture(id:String,required:String?=null,screenshot:Boolean=false) {
            waitForIdleSync()
            val labels=texts(field("dialog").get(activity)!=null)
            if(required!=null)check(labels.any { required in it }) { "$id: texto esperado ausente: $required" }
            screens.put(JSONObject().put("screen",id).put("labels",JSONArray(labels)))
            // A fila da Activity vazia não significa que a animação/janela já chegou ao compositor.
            // Esperar os eventos de acessibilidade evita capturar a tela ou o diálogo anterior.
            if(screenshot) {
                Thread.sleep(350) // margem para a janela/animação chegar ao compositor do aparelho
                uiAutomation.waitForIdle(500,5000)
                waitForIdleSync()
                uiAutomation.takeScreenshot()?.let { bitmap ->
                File(directory,"$id.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG,100,it) };bitmap.recycle()
                }
            }
        }
        try {
            val realQueue=JSONArray(real.prefs.getString("download-queue","[]"))
            check((0 until realQueue.length()).none { realQueue.getJSONObject(it).optString("state")==DownloadState.RUNNING.name }) { "Há download real ativo; adie a revisão." }
            MainActivity.automaticUpdates=false
            activity=startActivitySync(Intent(targetContext,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) as MainActivity
            originalOrientation=activity!!.requestedOrientation
            for(attempt in 0 until 200) {
                var ready=false;runOnMainSync { ready=field("localScanAt").getLong(activity)>0 }
                if(ready)break
                Thread.sleep(100)
            }
            val games=listOf(
                Game("ui-a","ui:a","Alpha · título longo para conferir a ficha e os cartões","NES","FC","Alpha.nes",genre="RPG",tracking=JSONObject().put("nota",11).put("iniciado",true),drive=true),
                Game("ui-b","ui:b","Beta","Super Nintendo","SFC","Beta.sfc",genre="Ação",tracking=JSONObject().put("nota",10)),
                Game("ui-c","ui:c","Gamma","NES","FC","Gamma.nes",genre="RPG",tracking=JSONObject().put("nota",7)),
                Game("ui-d","ui:d","Delta sem nota","NES","FC","Delta.nes",genre="Puzzle"))
            val wish=Game("wish-id","wish:xbox:ui","Desejado de teste","Xbox Series S",genre="Corrida")
            fixture.prefs.edit().putBoolean("favorite:ui:a",true).putLong("played:ui:a",100).commit()
            runOnMainSync {
                field("store").set(activity,fixture);field("catalog").set(activity,games);field("games").set(activity,games)
                field("wishGames").set(activity,listOf(wish));field("saveNames").set(activity,emptyMap<String,List<String>>())
                field("restorePosition").setBoolean(activity,false)
                (field("search").get(activity) as EditText).setText("")
                (field("status").get(activity) as TextView).text="Teste de interface · dados sintéticos"
            }
            for((orientation,label) in listOf(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT to "portrait",ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE to "landscape")) {
                runOnMainSync { activity!!.requestedOrientation=orientation };waitForIdleSync()
                for(attempt in 0 until 50) {
                    val wanted=if(label=="portrait")1 else 2
                    if(activity!!.resources.configuration.orientation==wanted)break
                    Thread.sleep(100)
                }
                check(activity!!.resources.configuration.orientation==if(label=="portrait")1 else 2) { "Desbloqueie o aparelho para aplicar a orientação." }
                for(collection in listOf("home","catalog","cell","favorites","ranking","wishlist","kept","stream")) {
                    dismiss()
                    runOnMainSync {
                        field("collection").set(activity,collection);field("page").setInt(activity,0)
                        field("filterPlatform").set(activity,"");field("filterGenre").set(activity,"")
                    }
                    invoke("render")
                    capture("$label-$collection",screenshot=collection in setOf("ranking","stream","home"))
                    if(collection=="ranking") {
                        var keys=emptyList<String>()
                        runOnMainSync { keys=nodes(field("grid").get(activity) as View).mapNotNull { (it.tag as? Game)?.key } }
                        check(keys.toSet()==setOf("ui:a","ui:b","ui:c") && keys.size==3) { "Ranking duplicou jogos ou incluiu jogo sem nota." }
                        if(label=="portrait")check(keys==listOf("ui:a","ui:b","ui:c")) { "Pódio em retrato fora da ordem 1–2–3." }
                    }
                }
                runOnMainSync { field("collection").set(activity,"wishlist") }
                invoke("filterDialog");capture("$label-wishlist-filters","Filtrar")
                check("Xbox Series S" in texts() && "Corrida" in texts()) { "Filtro de Desejados usou as opções do Catálogo." }
                dismiss()
                runOnMainSync { field("collection").set(activity,"catalog") }
                invoke("draw");capture("$label-draw","Sortear",screenshot=true);dismiss()
                runOnMainSync { MainActivity::class.java.getDeclaredMethod("details",Game::class.java).apply { isAccessible=true }.invoke(activity,games.first()) }
                capture("$label-details","Alpha",screenshot=true)
                runOnMainSync {
                    val root=(field("dialog").get(activity) as AlertDialog).window!!.decorView
                    nodes(root).filterIsInstance<Button>().first { "Progresso e tempo" in it.text }.let { if(it.text.startsWith("▸"))it.performClick() }
                }
                capture("$label-progress","Nota (0–11)",screenshot=true);dismiss()
                for((method,required) in listOf("statusCenter" to "Situação","settings" to "Opções","folderStatuses" to "Pastas e permissões",
                    "connectionApps" to "Emuladores e conexões","pendingChanges" to "Alterações pendentes","downloads" to "Downloads",
                    "queueList" to "Fila de downloads","syncFiles" to "Saves e estados","cloudMenu" to "Catálogo da nuvem","playlists" to "Playlists","statsDialog" to "Estatísticas")) {
                    invoke(method);capture("$label-$method",required);dismiss()
                }
                invoke("spaceManager")
                for(attempt in 0 until 100) { if(texts().any { "Livre para o app" in it })break;Thread.sleep(50) }
                capture("$label-space","Livre para o app");dismiss()
            }
            check(real.prefs.all.filterKeys { !it.startsWith("ui:") }==before.filterKeys { !it.startsWith("ui:") }) { "Preferências reais de jogos/pastas mudaram." }
            File(directory,"report.json").writeText(JSONObject().put("fontScale",activity!!.resources.configuration.fontScale).put("screens",screens).put("findings",findings).toString(2))
            result.putString("stream","PASS: ${screens.length()} telas/estados em retrato e paisagem; ${findings.length()} observações de paridade. Evidências: ${directory.absolutePath}. Nenhum jogo, sync, download ou remoção acionado.")
        } catch(error:Throwable) {
            File(directory,"report.json").writeText(JSONObject().put("screens",screens).put("findings",findings).put("error",error.stackTraceToString()).toString(2))
            result.putString("stream","FAIL: ${error.stackTraceToString()}\nEvidências: ${directory.absolutePath}")
        } finally {
            dismiss()
            activity?.let { current -> runOnMainSync { current.requestedOrientation=originalOrientation;current.finish() };waitForIdleSync() }
            val edit=real.prefs.edit();real.prefs.all.keys.filter { it.startsWith("ui:") }.forEach(edit::remove)
            before.filterKeys { it.startsWith("ui:") }.forEach { (key,value) -> when(value) {
                is String -> edit.putString(key,value);is Int -> edit.putInt(key,value);is Long -> edit.putLong(key,value);is Boolean -> edit.putBoolean(key,value)
            } };edit.commit()
            MainActivity.automaticUpdates=true
            targetContext.deleteSharedPreferences(name);targetContext.deleteSharedPreferences(name+"-file-sync")
            File(targetContext.filesDir,name+"-downloads").deleteRecursively()
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
