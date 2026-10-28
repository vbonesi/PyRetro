package com.pyretro.app

/** O destino não existe na nuvem. */
class CloudNotFound(message:String):Exception(message)
/** O destino já existe e não foi pedido sobrescrever. */
class CloudExists(message:String):Exception(message)

data class CloudEntry(val path:String,val size:Long)

/**
 * Armazenamento em nuvem independente de provedor (mesmo contrato de `core/cloud.py` no notebook).
 * `put` recusa sobrescrever a menos que `overwrite`; `trash` manda para a lixeira do provedor.
 */
interface CloudStorage {
    fun list(prefix:String=""):List<CloudEntry>
    fun exists(path:String):Boolean
    fun get(path:String):ByteArray
    fun put(path:String,data:ByteArray,overwrite:Boolean=false)
    fun trash(path:String)

    companion object {
        /** Mesma validação do notebook: caminho relativo, sem `..`, vazios, barra invertida ou NUL. */
        fun clean(path:String):String {
            require(path.isNotEmpty() && !path.startsWith("/") && '\\' !in path && '\u0000' !in path && path.split('/').none { it.isEmpty() || it=="." || it==".." }) { "caminho remoto inválido: $path" }
            return path
        }
    }
}

class MemoryCloudStorage:CloudStorage {
    val files=sortedMapOf<String,ByteArray>()
    val trashed=mutableListOf<String>()
    override fun list(prefix:String):List<CloudEntry> {
        val base=if(prefix.isEmpty())"" else prefix.trimEnd('/')+"/"
        return files.filterKeys { it.startsWith(base) }.map { CloudEntry(it.key,it.value.size.toLong()) }
    }
    override fun exists(path:String)=CloudStorage.clean(path) in files
    override fun get(path:String):ByteArray=files[CloudStorage.clean(path)] ?: throw CloudNotFound(path)
    override fun put(path:String,data:ByteArray,overwrite:Boolean) {
        CloudStorage.clean(path)
        if(path in files && !overwrite)throw CloudExists(path)
        files[path]=data.copyOf()
    }
    override fun trash(path:String) { CloudStorage.clean(path);files.remove(path)?.let { trashed.add(path) } }
}
