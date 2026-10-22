package com.pyretro.app

/** Saves/estados do RetroArch que pertencem a um jogo, com a pasta por sistema
 *  (`saves/<sistema>/<rom>.srm`, inclusive subpasta do core, como `ARCADE/fbneo/`).
 *  Só sufixo de extensão vale: "Super Mario Bros" não leva "Super Mario Bros. 3.srm".
 *  Arquivos soltos na raiz ficam de fora: o mesmo nome pode ser de outro sistema. */
object SaveRules {
    private val suffix=Regex("[A-Za-z0-9]+(\\.[A-Za-z0-9]+){0,2}")
    fun belongs(path:String,code:String,label:String):Boolean {
        val parts=path.split('/');if(parts.size<2 || parts.first()!=code || label.isBlank())return false
        val name=parts.last();if(!name.startsWith("$label."))return false
        return suffix.matches(name.removePrefix("$label."))
    }
    /** Nome do conteúdo como o RetroArch usa: arquivo sem extensão conhecida. */
    fun label(fileName:String,extensions:Set<String>):String {
        val extension=fileName.substringAfterLast('.',"").lowercase()
        return if(extension in extensions)fileName.substringBeforeLast('.') else fileName
    }
}
