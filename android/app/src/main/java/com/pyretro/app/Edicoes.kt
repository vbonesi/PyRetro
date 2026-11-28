package com.pyretro.app

import org.json.JSONObject

/**
 * Cards unificados (F2b, 28/11/2026), espelho de core/edicoes.py. O card que fica traz `tipo_card` ("versao" ou "colecao"),
 * `edicoes` (cada entrada: id, nome, plataforma, tipo, fontes, rom, progresso) e `ids_antigos`. Sem Android.
 */
data class Edicao(val nome: String, val plataforma: String, val tipo: String, val rom: String?, val progresso: String)

object Edicoes {
    fun colecao(tracking: JSONObject) = tracking.optString("tipo_card") == "colecao"
    fun versao(tracking: JSONObject) = tracking.optString("tipo_card") == "versao"

    fun lista(tracking: JSONObject): List<Edicao> {
        val a = tracking.optJSONArray("edicoes") ?: return emptyList()
        return (0 until a.length()).mapNotNull { a.optJSONObject(it) }.map { e ->
            Edicao(e.optString("nome"), e.optString("plataforma").takeUnless { e.isNull("plataforma") }.orEmpty(), e.optString("tipo"),
                e.optString("rom").takeIf { !e.isNull("rom") && it.startsWith("rom:") }, progresso(e.optJSONObject("progresso")))
        }
    }

    /** "finalizado · nota 8,5 · 3h": só o que o card absorvido tinha. */
    fun progresso(p: JSONObject?): String {
        if (p == null) return ""
        val partes = mutableListOf<String>()
        if (p.optBoolean("platinado")) partes += "platinado" else if (p.optBoolean("finalizado")) partes += "finalizado" else if (p.optBoolean("iniciado")) partes += "iniciado"
        if (p.has("nota") && !p.isNull("nota")) partes += "nota " + TrackingRules.label(p.optDouble("nota"))
        if (p.has("observacoes") && p.optString("observacoes").isNotBlank()) partes += "com observações"
        return partes.joinToString(" · ")
    }

    /** Código de sistema retrô de uma entrada de coleção com ROM (Rondo of Blood PCECD): o card da coleção passa a baixar essa ROM. */
    fun codigoRetro(tracking: JSONObject): String? =
        if (!colecao(tracking)) null else lista(tracking).firstNotNullOfOrNull { it.rom?.removePrefix("rom:")?.takeIf { c -> OndeRoda.retro(c) } }

    /** O jogo jogável de uma entrada de coleção com ROM retrô (ex.: Advance Wars dentro de Advance Wars 1+2): casa código e título entre os jogos carregados, menos o próprio card. */
    fun jogoDaEdicao(games: List<Game>, card: Game, e: Edicao): Game? {
        val code = e.rom?.removePrefix("rom:")?.takeIf { OndeRoda.retro(it) } ?: return null
        val alvo = CloudCatalog.titleKey(e.nome)
        return games.filter { it.key != card.key && it.code == code && (it.drive || it.localUri != null) }
            .firstOrNull { CloudCatalog.titleKey(it.name) == alvo || it.aliases.any { a -> CloudCatalog.titleKey(a) == alvo } }
    }

    /** Chaves antigas (`pc:<id>`) -> chave do card que ficou, para favoritos, recentes e tempo seguirem a unificação. */
    fun aliases(games: List<Game>): Map<String, String> = games.filter { it.id.isNotBlank() }.flatMap { g ->
        val ids = g.tracking.optJSONArray("ids_antigos") ?: return@flatMap emptyList()
        (0 until ids.length()).map { ids.optString(it) }.filter { it.isNotBlank() && it != g.id }.map { "pc:$it" to g.key }
    }.toMap()
}
