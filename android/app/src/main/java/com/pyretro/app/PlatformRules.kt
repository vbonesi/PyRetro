package com.pyretro.app

import java.text.Normalizer

/** Resolve plataforma/código para o selo (dados em PlatformData, gerados do mesmo manifesto da web e do modo TV). */
object PlatformRules {
    private fun key(text:String?):String=Normalizer.normalize(text.orEmpty(),Normalizer.Form.NFD).replace(Regex("\\p{M}+"),"").lowercase().replace(Regex("[^a-z0-9]+")," ").trim()
    private val index:Map<String,PlatformInfo> by lazy {
        val map=LinkedHashMap<String,PlatformInfo>()
        for(p in PlatformData.all.drop(1))for(name in listOf(p.id,p.name)+p.aliases)key(name).takeIf { it.isNotEmpty() }?.let { map.putIfAbsent(it,p) }
        map
    }
    /** O primeiro nome que casar vence; sem casar, selo neutro com as três primeiras letras. */
    fun find(vararg names:String?):PlatformInfo {
        for(name in names)index[key(name)]?.let { return it }
        val fallback=PlatformData.all.first();val first=names.firstOrNull { !it.isNullOrBlank() }.orEmpty()
        val letters=first.filter { it.isLetterOrDigit() }.take(3).uppercase()
        return fallback.copy(name=first.ifBlank { fallback.name },short=letters.ifBlank { fallback.short })
    }
}
