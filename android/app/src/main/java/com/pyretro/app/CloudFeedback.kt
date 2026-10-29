package com.pyretro.app

/** Resultado que a interface pode confirmar. Falha de grupo não desaparece como lista vazia. */
data class CloudFeedback(val complete:Boolean,val message:String) {
    companion object {
        fun batch(action:()->Map<String,Result<List<CloudResult>>>):CloudFeedback = runCatching {
            val groups=action();val errors=mutableListOf<String>();var completed=0;var conflicts=0
            for((group,result) in groups)result.fold({ rows -> for(row in rows) {
                when { row.conflict!=null -> conflicts++
                    !row.ok -> errors.add("${row.path}: ${row.error ?: "não foi concluído"}")
                    else -> completed++ }
            } },{ error -> errors.add("$group: ${error.message ?: "falha na sincronização"}") })
            val complete=errors.isEmpty() && conflicts==0
            CloudFeedback(complete,if(complete)"Saves na nuvem: $completed arquivo(s) conferido(s). Tudo em dia."
                else "$completed arquivo(s) conferido(s) · $conflicts conflito(s) · ${errors.size} erro(s)."+
                    errors.takeIf { it.isNotEmpty() }?.joinToString("\n",prefix="\n").orEmpty()+"\nCorrija o problema e tente novamente. As versões não resolvidas foram preservadas.")
        }.getOrElse { CloudFeedback(false,"Não foi possível sincronizar: ${it.message ?: "falha desconhecida"}. Tente novamente.") }

        fun resolve(success:String,action:()->CloudResult):CloudFeedback = runCatching {
            val result=action()
            if(result.ok && result.conflict==null)CloudFeedback(true,success)
            else CloudFeedback(false,"Não foi possível resolver ${result.path}: ${result.error ?: "o conflito continua pendente"}. Tente novamente.")
        }.getOrElse { CloudFeedback(false,"Não foi possível resolver: ${it.message ?: "falha desconhecida"}. Tente novamente.") }
    }
}
