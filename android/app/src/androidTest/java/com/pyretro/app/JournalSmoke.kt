package com.pyretro.app
import android.app.Activity
import android.app.Instrumentation
import android.os.Bundle
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** SQLite real em bases descartáveis; nenhum dado do usuário é alterado. */
class JournalSmoke(private val test:Instrumentation) {
    fun run() {
        val context=test.targetContext;val name="journal-smoke-"+UUID.randomUUID();val result=Bundle()
        val first=AndroidJournalDb(context,"$name-a.db");val second=AndroidJournalDb(context,"$name-b.db")
        val local=LibraryStore(context,"$name-library")
        var ok=false
        try {
            val cloud=MemoryCloudStorage();val a=LibraryJournal(first,"pc");val b=LibraryJournal(second,"phone")
            val base=JSONObject().put("games",JSONArray().put(JSONObject().put("id","fixture").put("nome","Sintético").put("nota",0)))
            a.seed(base);b.seed(base)
            first.transaction { val changed=a.library();changed.getJSONArray("games").getJSONObject(0).put("nota",9);a.record(changed) }
            check(a.publish(cloud)==1);check(b.pull(cloud)==1);check(b.pull(cloud)==0);check(second.game("fixture")!!.getInt("nota")==9)
            val changed=b.library();changed.getJSONArray("games").getJSONObject(0).put("favorite",true).put("_play_sessions",JSONObject().put("phone:session",60));b.record(changed)
            check(b.publish(cloud)==2);check(a.pull(cloud)==2);check(first.game("fixture")!!.getJSONObject("_play_sessions").getInt("phone:session")==60)
            val before=first.library().toString();runCatching { first.transaction { first.saveLibrary(base);error("rollback") } };check(first.library().toString()==before)
            first.close();val reopened=AndroidJournalDb(context,"$name-a.db")
            try { check(reopened.game("fixture")!!.getBoolean("favorite"));check(LibraryJournal(reopened,"pc").pending()==0) } finally { reopened.close() }
            val game=Game("","fixture-local","Local","NES","FC","Local.nes")
            local.prefs.edit().putString("pending:${game.key}",JSONObject().put("key",game.key).put("campos",JSONObject().put("iniciado",true)).toString())
                .putBoolean("favorite:${game.key}",true).putString("time-event:fixture",JSONObject().put("key",game.key).put("minutes",2).put("event","fixture").toString()).commit()
            val registered=local.cloudLibrary.register(game,"Local");val row=local.cloudLibrary.game(registered.getString("id"))!!
            check(row.getBoolean("iniciado") && row.getBoolean("favorite"));check(row.getJSONObject("_play_sessions").getLong(local.cloudLibrary.journal.device+":fixture")==120L)
            check(local.cached().single().id==registered.getString("id"));check(local.prefs.getString("pending:${game.key}",null)==null)
            val extras=NotebookExtras(local,context.cacheDir);extras.edit(row.getString("id"),mapOf("observacoes" to "Offline"));check(extras.record(row.getString("id"))!!.getString("observacoes")=="Offline")
            result.putString("stream","PASS: SQLite persistente, transação aninhada/rollback, dois dispositivos, replay idempotente e sessões.\n");ok=true
        } catch(error:Throwable) { result.putString("stream","FAIL: ${error.stackTraceToString()}\n") }
        finally { first.close();second.close();local.closeJournal();context.deleteDatabase("$name-a.db");context.deleteDatabase("$name-b.db");context.deleteDatabase("$name-library-library.db");context.deleteSharedPreferences("$name-library") }
        test.finish(if(ok)Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
