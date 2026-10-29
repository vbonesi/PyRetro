package com.pyretro.app
import org.json.JSONArray
import org.json.JSONObject

/** Leituras da mesma Biblioteca, inclusive offline. */
object LibraryView {
    fun wishlist(data:JSONObject):List<WishItem> = ExtrasRules.sorted(JournalRules.games(data).values.flatMap { game ->
        val sources=game.optJSONArray("fontes") ?: JSONArray()
        (0 until sources.length()).map(sources::optString).filter { it.startsWith("wishlist:") }.map { it.removePrefix("wishlist:") }.filter { it in ExtrasRules.STORES }.distinct()
            .map { WishItem(game.getString("id"),it,game.getString("nome"),"cloud-cover:"+game.getString("id"),game.optString("genero").takeUnless { game.isNull("genero") }.orEmpty()) }
    })
    fun stats(data:JSONObject):JSONObject {
        val rows=JournalRules.games(data).values.filter { !it.optBoolean("oculto") };val notes=rows.mapNotNull { (it.opt("nota") as? Number)?.toDouble() }
        fun hours(value:String):Double { val match=Regex("([0-9]+):([0-5][0-9])(?::([0-5][0-9]))?").matchEntire(value) ?: return 0.0
            return match.groupValues[1].toDouble()+match.groupValues[2].toInt()/60.0+(match.groupValues[3].toIntOrNull() ?: 0)/3600.0 }
        return JSONObject().put("total",rows.size).put("zerados",rows.count { it.optBoolean("finalizado") }).put("platinados",rows.count { it.optBoolean("platinado") })
            .put("jogando",rows.count { it.optBoolean("iniciado") && !it.optBoolean("finalizado") }).put("com_nota",notes.size)
            .put("nota_media",if(notes.isEmpty())JSONObject.NULL else notes.average()).put("com_genero",rows.count { !it.isNull("genero") && it.optString("genero").isNotBlank() })
            .put("tempo_total_horas",rows.sumOf { game -> hours(game.optString("tempo"))+(game.optJSONObject("_play_sessions")?.let { s -> s.keys().asSequence().sumOf { s.optLong(it) } } ?: 0)/3600.0 })
    }
    fun leaveWishlist(data:JSONObject,item:WishItem,bought:Boolean):JSONObject {
        val out=JournalRules.copy(data);val games=JournalRules.games(out);val game=games[item.id] ?: error("Jogo ausente da Biblioteca local.")
        val sources=game.optJSONArray("fontes") ?: JSONArray();val old=(0 until sources.length()).map(sources::getString)
        require("wishlist:${item.source}" in old) { "Este jogo já saiu desta lista; atualize os Desejados." }
        val next=(old-"wishlist:${item.source}"+(if(bought)listOf(item.source) else emptyList())).distinct()
        if(next.isEmpty())games.remove(item.id) else {
            game.put("fontes",JSONArray(next))
            if(bought && old.all { it.startsWith("wishlist:") } && game.optString("plataforma") in setOf("PSN","Steam","Xbox"))game.put("plataforma",if(item.source=="psn")"PlayStation 4" else ExtrasRules.STORES.getValue(item.source))
        }
        return out.put("games",JSONArray(games.values.toList()))
    }
}
