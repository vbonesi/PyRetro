package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Ranking e filtros da grade, e o contador do botão Situação. */
class GridRulesTest {
    private fun entry(key:String,platform:String="NES",genre:String="",nota:Double?=null)=GridEntry(key,key,platform,genre,nota)
    @Test fun rankingKeepsOnlyRatedGamesHighestFirst() {
        val entries=listOf(entry("b",nota=8.0),entry("sem"),entry("a",nota=8.0),entry("c",nota=10.5))
        assertEquals(listOf("c","a","b"),GridRules.ranking(entries))
    }
    @Test fun podiumGoesSecondFirstThirdAndTieIsAnnounced() {
        assertEquals(listOf("b","a","c"),GridRules.podiumOrder(listOf("a","b","c")))
        assertEquals(listOf("a","b"),GridRules.podiumOrder(listOf("a","b")))
        val ranked=listOf(entry("a",nota=11.0),entry("b",nota=11.0),entry("c",nota=11.0),entry("d",nota=11.0))
        assertNotNull(GridRules.tieNote(ranked))
        assertNull(GridRules.tieNote(ranked.take(3)))
        assertNull(GridRules.tieNote(ranked.take(3)+entry("e",nota=10.0)))
    }
    @Test fun filterCombinesPlatformAndGenre() {
        val entries=listOf(entry("1","NES","RPG"),entry("2","SNES","RPG"),entry("3","NES","Ação"))
        assertEquals(listOf("1"),GridRules.filter(entries,"NES","RPG").map { it.key })
        assertEquals(listOf("1","3"),GridRules.filter(entries,"NES","").map { it.key })
        assertEquals(3,GridRules.filter(entries,"","").size)
        assertEquals(listOf("NES","SNES"),GridRules.platforms(entries))
        assertEquals(listOf("Ação","RPG"),GridRules.genres(entries+entry("4",genre="")))
    }
    @Test fun statusCounterOnlyWhenSomethingNeedsAttention() {
        assertEquals("Situação",GridRules.statusLabel(GridRules.attention(0,0,0,0)))
        assertEquals("Situação · 4",GridRules.statusLabel(GridRules.attention(1,1,1,1)))
    }
}
