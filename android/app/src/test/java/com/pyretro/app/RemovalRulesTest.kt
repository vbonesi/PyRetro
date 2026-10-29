package com.pyretro.app
import org.junit.Assert.*
import org.junit.Test
class RemovalRulesTest {
    private val a=RemovalFile("Game.cue","local-id",123,"hash-a");private val b=RemovalFile("Game.cue","drive-id",123,"hash-a")
    @Test fun scopesAndRevalidationProtectEveryMutation() {
        val plan=RemovalRules.plan("both",listOf(a),listOf(b));val done=mutableListOf<String>()
        assertThrows(IllegalArgumentException::class.java) { RemovalRules.apply(plan,"stale",plan.confirmation,{done.add(it.id)},{done.add(it.id)}) };assertTrue(done.isEmpty())
        val changed=RemovalRules.plan("both",listOf(a.copy(fingerprint="new")),listOf(b));assertNotEquals(plan.token,changed.token)
        assertTrue(RemovalRules.apply(plan,plan.token,plan.confirmation,{done.add(it.id)},{done.add(it.id)}).all { it.second.isSuccess });assertEquals(listOf("local-id","drive-id"),done)
        assertTrue(RemovalRules.plan("local",listOf(a),listOf(b)).drive.isEmpty());assertTrue(RemovalRules.plan("drive",listOf(a),listOf(b)).local.isEmpty())
    }
    @Test fun startedPinnedQueuedUnknownDriveAndPartialFailuresStayVisible() {
        val blocked=RemovalRules.plan("both",listOf(a),null,protected=listOf("Iniciado","Fixado","Transferindo"),complete=false);assertEquals(5,blocked.blocked.size)
        assertThrows(IllegalArgumentException::class.java) { RemovalRules.apply(blocked,blocked.token,blocked.confirmation,{},{}) }
        val plan=RemovalRules.plan("both",listOf(a),listOf(b));val result=RemovalRules.apply(plan,plan.token,plan.confirmation,{}, {error("Offline")})
        assertTrue(result[0].second.isSuccess);assertTrue(result[1].second.isFailure)
    }
}
