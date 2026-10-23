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
    /** A pasta RetroArch é a raiz (com `saves/` e `states/` dentro). Escolher `saves` ou
     *  `states` levaria a `saves/saves/` e o save do notebook pareceria faltar no celular. */
    fun retroarchFolderProblem(documentId:String):String? {
        val last=documentId.substringAfterLast(':').trimEnd('/').substringAfterLast('/').lowercase()
        return if(last in setOf("saves","states"))"Essa é a pasta \"$last\". Volte um nível e escolha a pasta RetroArch, que contém saves e states." else null
    }
    /** Nome do conteúdo como o RetroArch usa: arquivo sem extensão conhecida. */
    fun label(fileName:String,extensions:Set<String>):String {
        val extension=fileName.substringAfterLast('.',"").lowercase()
        return if(extension in extensions)fileName.substringBeforeLast('.') else fileName
    }
}

/** Saves de PSP/3DS por jogo, pelo ID do título (contrato `docs/mobile-save-ids.md`, espelho de
 *  `core/game_save_ids.matches`). Extdata do 3DS nunca entra: é outro identificador. */
object SaveIdRules {
    fun groups(code:String)=when(code) { "PSP" -> listOf("psp-saves","psp-states");"3DS" -> listOf("3ds-saves");else -> emptyList() }
    fun valid(code:String,titleId:String)=when(code) { "PSP" -> Regex("[A-Z]{4}[0-9]{5}").matches(titleId);"3DS" -> Regex("00040000[0-9a-f]{8}").matches(titleId);else -> false }
    /** Árvores `Nintendo 3DS/<ID0>/<ID1>` que têm saves do título; mais de uma exige escolha. */
    fun trees(paths:Collection<String>,titleId:String)=paths.filter { matches("3ds-saves",it,titleId) }.map { it.split('/').take(3).joinToString("/") }.distinct().sorted()
    fun matches(group:String,path:String,titleId:String):Boolean {
        if(!SyncRules.accepted(group,path))return false
        if(group=="psp-saves" || group=="psp-states")return Regex("[A-Z]{4}[0-9]{5}").matches(titleId) && path.take(9).uppercase()==titleId
        if(group=="3ds-saves" && Regex("00040000[0-9a-f]{8}").matches(titleId))
            return path.lowercase().split('/').drop(3).take(4)==listOf("title",titleId.take(8),titleId.drop(8),"data")
        return false
    }
}
