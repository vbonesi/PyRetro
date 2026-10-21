package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class KeyAliasesTest {
    private val rekey={ raw:String,key:String -> raw.replace(Regex("\"key\":\"[^\"]*\""),"\"key\":\"$key\"") }
    @Test fun movesEveryPerGameRecordToTheNewKey() {
        val prefs=mapOf("favorite:rom:SFC:zelda" to true,"keep:rom:SFC:zelda" to "primary|1","rom:rom:SFC:zelda" to "content://x",
            "cloud:rom:SFC:zelda" to "content://y","pending:rom:SFC:zelda" to "{\"key\":\"rom:SFC:zelda\",\"campos\":{}}","ui:page" to 2)
        val plan=KeyAliases.plan(prefs,mapOf("rom:SFC:zelda" to "rom:SFC:alttp"),rekey)
        assertEquals(setOf("favorite:rom:SFC:zelda","keep:rom:SFC:zelda","rom:rom:SFC:zelda","cloud:rom:SFC:zelda","pending:rom:SFC:zelda"),plan.removes)
        assertEquals(true,plan.puts["favorite:rom:SFC:alttp"]);assertEquals("primary|1",plan.puts["keep:rom:SFC:alttp"])
        assertEquals("{\"key\":\"rom:SFC:alttp\",\"campos\":{}}",plan.puts["pending:rom:SFC:alttp"])
        assertFalse(plan.puts.keys.any { it.startsWith("ui:") })
    }
    @Test fun mergesWithoutLosingTimeOrExistingRecords() {
        val prefs=mapOf("time:a" to 600L,"time:b" to 60L,"favorite:a" to false,"favorite:b" to true,"rom:a" to "old","rom:b" to "kept")
        val plan=KeyAliases.plan(prefs,mapOf("a" to "b"),rekey)
        assertEquals(660L,plan.puts["time:b"]);assertEquals(true,plan.puts["favorite:b"]);assertEquals("kept",plan.puts["rom:b"])
        assertTrue("time:a" in plan.removes && "rom:a" in plan.removes)
    }
    @Test fun rekeysUnsentSessionsAndIgnoresUnrelatedOnes() {
        val prefs=mapOf("time-event:1" to "{\"key\":\"a\",\"minutes\":5}","time-event:2" to "{\"key\":\"z\",\"minutes\":5}")
        val plan=KeyAliases.plan(prefs,mapOf("a" to "b"),rekey)
        assertEquals("{\"key\":\"b\",\"minutes\":5}",plan.puts["time-event:1"]);assertFalse("time-event:2" in plan.puts);assertTrue(plan.removes.isEmpty())
    }
    @Test fun noAliasesNoChanges() {
        val plan=KeyAliases.plan(mapOf("favorite:a" to true),emptyMap(),rekey)
        assertTrue(plan.puts.isEmpty() && plan.removes.isEmpty())
    }
}
