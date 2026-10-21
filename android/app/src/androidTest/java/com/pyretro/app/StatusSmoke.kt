package com.pyretro.app

import android.app.Activity
import android.app.Instrumentation
import android.content.Intent
import android.content.pm.ActivityInfo
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.view.View
import android.view.ViewGroup
import org.json.JSONObject
import java.util.UUID

/** Preferências isoladas; navegação real somente por telas de consulta do PyRetro. */
class StatusSmoke(private val runner:Instrumentation,private val connectionTest:Boolean=false) {
    fun run()=with(runner) {
        val result=Bundle();val name="status-smoke-"+UUID.randomUUID();val fixture=LibraryStore(targetContext,name)
        var activity:MainActivity?=null;var orientation=ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        var realUI:Map<String,*>?=null
        fun nodes(view:View):List<View> = listOf(view)+if(view is ViewGroup)(0 until view.childCount).flatMap { nodes(view.getChildAt(it)) } else emptyList()
        fun invoke(method:String) { runOnMainSync { MainActivity::class.java.getDeclaredMethod(method).apply { isAccessible=true }.invoke(activity) };waitForIdleSync() }
        fun dialogViews():List<View> {
            var values=emptyList<View>();runOnMainSync {
                val field=MainActivity::class.java.getDeclaredField("dialog").apply { isAccessible=true }
                val dialog=field.get(activity) as android.app.AlertDialog
                values=nodes(dialog.window!!.decorView)
            };return values
        }
        fun contains(value:String)=dialogViews().filterIsInstance<TextView>().any { it.text.toString().contains(value) }
        try {
            // Não acessa provedores nem o servidor ao compor os estados.
            val real=LibraryStore(targetContext)
            real.prefs.getString("tree:ROOT",null)?.let { fixture.saveTree("ROOT",android.net.Uri.parse(it)) }
            val folders=StatusStore(fixture).folders()
            check(folders.any { it.code=="retroarch" && it.access==FolderAccess.UNSELECTED })
            if(fixture.tree("ROOT")!=null)check(folders.first { it.code=="ROOT" }.access in setOf(FolderAccess.READ_ONLY,FolderAccess.READ_WRITE))
            val selected=fixture.prefs.getString("tree:ROOT",null)
            fixture.prefs.edit().putString("tree:ROOT","invalid-tree").commit()
            check(StatusStore(fixture).folders().first { it.code=="ROOT" }.access==FolderAccess.RESELECT)
            check(StatusStore(fixture).folders().first { it.code=="FC" }.access==FolderAccess.RESELECT)
            fixture.prefs.edit().putString("tree:ROOT",selected).commit()
            val payload=JSONObject().put("key","fixture-game").put("campos",JSONObject().put("iniciado",true)).toString()
            fixture.prefs.edit().putString("pending:fixture-game",payload).putString("conflict:pending:fixture-game",payload)
                .putString("time-event:fixture-event",JSONObject().put("key","fixture-game").put("minutes",5).toString()).commit()
            check(StatusStore(fixture).pending().size==2)
            check(StatusStore(fixture).pending().count { it.conflict }==1)
            fixture.prefs.edit().putString("pending:fixture-game",JSONObject(payload).put("changed",true).toString()).commit()
            check(StatusStore(fixture).pending().none { it.conflict })
            check(StatusStore(fixture).connectionSummary { "date-$it" }.contains("não configurado"))
            fixture.setBase("https://example.invalid")
            fixture.prefs.edit().putLong("last-contact",123L).putLong("tracking-sync-at",456L).putLong("last-attempt",789L).putBoolean("last-attempt-ok",false).commit()
            val connection=StatusStore(fixture).connectionSummary { "date-$it" }
            check(connection.contains("date-123") && connection.contains("date-789") && connection.contains("falhou"))
            fixture.prefs.edit().putBoolean("last-attempt-ok",true).commit()
            check(StatusStore(fixture).connectionSummary { "date-$it" }.contains("respondeu"))
            fixture.setBase("https://example.invalid/");check(fixture.prefs.getLong("last-contact",0)==123L)
            fixture.setBase("https://other.invalid");check(!fixture.prefs.contains("last-contact") && !fixture.prefs.contains("tracking-sync-at"))
            check(StatusStore(fixture).pending().size==2)
            val sync=FileSync(fixture)
            sync.setTree("retro-saves",android.net.Uri.parse("content://com.android.externalstorage.documents/tree/primary%3Apyretro-status-smoke"))
            val record=JSONObject().put("server",fixture.base()).put("tree",sync.tree("retro-saves").toString()).put("at",1L).put("conflicts",0).put("failures",0).put("applied",false)
            val syncPrefs=targetContext.getSharedPreferences(name+"-file-sync",0)
            syncPrefs.edit().putString("observation:retro-saves",record.toString()).commit();check(sync.observation("retro-saves")!=null)
            record.remove("at");syncPrefs.edit().putString("observation:retro-saves",record.toString()).commit();check(sync.observation("retro-saves")==null)
            // Dados do usuário só são lidos. Nenhum botão de sync/download/remoção é acionado.
            val realBefore=real.prefs.all.toMap()
            realUI=realBefore.filterKeys { it.startsWith("ui:") }
            activity=startActivitySync(Intent(targetContext,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) as MainActivity
            orientation=activity!!.requestedOrientation
            invoke("statusCenter")
            var scanned=false
            for(attempt in 0 until 200) {
                runOnMainSync { scanned=MainActivity::class.java.getDeclaredField("localScanAt").apply { isAccessible=true }.getLong(activity)>0 }
                if(scanned)break
                Thread.sleep(100)
            }
            check(scanned && !contains("Leitura local ainda em andamento")) { "Central não atualizou a leitura local automaticamente." }
            for(direction in listOf(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT,ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)) {
                runOnMainSync { activity!!.requestedOrientation=direction };waitForIdleSync()
                val expected=if(direction==ActivityInfo.SCREEN_ORIENTATION_PORTRAIT)android.content.res.Configuration.ORIENTATION_PORTRAIT else android.content.res.Configuration.ORIENTATION_LANDSCAPE
                var actual=0
                for(attempt in 0 until 50) {
                    runOnMainSync { actual=activity!!.resources.configuration.orientation }
                    if(actual==expected)break
                    Thread.sleep(100)
                }
                check(actual==expected) { "Orientação não aplicada; desbloqueie o aparelho para testar retrato/paisagem." }
                invoke("statusCenter")
                check(contains("Situação e conexões") && contains("Disponível offline") && contains("Progresso e tempo"))
                val buttons=dialogViews().filterIsInstance<Button>()
                check(buttons.any { it.text.toString()=="Conferir / escolher pastas" })
                check(buttons.any { it.text.toString()=="Continuar / pausar downloads" })
                check(buttons.all { it.minimumHeight>=48*targetContext.resources.displayMetrics.density || it.id==android.R.id.button2 })
                check(buttons.first { it.text.toString()=="Ver jogos neste celular" }.hasFocus()) { "Central sem foco inicial na primeira ação." }
                invoke("folderStatuses");check(contains("Pastas e permissões"))
                invoke("connectionApps");check(contains("Emuladores e conexões") && contains("Tailscale"))
                check(dialogViews().filterIsInstance<Button>().filter { it.text.toString().contains("não encontrado") }.all { !it.isEnabled })
                invoke("pendingChanges");check(contains("Alterações pendentes"))
                invoke("downloads");check(contains("Iniciar / continuar fila") && contains("Ver fila / reordenar itens"))
                check(dialogViews().filterIsInstance<TextView>().first { it.text.toString().startsWith("Um arquivo por vez, na ordem") }.visibility==View.GONE)
                invoke("appearance");check(contains("Mostrar dica do controle"))
                runOnMainSync {
                    (MainActivity::class.java.getDeclaredField("dialog").apply { isAccessible=true }.get(activity) as? android.app.AlertDialog)?.dismiss()
                }
                runOnMainSync {
                    MainActivity::class.java.getDeclaredMethod("selectCollection",String::class.java).apply { isAccessible=true }.invoke(activity,"stream")
                    val root=activity!!.window.decorView
                    val labels=nodes(root).filterIsInstance<TextView>().map { it.text.toString() }
                    check(listOf("Xbox · XBXPlay","PS4 · Remote Play","PC e Switch · Moonlight").all { label -> labels.any { it.startsWith(label) } })
                    check(nodes(root).filterIsInstance<android.widget.EditText>().all { it.visibility==View.GONE })
                    MainActivity::class.java.getDeclaredMethod("selectCollection",String::class.java).apply { isAccessible=true }.invoke(activity,"cell")
                }
                invoke("spaceManager")
                var measured=false
                for(attempt in 0 until 200) { if(contains("Atualizar leitura de espaço")) { measured=true;break };Thread.sleep(100) }
                check(measured && contains("Livre para o app/checkpoints"))
                check(dialogViews().any { it is android.widget.HorizontalScrollView })
            }
            // Recriação verifica a mesma persistência usada ao retornar depois de o Android liberar o processo.
            runOnMainSync {
                MainActivity::class.java.getDeclaredField("dialog").apply { isAccessible=true }.get(activity).let { (it as? android.app.AlertDialog)?.dismiss() }
                MainActivity::class.java.getDeclaredField("collection").apply { isAccessible=true }.set(activity,"catalog")
                MainActivity::class.java.getDeclaredField("page").apply { isAccessible=true }.setInt(activity,2)
                MainActivity::class.java.getDeclaredMethod("render").apply { isAccessible=true }.invoke(activity)
            }
            val monitor=addMonitor(MainActivity::class.java.name,null,false)
            runOnMainSync { activity!!.recreate() }
            activity=waitForMonitorWithTimeout(monitor,15000) as? MainActivity ?: error("Activity não foi recriada.")
            removeMonitor(monitor);waitForIdleSync()
            for(attempt in 0 until 200) {
                var ready=false;runOnMainSync { ready=MainActivity::class.java.getDeclaredField("localScanAt").apply { isAccessible=true }.getLong(activity)>0 }
                if(ready)break;Thread.sleep(100)
            }
            runOnMainSync {
                check(MainActivity::class.java.getDeclaredField("collection").apply { isAccessible=true }.get(activity)=="catalog")
                check(MainActivity::class.java.getDeclaredField("page").apply { isAccessible=true }.getInt(activity)==2)
            }
            invoke("statusCenter")
            val pending=StatusStore(real).pending()
            check(real.prefs.all.filterKeys { !it.startsWith("ui:") }==realBefore.filterKeys { !it.startsWith("ui:") }) { "Preferências reais de jogos/pastas mudaram durante a navegação de consulta." }
            var locals=0;var problems:List<*> = emptyList<Any>()
            runOnMainSync {
                val gameField=MainActivity::class.java.getDeclaredField("games").apply { isAccessible=true }
                locals=(gameField.get(activity) as List<*>).filterIsInstance<Game>().count { it.localUri!=null }
                problems=MainActivity::class.java.getDeclaredField("localProblems").apply { isAccessible=true }.get(activity) as List<*>
            }
            val retro=StatusStore(real).folders().first { it.code=="retroarch" }.access
            var contact="não consultado"
            if(connectionTest && real.base().isNotBlank()) {
                val button=dialogViews().filterIsInstance<Button>().first { it.text.toString()=="Testar conexão com notebook" }
                val started=System.currentTimeMillis()
                runOnMainSync { button.performClick() }
                var completed=false
                for(attempt in 0 until 900) {
                    runOnMainSync { completed=button.isEnabled }
                    if(completed)break
                    Thread.sleep(100)
                }
                check(completed && real.prefs.getLong("last-attempt",0)>=started) { "Teste de conexão não concluiu." }
                val expected=StatusStore(real).connectionSummary { java.text.SimpleDateFormat("dd/MM/yyyy HH:mm",java.util.Locale.getDefault()).format(java.util.Date(it)) }
                check(dialogViews().filterIsInstance<TextView>().any { it.text.toString()==expected }) { "Resumo de conexão permaneceu desatualizado após o teste." }
                val contactKeys=setOf("last-contact","last-attempt","last-attempt-ok")
                check(real.prefs.all.filterKeys { it !in contactKeys && !it.startsWith("ui:") }==realBefore.filterKeys { it !in contactKeys && !it.startsWith("ui:") })
                contact=if(real.prefs.getBoolean("last-attempt-ok",false))"respondeu" else "indisponível; falha registrada"
            }
            result.putString("stream","PASS: estados/permissões/pendências isoladas e central/submenus/aba Stream em retrato/paisagem; ${pending.size} pendência(s) real(is), $locals jogo(s) local(is), ${real.cached().size} entrada(s) em cache, ${problems.size} falha(s) na leitura local, RetroArch=$retro, notebook=$contact. Coleção/página restauradas após recriação; preferências visuais temporárias restauradas, dados de jogos/pastas preservados salvo registro de contato explícito. Nenhum jogo ou sync acionado.")
        } catch(error:Throwable) { result.putString("stream","FAIL: "+error.stackTraceToString()) }
        finally {
            activity?.let { current -> runOnMainSync { current.requestedOrientation=orientation;current.finish() };waitForIdleSync() }
            realUI?.let { previous ->
                val preferences=LibraryStore(targetContext).prefs;val edit=preferences.edit()
                preferences.all.keys.filter { it.startsWith("ui:") }.forEach(edit::remove)
                previous.forEach { (key,value) -> when(value) { is String -> edit.putString(key,value);is Int -> edit.putInt(key,value);is Long -> edit.putLong(key,value);is Boolean -> edit.putBoolean(key,value) } }
                edit.commit()
            }
            targetContext.deleteSharedPreferences(name);targetContext.deleteSharedPreferences(name+"-file-sync")
        }
        finish(if(result.getString("stream","").startsWith("PASS"))Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
