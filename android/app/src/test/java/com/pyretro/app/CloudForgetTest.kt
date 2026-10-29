package com.pyretro.app
import org.junit.Assert.*
import org.junit.Test
class CloudForgetTest {
    @Test fun sharedPythonKotlinTombstoneFixture() {
        val data=org.json.JSONObject(javaClass.getResource("/save-tombstone.json")!!.readText());val store=MemoryCloudStorage();val local=MemoryLocal();local.put(data.getString("path"),data.getString("content"))
        for(who in listOf("pc","phone"))store.put("saves/devices/$who.json",data.getJSONObject(who).toString().toByteArray())
        val engine=CloudSavesEngine(store,"phone",local,linkedMapOf(data.getString("path") to data.getString("old")))
        assertEquals("forget",engine.plan().single().action);assertEquals(setOf(data.getString("marker")),engine.plan().single().deletedHeads)
        engine.apply();assertTrue(local.files.isEmpty());assertTrue(engine.plan().isEmpty())
    }
    @Test fun explicitDeletionPropagatesWithHistoryAndRestorationIsPossible() {
        val store=MemoryCloudStorage();val pc=MemoryLocal();val phone=MemoryLocal();val a=CloudSavesEngine(store,"pc",pc,now={1000});val b=CloudSavesEngine(store,"phone",phone,now={1})
        pc.put("Game.srm","original");a.apply();b.apply();val item=a.plan(true).single()
        assertTrue(a.forget(item.path,item.local,item.heads.keys).ok);assertEquals("forget",b.plan().single().action);b.apply()
        assertTrue(pc.files.isEmpty());assertTrue(phone.files.isEmpty());assertEquals("original",String(phone.history.single().second));assertTrue(a.plan().isEmpty());assertTrue(b.plan().isEmpty())
        pc.put("Game.srm","restored");a.apply();b.apply();assertEquals("restored",String(phone.files.getValue("Game.srm")))
    }
    @Test fun offlineEditAndStaleConfirmationArePreserved() {
        val store=MemoryCloudStorage();val pc=MemoryLocal();val phone=MemoryLocal();val a=CloudSavesEngine(store,"pc",pc,now={1000});val b=CloudSavesEngine(store,"phone",phone,now={1})
        pc.put("Game.srm","original");a.apply();b.apply();val item=a.plan(true).single();pc.put("Game.srm","changed")
        assertThrows(IllegalArgumentException::class.java) { a.forget(item.path,item.local,item.heads.keys) }
        pc.put("Game.srm","original");a.forget(item.path,item.local,item.heads.keys);phone.put("Game.srm","offline");assertEquals("conflict",b.plan().single().action)
        b.resolve("Game.srm","local");a.apply();assertEquals("offline",String(pc.files.getValue("Game.srm")))
    }
}
