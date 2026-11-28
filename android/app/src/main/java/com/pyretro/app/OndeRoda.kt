package com.pyretro.app

import org.json.JSONObject

/**
 * "Onde jogar" (plano de 27/11/2026), espelho de core/onde_roda.py e de tv/state.js: fora do retrô o card não carrega ROM,
 * só diz em que plataformas o jogo existe. Ordem e rótulos iguais aos do modo TV. Sem Android.
 */
object OndeRoda {
    val PLATAFORMAS = listOf("switch" to "Switch", "ps4" to "PS4", "xbox" to "Xbox", "pc" to "PC", "switch2" to "Switch 2")

    /** Sistemas que continuam no Drive e que o celular baixa (core/onde_roda.py: SISTEMAS_RETRO). */
    val RETRO = setOf("FC", "SFC", "MD", "SMS", "GG", "GB", "GBC", "GBA", "N64", "PCE", "PCECD", "ARCADE")
    fun retro(code: String) = code in RETRO

    /** Plataformas em que o jogo existe, na ordem do modo TV. */
    fun existe(tracking: JSONObject): List<Pair<String, String>> {
        val mapa = tracking.optJSONObject("onde_roda") ?: return emptyList()
        return PLATAFORMAS.filter { (id, _) -> mapa.optJSONObject(id)?.let { it.has("existe") && it.optBoolean("existe", false) } == true }
    }

    /** Selos: "✓ " marca onde o Victor tem o jogo; sem plataforma conhecida, "♡ Quero jogar". */
    fun selos(tracking: JSONObject): List<String> {
        val jogar = tracking.optJSONObject("jogar")
        val tenho = jogar?.optString("estado") == "tenho"
        val plataforma = jogar?.optString("plataforma").orEmpty()
        val lista = existe(tracking).map { (id, label) -> (if (tenho && plataforma == id) "✓ " else "") + label }
        return if (lista.isEmpty() && jogar?.optString("estado") == "quero") listOf("♡ Quero jogar") else lista
    }

    /** Tamanhos aproximados (GB) por plataforma, para a ficha. */
    fun detalhe(tracking: JSONObject): String {
        val mapa = tracking.optJSONObject("onde_roda") ?: return ""
        return existe(tracking).joinToString(" · ") { (id, label) ->
            val gb = mapa.optJSONObject(id)?.takeIf { it.has("gb") && !it.isNull("gb") }?.optDouble("gb")
            label + (gb?.let { " ~" + (if (it % 1.0 == 0.0) it.toInt().toString() else it.toString().replace('.', ',')) + " GB" } ?: "")
        }
    }
}
