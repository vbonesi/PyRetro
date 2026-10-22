package com.pyretro.app

import java.net.URLDecoder
import java.net.URLEncoder

/** ROM entregue pelo notebook: arquivo do acervo ou streaming do Drive pelo rclone.
 *  Guardada em `cloud:<chave>` como `pyretro-rom:<sistema>/<arquivo>?etag=…&size=…`; o endereço
 *  do notebook não entra na origem, então trocar LAN ↔ Tailscale não invalida a fila. */
data class RomRef(val code:String,val file:String,val etag:String,val size:Long) {
    val name get()=file.substringAfterLast('/')
    fun encoded()="${RomSource.PREFIX}${enc(code)}/${enc(file)}?etag=${enc(etag)}&size=$size"
    fun query()="code=${enc(code)}&file=${enc(file)}&etag=${enc(etag)}"
    private fun enc(value:String)=URLEncoder.encode(value,"UTF-8")
}
data class RomOption(val file:String,val size:Long,val etag:String,val source:String)

object RomSource {
    const val PREFIX="pyretro-rom:"
    fun parse(value:String?):RomRef? {
        if(value==null || !value.startsWith(PREFIX))return null
        return runCatching {
            val body=value.removePrefix(PREFIX);val path=body.substringBefore('?')
            val query=body.substringAfter('?',"").split('&').filter { it.contains('=') }.associate { it.substringBefore('=') to dec(it.substringAfter('=')) }
            val code=dec(path.substringBefore('/'));val file=dec(path.substringAfter('/',""))
            require(code.isNotEmpty() && file.isNotEmpty() && file.split('/').none { it in setOf("",".","..") } && !file.contains('\\'))
            RomRef(code,file,query.getValue("etag"),query.getValue("size").toLong().also { require(it>0) })
        }.getOrNull()
    }
    /** Formatos que o celular abre sozinhos; CUE/M3U dependem de outros arquivos. */
    fun playable(options:List<RomOption>,accepts:(String)->Boolean)=options.filter { option ->
        val extension=option.file.substringAfterLast('.').lowercase()
        option.size>0 && accepts(option.file.substringAfterLast('/')) && extension !in setOf("cue","m3u")
    }
    private fun dec(value:String)=URLDecoder.decode(value,"UTF-8")
}
