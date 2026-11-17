package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class LibraryRulesTest {
    private val list = listOf(
        LibEntry("a", "Zelda", "NES", onPhone = true, started = true, favorite = true, nota = 9.0),
        LibEntry("b", "álbum", "GBA", started = true, finished = true, nota = 10.0),
        LibEntry("c", "Mario", "N64", onPhone = true),
        LibEntry("d", "Metroid", "SNES", favorite = true, nota = 9.0),
    )

    @Test fun `filtros rapidos tem os nomes do PC`() {
        assertEquals(listOf("Tudo", "Jogando", "Neste celular", "Favoritos", "Ranking", "Finalizados"), QuickFilter.values().map { it.label })
    }
    @Test fun `cada filtro separa o que o nome promete`() {
        assertEquals(listOf("a"), LibraryRules.apply(list, QuickFilter.JOGANDO))          // iniciado e não finalizado
        assertEquals(listOf("c", "a"), LibraryRules.apply(list, QuickFilter.NESTE_CELULAR))
        assertEquals(listOf("d", "a"), LibraryRules.apply(list, QuickFilter.FAVORITOS))
        assertEquals(listOf("b"), LibraryRules.apply(list, QuickFilter.FINALIZADOS))
    }
    @Test fun `tudo ordena por nome sem acento e ranking pela nota`() {
        assertEquals(listOf("b", "c", "d", "a"), LibraryRules.apply(list, QuickFilter.TUDO))
        assertEquals(listOf("b", "d", "a"), LibraryRules.apply(list, QuickFilter.RANKING))  // 10, depois 9 por nome (Metroid, Zelda)
    }
    @Test fun `contagens batem com os filtros`() {
        val counts = LibraryRules.counts(list)
        assertEquals(4, counts[QuickFilter.TUDO]); assertEquals(1, counts[QuickFilter.JOGANDO]); assertEquals(2, counts[QuickFilter.NESTE_CELULAR])
        assertEquals(2, counts[QuickFilter.FAVORITOS]); assertEquals(3, counts[QuickFilter.RANKING]); assertEquals(1, counts[QuickFilter.FINALIZADOS])
    }
    @Test fun `LB e RB giram pelos filtros sem parar nas pontas`() {
        assertEquals(QuickFilter.JOGANDO, LibraryRules.step(QuickFilter.TUDO, 1))
        assertEquals(QuickFilter.FINALIZADOS, LibraryRules.step(QuickFilter.TUDO, -1))
        assertEquals(QuickFilter.TUDO, LibraryRules.step(QuickFilter.FINALIZADOS, 1))
    }
    @Test fun `capa perto de 3 por 4 corta e o resto fica inteiro`() {
        assertEquals(CoverFit.CROP, CoverRules.fit(300, 400)); assertEquals(CoverFit.CROP, CoverRules.fit(620, 1000)); assertEquals(CoverFit.CROP, CoverRules.fit(900, 1000))
        assertEquals(CoverFit.FIT, CoverRules.fit(1000, 1000)); assertEquals(CoverFit.FIT, CoverRules.fit(1500, 1000))
        assertEquals(CoverFit.FIT, CoverRules.fit(300, 600)); assertEquals(CoverFit.FIT, CoverRules.fit(0, 0))
    }
}
