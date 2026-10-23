package com.pyretro.app

/** Um jogo visto pela grade: só o que Ranking e filtros precisam, sem Android. */
data class GridEntry(val key:String,val name:String,val platform:String,val genre:String,val nota:Double?)

/** Ranking, filtro por plataforma/gênero e o contador do botão Situação. */
object GridRules {
    /** Mesma ordem do Ranking da web e do modo TV: só quem tem nota, maior primeiro; empate por nome. */
    fun ranking(entries:List<GridEntry>):List<String> =
        entries.filter { it.nota!=null }.sortedWith(compareByDescending<GridEntry> { it.nota }.thenBy { it.name.lowercase() }).map { it.key }
    fun filter(entries:List<GridEntry>,platform:String,genre:String):List<GridEntry> =
        entries.filter { (platform.isBlank() || it.platform==platform) && (genre.isBlank() || it.genre==genre) }
    /** Opções do filtro a partir do que está na coleção atual (vazio some). */
    fun platforms(entries:List<GridEntry>)=entries.map { it.platform }.filter { it.isNotBlank() }.distinct().sortedBy { it.lowercase() }
    fun genres(entries:List<GridEntry>)=entries.map { it.genre }.filter { it.isNotBlank() }.distinct().sortedBy { it.lowercase() }
    /** O que pede atenção em Situação: progresso esperando o notebook, downloads com falha,
     *  pastas ilegíveis e conflitos de save adiados. */
    fun attention(pending:Int,failedDownloads:Int,folderProblems:Int,saveConflicts:Int)=pending+failedDownloads+folderProblems+saveConflicts
    fun statusLabel(count:Int)=if(count>0)"Situação · $count" else "Situação"
}
