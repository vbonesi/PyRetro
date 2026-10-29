package com.pyretro.app
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
class ArcadeRulesTest {
    @Test fun cloneParentAndBiosChainsProtectOnlyDependencies() {
        val parents=ArcadeRules.parse(JSONObject("""{"schema":1,"parents":{"clone":"parent","parent":"bios","bios":"","other":""}}"""))
        assertEquals(listOf("clone.zip"),ArcadeRules.dependents("parent.zip",listOf("clone.zip","parent.zip","other.zip"),parents))
        assertEquals(listOf("clone.zip","parent.zip"),ArcadeRules.dependents("bios.zip",listOf("clone.zip","parent.zip"),parents))
        assertTrue(ArcadeRules.dependents("other.zip",listOf("clone.zip","parent.zip","other.zip"),parents).isEmpty())
        assertThrows(IllegalArgumentException::class.java) { ArcadeRules.dependents("parent.zip",listOf("unknown.zip"),parents) }
    }
}
