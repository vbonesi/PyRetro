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
    private fun le(bytes:ByteArray,at:Int,n:Int):Long { var v=0L;for(i in n-1 downTo 0)v=(v shl 8) or (bytes[at+i].toLong() and 0xff);return v }
    /** Program ID da ROM 3DS (.3ds/.cci/.cxi), como `core/game_save_ids.read_3ds_id`: só cabeçalhos
     *  NCSD/NCCH de 512 bytes, sem descriptografar. `read(offset)` devolve 512 bytes a partir dali. */
    fun programId(size:Long,read:(Long)->ByteArray):String {
        require(size>=512) { "Cabeçalho truncado." }
        var header=read(0);var available=size
        if(String(header,0x100,4,Charsets.US_ASCII)=="NCSD") {
            val offset=le(header,0x120,4)*512;val part=le(header,0x124,4)*512
            require(offset>=512 && part>=512 && offset+part<=size) { "Partição NCSD inválida." }
            header=read(offset);available=part
        }
        require(String(header,0x100,4,Charsets.US_ASCII)=="NCCH") { "Formato não suportado." }
        val content=le(header,0x104,4)*(512L shl (header[0x18e].toInt() and 0xff))
        require(content in 512..available) { "Conteúdo NCCH truncado." }
        val title=le(header,0x118,8)
        require(title ushr 32==0x00040000L && title and 0xffffffffL!=0L) { "Não é aplicação 3DS base." }
        return "%016x".format(title)
    }
    fun matches(group:String,path:String,titleId:String):Boolean {
        if(!SyncRules.accepted(group,path))return false
        if(group=="psp-saves" || group=="psp-states")return Regex("[A-Z]{4}[0-9]{5}").matches(titleId) && path.take(9).uppercase()==titleId
        if(group=="3ds-saves" && Regex("00040000[0-9a-f]{8}").matches(titleId))
            return path.lowercase().split('/').drop(3).take(4)==listOf("title",titleId.take(8),titleId.drop(8),"data")
        return false
    }
}
