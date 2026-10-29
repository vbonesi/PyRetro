package com.pyretro.app

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MemoryJournalDb:JournalDb {
    var data=JSONObject().put("games",JSONArray());var values=JSONObject();var events=mutableListOf<JournalRow>();var seq=0L
    override fun <T> transaction(action:()->T):T {
        val oldData=JournalRules.copy(data);val oldValues=JournalRules.copy(values);val oldRows=events.toMutableList();val oldSeq=seq
        return try { action() } catch(e:Throwable) { data=oldData;values=oldValues;events=oldRows;seq=oldSeq;throw e }
    }
    override fun library()=JournalRules.copy(data)
    override fun saveLibrary(value:JSONObject) { data=JournalRules.copy(value) }
    override fun meta(key:String):Any?=values.opt(key)
    override fun putMeta(key:String,value:Any) { values.put(key,value) }
    override fun append(event:JSONObject,origin:String):Long { seq++;events.add(JournalRow(seq,origin,JournalRules.copy(event).apply { if(origin=="local")put("seq",seq) }));return seq }
    override fun rows(since:Long,origin:String?)=events.filter { it.localSeq>since && (origin==null || origin==it.origin) }
}

class LibraryJournalTest {
    @Test fun sharedPythonKotlinFixtureConvergesInBothOrders() {
        val fixture=JSONObject(javaClass.getResource("/journal-parity.json")!!.readText());val rows=fixture.getJSONArray("changes");val events=(0 until rows.length()).map { rows.getJSONObject(it) }
        for(order in listOf(events,events.reversed())) {
            var data=fixture.getJSONObject("base");var state=JSONObject()
            for(c in order) { val result=JournalRules.merge(data,listOf(c),state);data=result.library;state=result.state }
            assertTrue(JournalRules.same(fixture.getJSONObject("expected"),data))
        }
    }
    private fun library(nota:Int)=JSONObject("""{"games":[{"id":"a","nome":"Água","nota":$nota}]}""")
    @Test fun diffRoundTripAndThePythonFormatAreUnderstood() {
        val before=library(5);val after=library(8)
        val changes=JournalRules.diff(before,after)
        assertEquals(1,changes.size);assertEquals("set",changes.single().getString("op"))
        val remote=JSONObject("""{"device":"pc","from":1,"to":1,"changes":[{"seq":1,"at":1000,"op":"set","id":"a","field":"nota","value":8}]}""")
        val store=MemoryCloudStorage();store.put("journal/pc/000000000001-000000000001.json",remote.toString().toByteArray())
        val db=MemoryJournalDb();val diary=LibraryJournal(db,"phone");diary.seed(before)
        assertEquals(1,diary.pull(store));assertEquals(8,diary.library().getJSONArray("games").getJSONObject(0).getInt("nota"))
        assertEquals(0,diary.pull(store));assertEquals(0,diary.publish(store))
    }
    @Test fun publicationIsImmutableAndBackwardClockCannotWinOverANewerChange() {
        val store=MemoryCloudStorage();val db=MemoryJournalDb();var now=1000.0
        val diary=LibraryJournal(db,"phone",now={now});diary.seed(library(5));diary.record(library(8));assertEquals(1,diary.publish(store))
        assertEquals(0,diary.publish(store));now=1.0;diary.record(library(9))
        assertTrue(db.events.last().event.getDouble("at")>1000.0)
        store.put("journal/phone/000000000002-000000000002.json","{}".toByteArray())
        assertThrows(IllegalArgumentException::class.java) { diary.publish(store) }
        assertEquals(1,diary.pending())
    }
    @Test fun bootstrapPreservesOfflineEditsAndMergesSessionsWithoutAddingAccumulatedTime() {
        val db=MemoryJournalDb();val diary=LibraryJournal(db,"phone",now={2000.0});diary.seed(library(5));diary.record(library(9))
        diary.bootstrap(library(6),JSONObject())
        assertEquals(9,diary.library().getJSONArray("games").getJSONObject(0).getInt("nota"))
        val withSessions=diary.library();withSessions.getJSONArray("games").getJSONObject(0).put("tempo","10:00:00").put("_play_sessions",JSONObject().put("phone:x",60))
        diary.record(withSessions);val event=db.events.last { it.event.optString("op")=="session" }.event
        assertEquals("session",event.getString("op"))
        val merged=JournalRules.merge(withSessions,listOf(event));assertEquals(0,merged.applied)
        assertEquals("10:00:00",merged.library.getJSONArray("games").getJSONObject(0).getString("tempo"))
    }
    @Test fun sameTimestampHasAStableWinnerAndUnknownGameEditsWaitForRegistration() {
        val older=JSONObject("""{"op":"set","id":"a","field":"nota","value":5,"at":10,"device":"a","seq":1}""")
        val newer=JSONObject("""{"op":"set","id":"a","field":"nota","value":9,"at":10,"device":"z","seq":1}""")
        for(events in listOf(listOf(older,newer),listOf(newer,older)))assertEquals(9,JournalRules.merge(library(0),events).library.getJSONArray("games").getJSONObject(0).getInt("nota"))
        val pending=JournalRules.merge(JSONObject().put("games",JSONArray()),listOf(newer))
        val add=JSONObject("""{"op":"add","id":"a","value":{"id":"a","nome":"A"},"at":1,"device":"pc","seq":1}""")
        val resolved=JournalRules.merge(pending.library,listOf(add),pending.state)
        assertEquals(9,resolved.library.getJSONArray("games").getJSONObject(0).getInt("nota"))
    }
}
