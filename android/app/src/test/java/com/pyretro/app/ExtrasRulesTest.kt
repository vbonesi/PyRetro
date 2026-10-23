package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

/** Desejados, horas, destino da capa e campos alterados na edição. */
class ExtrasRulesTest {
    @Test fun wishlistSortedByNameAcrossStores() {
        val list=ExtrasRules.sorted(listOf(WishItem("b","steam","Zelda","",""),WishItem("a","psn","astro","/library-images/capas/a.png","Ação")))
        assertEquals(listOf("astro","Zelda"),list.map { it.name })
        assertEquals("wish:steam:b",ExtrasRules.wishKey(list[1]))
    }
    @Test fun hoursLikeTvMode() {
        assertEquals("20 h",ExtrasRules.hours(20.2))
        assertEquals("1 dia e 6 h (30 h)",ExtrasRules.hours(30.0))
        assertEquals("190 dias e 12 h (4572 h)",ExtrasRules.hours(4572.0))
    }
    @Test fun coverTargetFromUrl() {
        assertEquals(CoverTarget("rom",code="SFC",label="Final Fantasy VI"),ExtrasRules.coverTarget("x","/images/SFC/Final%20Fantasy%20VI.png?v=12"))
        assertEquals(CoverTarget("biblioteca",id="x"),ExtrasRules.coverTarget("x","/library-images/capas/x.png"))
        assertNull(ExtrasRules.coverTarget("",""))
    }
    @Test fun onlyChangedFieldsAndEmptyClears() {
        val out=ExtrasRules.changes(mapOf("genero" to "Ação","observacoes" to "velho","tempo" to ""),mapOf("genero" to "Ação ","observacoes" to "","tempo" to "10:00:00"))
        assertEquals(mapOf("observacoes" to null,"tempo" to "10:00:00"),out)
    }
}
