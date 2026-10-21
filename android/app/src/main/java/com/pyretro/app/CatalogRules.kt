package com.pyretro.app

/** Só associa candidatos únicos nos dois sentidos; edições homônimas ficam para escolha. */
object CatalogRules {
    fun match(wanted:Map<String,Set<String>>,files:Map<String,String>):Map<String,String> {
        val matches=wanted.mapValues { (_,names) -> files.filterValues { GameLogic.normalized(GameLogic.fileLabel(it)) in names }.keys }
        val owners=matches.values.flatten().groupingBy { it }.eachCount()
        return matches.mapNotNull { (key,uris) -> uris.singleOrNull()?.takeIf { owners[it]==1 }?.let { key to it } }.toMap()
    }
}
