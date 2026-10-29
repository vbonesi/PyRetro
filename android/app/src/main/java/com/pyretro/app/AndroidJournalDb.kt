package com.pyretro.app

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import org.json.JSONArray
import org.json.JSONObject

/** Jogos e eventos em tabelas distintas; cada edição regrava apenas as linhas alteradas. */
class AndroidJournalDb(context:Context,name:String):SQLiteOpenHelper(context,name,null,1),JournalDb {
    init { setWriteAheadLoggingEnabled(true) }
    override fun onCreate(db:SQLiteDatabase) { db.execSQL("CREATE TABLE games(id TEXT PRIMARY KEY,data TEXT NOT NULL)");db.execSQL("CREATE TABLE meta(key TEXT PRIMARY KEY,data TEXT NOT NULL)");db.execSQL("CREATE TABLE changes(seq INTEGER PRIMARY KEY AUTOINCREMENT,origin TEXT NOT NULL,event TEXT NOT NULL)") }
    override fun onUpgrade(db:SQLiteDatabase,oldVersion:Int,newVersion:Int)=Unit
    override fun <T> transaction(action:()->T):T {
        val db=writableDatabase;db.beginTransaction()
        return try { action().also { db.setTransactionSuccessful() } } finally { db.endTransaction() }
    }
    override fun library():JSONObject {
        val out=(meta("library_meta") as? JSONObject)?.let(JournalRules::copy) ?: JSONObject();val games=JSONArray()
        readableDatabase.rawQuery("SELECT data FROM games ORDER BY rowid",null).use { c -> while(c.moveToNext())games.put(JSONObject(c.getString(0))) }
        return out.put("games",games)
    }
    fun game(id:String):JSONObject?=readableDatabase.rawQuery("SELECT data FROM games WHERE id=?",arrayOf(id)).use { if(it.moveToFirst())JSONObject(it.getString(0)) else null }
    override fun saveLibrary(value:JSONObject) {
        val db=writableDatabase;val wanted=JournalRules.games(value);val old=linkedMapOf<String,String>()
        db.rawQuery("SELECT id,data FROM games",null).use { c -> while(c.moveToNext())old[c.getString(0)]=c.getString(1) }
        for(id in old.keys-wanted.keys)db.delete("games","id=?",arrayOf(id))
        for((id,game) in wanted) { val raw=game.toString();if(old[id]!=raw)check(db.insertWithOnConflict("games",null,ContentValues().apply { put("id",id);put("data",raw) },SQLiteDatabase.CONFLICT_REPLACE)!=-1L) { "Falha ao gravar jogo; transação cancelada." } }
        val metadata=JournalRules.copy(value).apply { remove("games") };putMeta("library_meta",metadata)
    }
    override fun meta(key:String):Any?=readableDatabase.rawQuery("SELECT data FROM meta WHERE key=?",arrayOf(key)).use { if(it.moveToFirst())JSONArray(it.getString(0)).opt(0).takeUnless { v -> v==JSONObject.NULL } else null }
    override fun putMeta(key:String,value:Any) { check(writableDatabase.insertWithOnConflict("meta",null,ContentValues().apply { put("key",key);put("data",JSONArray().put(value).toString()) },SQLiteDatabase.CONFLICT_REPLACE)!=-1L) { "Falha ao gravar recibo; transação cancelada." } }
    override fun append(event:JSONObject,origin:String):Long {
        val db=writableDatabase;val seq=db.insertOrThrow("changes",null,ContentValues().apply { put("origin",origin);put("event",event.toString()) })
        if(origin=="local")db.update("changes",ContentValues().apply { put("event",JournalRules.copy(event).put("seq",seq).toString()) },"seq=?",arrayOf(seq.toString()))
        return seq
    }
    override fun rows(since:Long,origin:String?):List<JournalRow> {
        val out=mutableListOf<JournalRow>();val where=if(origin==null)"seq>?" else "seq>? AND origin=?";val args=if(origin==null)arrayOf(since.toString()) else arrayOf(since.toString(),origin)
        readableDatabase.rawQuery("SELECT seq,origin,event FROM changes WHERE $where ORDER BY seq",args).use { c -> while(c.moveToNext())out.add(JournalRow(c.getLong(0),c.getString(1),JSONObject(c.getString(2)))) };return out
    }
}
