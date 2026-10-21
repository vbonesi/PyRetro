package com.pyretro.app

/** Baseline comum, nunca "data mais recente vence" entre saves divergentes. */
object SyncRules {
    fun direction(local:String?,remote:String?,baseline:String?):String = when {
        local==remote -> "same"
        local==null -> if(baseline==null)"download" else "conflict"
        remote==null -> if(baseline==null)"upload" else "conflict"
        baseline==null -> "conflict"
        local==baseline -> "download"
        remote==baseline -> "upload"
        else -> "conflict"
    }
    fun accepted(group:String,path:String):Boolean {
        if(path.isEmpty() || path.length>1024 || path.startsWith('/') || path.contains('\\') || path.contains(':') || path.contains('\u0000') || path.split('/').any { it in listOf("",".","..") || it.startsWith(".pyretro-") })return false
        return when(group) {
            "retro-saves" -> path.substringAfterLast('.').lowercase() in setOf("srm","sav","rtc","sra","eep","fla","mcr","mcd","dat","dsv","nv","nvm","mem")
            "retro-states" -> Regex(".*\\.state(?:[0-9]+|\\.auto)?(?:\\.png)?",RegexOption.IGNORE_CASE).matches(path)
            "retro-runtime" -> path.endsWith(".lrtl",true)
            "psp-saves" -> Regex("[A-Z]{4}[0-9]{5}[^/]*(/[^/]+)+").matches(path)
            "psp-states" -> Regex("[A-Z]{4}[0-9]{5}[^/]*\\.(ppst|jpg|png)",RegexOption.IGNORE_CASE).matches(path)
            "3ds-saves" -> Regex("Nintendo 3DS/[0-9a-f]{32}/[0-9a-f]{32}/(?:title/[0-9a-f]{8}/[0-9a-f]{8}/data|extdata/[0-9a-f]{8}/[0-9a-f]{8})/.+",RegexOption.IGNORE_CASE).matches(path)
            else -> false
        }
    }
}
