package com.pyretro.app

/** Um jogo visto pela grade: só o que Ranking e filtros precisam, sem Android. */
data class GridEntry(val key:String,val name:String,val platform:String,val genre:String,val nota:Double?)

/** Ranking, filtro por plataforma/gênero e o contador do botão Situação. */
object GridRules {
    /** Mesma ordem do Ranking da web e do modo TV: só quem tem nota, maior primeiro; empate por nome. */
    fun ranking(entries:List<GridEntry>):List<String> =
        entries.filter { it.nota!=null }.sortedWith(compareByDescending<GridEntry> { it.nota }.thenBy { it.name.lowercase() }).map { it.key }
    /** Top 3 da seleção em ordem de posição; na tela vai 2–1–3 (ver [podiumOrder]). */
    fun podiumOrder(top:List<String>):List<String> = if(top.size==3)listOf(top[1],top[0],top[2]) else top
    /** Aviso quando o quarto colocado tem a mesma nota do terceiro: a ordem entre empatados é alfabética. */
    fun tieNote(ranked:List<GridEntry>):String? {
        val last=ranked.getOrNull(2)?.nota ?: return null
        return if(ranked.getOrNull(3)?.nota==last)"Empate na nota ${TrackingRules.label(last).removeSuffix(",0")}: a ordem entre empatados é alfabética, não de preferência." else null
    }
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
