package com.pyretro.app

object GlyphRules {
    val choices=listOf("auto","xbox","ps","generic")
    fun family(preference:String,names:List<String>):String {
        if(preference in choices && preference!="auto")return preference
        val name=names.joinToString(" ").lowercase()
        return when { listOf("sony","playstation","dualshock","dualsense","wireless controller").any { it in name } -> "ps"
            listOf("xbox","gamesir","galileo","g8").any { it in name } -> "xbox"
            else -> "generic" }
    }
    fun key(family:String,key:String):String = if(family=="ps")mapOf("A" to "✕","B" to "○","X" to "□","Y" to "△","LB" to "L1","RB" to "R1","Menu" to "Options")[key] ?: key else key
    fun label(preference:String,family:String):String=when(preference) { "auto" -> "Automático (${label(family,family)})";"ps" -> "PlayStation";"xbox" -> "Xbox";else -> "Genérico" }
}
