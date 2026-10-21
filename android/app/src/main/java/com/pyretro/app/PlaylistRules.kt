package com.pyretro.app

object PlaylistRules {
    fun path(documentId:String):String {
        val parts=documentId.split(':',limit=2)
        require(parts.size==2 && parts[0].isNotEmpty() && parts[1].split('/').none { it in listOf(".","..") } && !parts[1].contains('\\'))
        return (if(parts[0]=="primary")"/storage/emulated/0/" else "/storage/${parts[0]}/")+parts[1]
    }
    /** Só remove entradas da raiz e do sistema escolhidos; outras ficam intactas. */
    fun removed(existing:List<String>,local:Set<String>,root:String,extensions:Set<String>):Set<String> = existing.filter { path ->
        path.startsWith(root.trimEnd('/')+"/") && path.substringAfterLast('.').lowercase() in extensions && path !in local
    }.toSet()
}
