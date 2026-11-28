package com.pyretro.app

/** Filtros rápidos da Biblioteca, com os mesmos nomes do PC (Neste PC vira Neste celular). */
enum class QuickFilter(val label: String) {
    TUDO("Tudo"), JOGANDO("Jogando"), NESTE_CELULAR("Neste celular"), FAVORITOS("Favoritos"), RANKING("Ranking"), FINALIZADOS("Finalizados")
}

/** Um jogo visto pela Biblioteca: só o que filtros e Ranking precisam, sem Android. */
data class LibEntry(val key: String, val name: String, val platform: String = "", val onPhone: Boolean = false, val started: Boolean = false,
    val finished: Boolean = false, val favorite: Boolean = false, val nota: Double? = null, val genre: String = "", val inside: String = "")

object LibraryRules {
    private fun collator() = java.text.Collator.getInstance(java.util.Locale.forLanguageTag("pt-BR")).apply { strength = java.text.Collator.PRIMARY }

    fun matches(entry: LibEntry, filter: QuickFilter) = when (filter) {
        QuickFilter.TUDO -> true
        QuickFilter.JOGANDO -> entry.started && !entry.finished
        QuickFilter.NESTE_CELULAR -> entry.onPhone
        QuickFilter.FAVORITOS -> entry.favorite
        QuickFilter.RANKING -> entry.nota != null
        QuickFilter.FINALIZADOS -> entry.finished
    }

    /** Chaves na ordem de exibição: Ranking pela nota (mesma regra da grade); o resto por nome. */
    fun apply(entries: List<LibEntry>, filter: QuickFilter): List<String> {
        val picked = entries.filter { matches(it, filter) }
        if (filter == QuickFilter.RANKING) return GridRules.ranking(picked.map { GridEntry(it.key, it.name, it.platform, "", it.nota) })
        val c = collator()
        return picked.sortedWith { a, b -> c.compare(a.name, b.name).takeIf { it != 0 } ?: c.compare(a.platform, b.platform) }.map { it.key }
    }

    /** Busca pelo nome entre os jogos carregados (também plataforma e gênero, como a tela antiga); sem acento e sem diferença de caixa. */
    fun search(entries: List<LibEntry>, query: String, limit: Int = 200): List<String> {
        val q = GameLogic.normalized(query)
        if (q.isEmpty()) return emptyList()
        val c = collator()
        return entries.filter { GameLogic.normalized(it.name + it.platform + it.genre + it.inside).contains(q) }
            // nome que começa pelo termo vem antes do que só o contém; achado só dentro de coletânea vem por último
            .sortedWith(compareBy<LibEntry> { !GameLogic.normalized(it.name).startsWith(q) }.thenBy { !GameLogic.normalized(it.name + it.platform + it.genre).contains(q) }.thenComparator { a, b -> c.compare(a.name, b.name) })
            .take(limit).map { it.key }
    }

    fun counts(entries: List<LibEntry>) = QuickFilter.values().associateWith { f -> entries.count { matches(it, f) } }

    /** LB/RB: gira pelos filtros, sem parar nas pontas. */
    fun step(current: QuickFilter, delta: Int): QuickFilter {
        val all = QuickFilter.values(); return all[(current.ordinal + delta + all.size) % all.size]
    }
}

/** Moldura 3:4 das capas (igual ao modo TV, N10): perto da proporção preenche com corte; o resto fica inteiro sobre fundo desfocado. */
enum class CoverFit { CROP, FIT }
object CoverRules {
    fun fit(width: Int, height: Int): CoverFit {
        if (width <= 0 || height <= 0) return CoverFit.FIT
        val ratio = width.toDouble() / height
        return if (ratio >= 0.62 && ratio <= 0.9) CoverFit.CROP else CoverFit.FIT
    }
}
