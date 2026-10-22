package com.pyretro.app

/** Um jogo visto pelo Início: só o que as fileiras precisam, sem Android. */
data class HomeEntry(val key:String,val name:String,val onPhone:Boolean,val started:Boolean,val finished:Boolean,
    val favorite:Boolean,val playedAt:Long,val seconds:Long)

/** Fileiras do Início. Tudo vem do cache e das preferências do celular, então funciona igual
 *  online e offline. Fileira vazia não aparece; cada uma tem no máximo [limit] jogos. */
object HomeRules {
    fun rows(entries:List<HomeEntry>,limit:Int=15):List<Pair<String,List<String>>> {
        val recent=compareByDescending<HomeEntry> { it.playedAt }.thenBy { it.name.lowercase() }
        val rows=listOf(
            "Continuar jogando" to entries.filter { it.started && !it.finished }.sortedWith(compareByDescending<HomeEntry> { it.onPhone }.then(recent)),
            "Recentes" to entries.filter { it.playedAt>0 }.sortedWith(recent),
            "Mais jogados" to entries.filter { it.seconds>0 }.sortedWith(compareByDescending<HomeEntry> { it.seconds }.thenBy { it.name.lowercase() }),
            "Favoritos" to entries.filter { it.favorite }.sortedWith(compareByDescending<HomeEntry> { it.onPhone }.then(recent)),
            "Prontos no celular" to entries.filter { it.onPhone }.sortedWith(recent)
        )
        return rows.map { (title,list) -> title to list.take(limit).map { it.key } }.filter { it.second.isNotEmpty() }
    }
}
