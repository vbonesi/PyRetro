package com.pyretro.app

/** Mudanças em preferências para seguir ROMs renomeadas no PC (/api/tv/key_aliases). */
data class KeyMigration(val puts:Map<String,Any>,val removes:Set<String>)

/**
 * Regras puras (testáveis sem Android). Prefixos por jogo: favorito/fixado/tempo/
 * pendência/ROM escolhida/vínculo de nuvem/conflito. Nunca descarta dado: tempo
 * soma, favorito vale se qualquer um for, o resto mantém o que já existir na chave nova.
 * `rekey` troca o campo "key" dentro dos JSON de pendência/sessão.
 */
object KeyAliases {
    private val prefixes=listOf("favorite:","keep:","time:","pending:","rom:","cloud:","conflict:")
    fun plan(prefs:Map<String,*>,aliases:Map<String,String>,rekey:(String,String)->String):KeyMigration {
        val puts=linkedMapOf<String,Any>();val removes=mutableSetOf<String>()
        fun current(name:String):Any?=if(name in removes)null else puts[name] ?: prefs[name]
        for((old,new) in aliases) {
            if(old==new)continue
            for(prefix in prefixes) {
                val from=prefix+old;val value=prefs[from] ?: continue;val to=prefix+new;val existing=current(to)
                val merged:Any=when {
                    existing==null -> if(prefix=="pending:" && value is String)rekey(value,new) else value
                    prefix=="time:" && value is Long && existing is Long -> existing+value
                    prefix=="favorite:" && value is Boolean && existing is Boolean -> existing || value
                    else -> existing
                }
                puts[to]=merged;removes.add(from);puts.remove(from)
            }
        }
        // Sessões de tempo ainda não enviadas carregam a chave no próprio registro.
        for((name,value) in prefs) if(name.startsWith("time-event:") && value is String) {
            val key=Regex("\"key\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").find(value)?.groupValues?.get(1) ?: continue
            aliases[key]?.takeIf { it!=key }?.let { puts[name]=rekey(value,it) }
        }
        return KeyMigration(puts,removes-puts.keys)
    }
}
