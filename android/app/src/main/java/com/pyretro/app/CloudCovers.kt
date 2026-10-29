package com.pyretro.app
import org.json.JSONObject

/** Mesmo protocolo de core/cloud_covers.py. Nenhuma listagem/envio em lote. */
object CloudCovers {
    const val MAX_BYTES=8*1024*1024
    fun item(identity:String):String { require(identity.length in 1..1024);return "capas/items/"+CloudRules.sha256(identity.toByteArray())+".json" }
    fun publish(store:CloudStorage,identity:String,bytes:ByteArray) {
        require(bytes.size in 1..MAX_BYTES);val sha=CloudRules.sha256(bytes);val path="capas/blobs/$sha"
        try { store.put(path,bytes) } catch(_:CloudExists) { require(store.get(path).contentEquals(bytes)) }
        val pointer=JSONObject().put("sha256",sha).put("size",bytes.size)
        val previous=try { JSONObject(String(store.get(item(identity)),Charsets.UTF_8)) } catch(_:CloudNotFound) { null }
        if(!JournalRules.same(pointer,previous))store.put(item(identity),pointer.toString().toByteArray(),overwrite=true)
    }
    fun get(store:CloudStorage,identity:String):ByteArray {
        val pointer=JSONObject(String(store.get(item(identity)),Charsets.UTF_8));val sha=pointer.getString("sha256")
        require(Regex("[a-f0-9]{64}").matches(sha));val bytes=store.get("capas/blobs/$sha")
        require(bytes.size in 1..MAX_BYTES && bytes.size.toLong()==pointer.getLong("size") && CloudRules.sha256(bytes)==sha) { "Capa não confere; cache anterior preservado." };return bytes
    }
}
