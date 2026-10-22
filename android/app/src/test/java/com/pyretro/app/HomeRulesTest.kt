package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Fileiras do Início: só dados locais, fileira vazia some, jogo do celular vem antes. */
class HomeRulesTest {
    private fun entry(key:String,onPhone:Boolean=false,started:Boolean=false,finished:Boolean=false,favorite:Boolean=false,playedAt:Long=0,seconds:Long=0)=
        HomeEntry(key,key,onPhone,started,finished,favorite,playedAt,seconds)
    @Test fun rowsFollowLocalDataAndSkipEmptyOnes() {
        val rows=HomeRules.rows(listOf(
            entry("pc-iniciado",started=true),
            entry("cel-iniciado",onPhone=true,started=true),
            entry("finalizado",onPhone=true,started=true,finished=true,playedAt=50,seconds=600),
            entry("recente",onPhone=true,playedAt=100,seconds=60)
        )).toMap()
        assertEquals(listOf("cel-iniciado","pc-iniciado"),rows["Continuar jogando"])
        assertEquals(listOf("recente","finalizado"),rows["Recentes"])
        assertEquals(listOf("finalizado","recente"),rows["Mais jogados"])
        assertEquals(listOf("recente","finalizado","cel-iniciado"),rows["Prontos no celular"])
        assertFalse("Favoritos" in rows)
    }
    @Test fun eachRowIsLimited() {
        val rows=HomeRules.rows((1..40).map { entry("j$it",onPhone=true) },limit=15).toMap()
        assertEquals(15,rows.getValue("Prontos no celular").size)
        assertTrue(HomeRules.rows(emptyList()).isEmpty())
    }
    @Test fun renamedGameKeepsTheLatestLaunch() {
        val migration=KeyAliases.plan(mapOf("played:velho" to 10L,"played:novo" to 30L),mapOf("velho" to "novo")) { raw,_ -> raw }
        assertEquals(30L,migration.puts["played:novo"])
        assertTrue("played:velho" in migration.removes)
    }
    @Test fun ratingStepsAndComparisonMatchTheServer() {
        assertEquals(1.0,TrackingRules.adjust(null,1.0),0.0)
        assertEquals(11.0,TrackingRules.adjust(10.95,1.0),0.0)
        assertEquals(0.0,TrackingRules.adjust(0.05,-1.0),0.0)
        assertEquals(7.6,TrackingRules.adjust(7.5,0.1),0.0)
        assertTrue(TrackingRules.same(8,8.0));assertTrue(TrackingRules.same(org.json.JSONObject.NULL,null))
        assertFalse(TrackingRules.same(7.5,null))
        assertEquals("Sem nota",TrackingRules.label(null))
    }
}
