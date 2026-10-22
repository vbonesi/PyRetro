package com.pyretro.app

import java.text.Normalizer
import java.security.MessageDigest

object GameLogic {
    fun normalized(value: String): String = Normalizer.normalize(value, Normalizer.Form.NFD)
        .replace("\\p{M}+".toRegex(), "").lowercase().replace("[^a-z0-9]".toRegex(), "")
    fun fileLabel(name: String): String = name.substringBeforeLast('.', name)
    fun localKey(code:String,uri:String):String = "local:$code:"+MessageDigest.getInstance("SHA-256").digest(uri.toByteArray()).joinToString("") { "%02x".format(it) }
    fun exactFile(title: String, aliases: List<String>, names: List<String>): String? {
        val wanted = (aliases + title).map(::normalized).toSet()
        return names.filter { normalized(fileLabel(it)) in wanted }.singleOrNull()
    }
    fun progress(field: String, value: Boolean): Map<String, Boolean> {
        val fields = listOf("iniciado", "finalizado", "platinado")
        require(field in fields)
        val index = fields.indexOf(field)
        return fields.filterIndexed { i, _ -> if (value) i <= index else i >= index }.associateWith { value }
    }
    fun offerRemoval(wasFinished:Boolean, isFinished:Boolean, hasLocalRom:Boolean):Boolean = !wasFinished && isFinished && hasLocalRom
    fun remotePackage(platform: String): String? = when(platform) {
        "PlayStation 4", "PlayStation 5" -> "com.playstation.remoteplay"
        "Xbox", "Xbox One", "Xbox Series S", "Xbox Series X" -> "com.grill.xbxplay"
        else -> null
    }
    /** Switch não tem cliente no celular: o notebook abre o SysDVR e o Moonlight transmite. */
    fun streamedThroughNotebook(platform: String): Boolean = platform in setOf("Nintendo Switch", "Switch")
}
