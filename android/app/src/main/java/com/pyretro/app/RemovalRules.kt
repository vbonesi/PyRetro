package com.pyretro.app
import org.json.JSONArray
import org.json.JSONObject

data class RemovalFile(val path:String,val id:String,val size:Long,val fingerprint:String) {
    fun json()=JSONObject().put("path",path).put("id",id).put("size",size).put("fingerprint",fingerprint)
}
data class RemovalPlan(val scope:String,val local:List<RemovalFile>,val drive:List<RemovalFile>,val preserved:List<String>,val blocked:List<String>,val warnings:List<String>) {
    val confirmation get()=when(scope) { "local" -> "Remover só deste celular";"drive" -> "Enviar só o Drive à lixeira";else -> "Remover do celular e enviar o Drive à lixeira" }
    val token get()=CloudRules.sha256(JSONObject().put("scope",scope).put("local",JSONArray(local.map { it.json() })).put("drive",JSONArray(drive.map { it.json() })).put("preserved",JSONArray(preserved)).toString().toByteArray())
}
object RemovalRules {
    fun plan(scope:String,local:List<RemovalFile>,remote:List<RemovalFile>?,preserved:List<String> = emptyList(),protected:List<String> = emptyList(),complete:Boolean=true):RemovalPlan {
        require(scope in setOf("local","drive","both"));val errors=protected.toMutableList();val warnings=mutableListOf<String>()
        if(!complete)errors.add("Não foi possível provar quais arquivos são exclusivos.")
        if(scope!="local" && remote==null)errors.add("Não foi possível consultar o Drive; tente novamente conectado.")
        if(scope=="local" && remote?.isEmpty()==true && local.isNotEmpty())warnings.add("Última cópia conhecida: não há cópia no Drive.")
        if(scope=="drive" && local.isEmpty() && !remote.isNullOrEmpty())warnings.add("Última cópia conhecida: não há cópia neste celular.")
        if(scope=="local" && remote==null)warnings.add("Cópia no Drive não conferida; a ROM pode ser a última cópia.")
        return RemovalPlan(scope,if(scope=="drive")emptyList() else local.sortedBy { it.path },if(scope=="local")emptyList() else remote.orEmpty().sortedBy { it.path },preserved.sorted(),errors,warnings)
    }
    fun apply(current:RemovalPlan,token:String,confirmation:String,local:(RemovalFile)->Unit,remote:(RemovalFile)->Unit):List<Pair<String,Result<Unit>>> {
        require(current.blocked.isEmpty()) { current.blocked.joinToString("\n") }
        require(current.token==token && current.confirmation==confirmation) { "Conteúdo ou confirmação mudou; confira a prévia novamente." }
        return current.local.map { "Celular: ${it.path}" to runCatching { local(it) } }+current.drive.map { "Drive: ${it.path}" to runCatching { remote(it) } }
    }
}
