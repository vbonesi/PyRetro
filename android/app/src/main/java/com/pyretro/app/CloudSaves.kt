package com.pyretro.app

import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/** Os arquivos locais de um grupo de saves (no Android, uma pasta SAF; nos testes, memória). */
interface LocalFiles {
    /** {caminho relativo: sha256}. */
    fun hashes():Map<String,String>
    fun read(rel:String):ByteArray
    /** Grava o arquivo; se já existia, guarda a versão anterior no histórico antes de substituir. */
    fun write(rel:String,data:ByteArray)
}

data class CloudItem(val path:String,val action:String,val local:String?,val baseline:String?,val heads:Map<String,List<String>>)
data class CloudResult(val path:String,val action:String,val ok:Boolean,val error:String?=null,val conflict:Map<String,List<String>>?=null)

object CloudRules {
    private val skipDirs=setOf(".pyretro-pending",".pyretro-history",".pyretro-cloud",".pyretro-conflicts")
    const val PART=".pyretro-part"

    fun sha256(data:ByteArray):String=MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { "%02x".format(it) }

    /** Caminho relativo aceito, principalmente os que vêm de um manifesto remoto (nunca confiáveis). */
    fun safeRelative(rel:String?):Boolean {
        if(rel.isNullOrEmpty() || rel.startsWith("/") || '\\' in rel || '\u0000' in rel)return false
        return rel.split('/').none { it.isEmpty() || it=="." || it==".." || it in skipDirs || it.endsWith(PART) }
    }

    /** 'none' | 'same' | 'push' | 'pull' | 'conflict'. Mesma tabela do notebook (`decide` em core/cloud_saves.py). */
    fun decide(local:String?,baseline:String?,heads:Set<String>):String {
        if(local==null)return if(heads.isEmpty())"none" else if(heads.size==1)"pull" else "conflict"
        if(heads.isEmpty())return "push"
        if(heads==setOf(local))return "same"
        if(local==baseline)return if(heads.size==1)"pull" else "conflict"
        if(baseline!=null && heads==setOf(baseline))return "push"
        return "conflict"
    }
}

/**
 * Saves na nuvem por manifestos por dispositivo (protocolo de docs/nuvem.md, igual ao do notebook):
 *   <grupo>/blobs/<sha256>              conteúdo imutável
 *   <grupo>/devices/<dispositivo>.json  manifesto que SÓ este dispositivo escreve
 * `prefix` liga a pasta local do aparelho ao caminho comum da nuvem (ex.: pasta de saves do RetroArch
 * = "saves/", PPSSPP = "PPSSPP/SAVEDATA/"), para o notebook e o celular enxergarem os mesmos arquivos.
 * `baseline` é a última sincronização de cada arquivo; o chamador a persiste depois de `apply`.
 */
class CloudSavesEngine(private val storage:CloudStorage,private val device:String,private val local:LocalFiles,
                       val baseline:MutableMap<String,String> = mutableMapOf(),private val group:String="saves",
                       private val prefix:String="",private val now:()->Long={ System.currentTimeMillis()/1000 }) {
    init { require(device.isNotEmpty() && '/' !in device && !device.startsWith(".")) { "nome de dispositivo inválido" } }

    private fun manifestPath(who:String)="$group/devices/$who.json"
    fun manifests():Map<String,JSONObject> {
        val out=linkedMapOf<String,JSONObject>()
        for(item in storage.list("$group/devices")) {
            val name=item.path.substringAfterLast('/')
            if(!name.endsWith(".json"))continue
            val data=runCatching { JSONObject(String(storage.get(item.path),Charsets.UTF_8)) }.getOrNull() ?: continue
            if(data.optJSONObject("files")!=null)out[name.removeSuffix(".json")]=data
        }
        return out
    }

    /** {caminho local: {sha: [dispositivos]}}: só as cabeças. Uma entrada só substitui outra MAIS ANTIGA:
     *  duas que citam uma à outra não podem se anular (mesma regra do notebook). */
    fun heads(manifests:Map<String,JSONObject>):Map<String,Map<String,List<String>>> {
        data class Row(val device:String,val sha:String,val base:List<String>,val at:Double)
        val rows=linkedMapOf<String,MutableList<Row>>();val written=hashMapOf<Pair<String,String>,Double>()
        for((device,manifest) in manifests) {
            val files=manifest.getJSONObject("files")
            for(key in files.keys()) {
                if(!key.startsWith(prefix))continue
                val rel=key.removePrefix(prefix);val entry=files.optJSONObject(key) ?: continue
                val sha=entry.optString("sha256");val at=entry.optDouble("at",0.0).let { if(it.isNaN())0.0 else it }
                if(!CloudRules.safeRelative(rel) || sha.length!=64)continue
                val base=mutableListOf<String>();entry.optJSONArray("base")?.let { arr -> for(i in 0 until arr.length())arr.optString(i).takeIf { it.isNotEmpty() }?.let(base::add) }
                rows.getOrPut(rel) { mutableListOf() }.add(Row(device,sha,base,at))
                written[rel to sha]=maxOf(written[rel to sha] ?: 0.0,at)
            }
        }
        val superseded=hashSetOf<Pair<String,String>>()
        for((rel,list) in rows)for(r in list)for(b in r.base)if((written[rel to b] ?: 0.0)<=r.at)superseded.add(rel to b)
        val out=linkedMapOf<String,Map<String,List<String>>>()
        for((rel,list) in rows) {
            val heads=linkedMapOf<String,MutableList<String>>()
            for(r in list)if((rel to r.sha) !in superseded)heads.getOrPut(r.sha) { mutableListOf() }.add(r.device)
            if(heads.isNotEmpty())out[rel]=heads
        }
        return out
    }

    fun plan():List<CloudItem> {
        val files=local.hashes();val heads=heads(manifests());val items=mutableListOf<CloudItem>()
        for(rel in (files.keys+heads.keys).toSortedSet()) {
            val h=heads[rel].orEmpty();val action=CloudRules.decide(files[rel],baseline[rel],h.keys)
            if(action=="none" || (action=="same" && baseline[rel]==files[rel]))continue
            items.add(CloudItem(rel,action,files[rel],baseline[rel],h.mapValues { it.value.sorted() }))
        }
        return items
    }

    fun apply(items:List<CloudItem> = plan()):List<CloudResult> {
        val own=manifests()[device] ?: JSONObject().put("version",1).put("device",device).put("generation",0).put("files",JSONObject())
        val results=mutableListOf<CloudResult>();var wrote=false
        for(item in items) {
            try {
                require(CloudRules.safeRelative(item.path)) { "caminho de save inválido: ${item.path}" }
                when(item.action) {
                    "push" -> { push(item,own);wrote=true }
                    "pull" -> pull(item.path,item.heads.keys.first())
                    "same" -> baseline[item.path]=item.local!!
                }
                results.add(CloudResult(item.path,item.action,item.action!="conflict",conflict=item.heads.takeIf { item.action=="conflict" }))
            } catch(e:Exception) { results.add(CloudResult(item.path,item.action,false,e.message ?: e.javaClass.simpleName)) }
        }
        if(wrote) {
            own.put("generation",own.optInt("generation",0)+1).put("updated",now())
            storage.put(manifestPath(device),own.toString().toByteArray(Charsets.UTF_8),overwrite=true)
        }
        return results
    }

    private fun push(item:CloudItem,own:JSONObject) {
        val data=local.read(item.path);val sha=CloudRules.sha256(data)
        if(sha!=item.local)error("${item.path}: o arquivo mudou durante a sincronização; tente de novo")
        try { storage.put("$group/blobs/$sha",data) } catch(_:CloudExists) {}
        val base=JSONArray();item.heads.keys.sorted().forEach(base::put)
        own.getJSONObject("files").put(prefix+item.path,JSONObject().put("sha256",sha).put("size",data.size).put("base",base).put("at",now()))
        baseline[item.path]=sha
    }

    private fun pull(rel:String,sha:String) {
        val data=storage.get("$group/blobs/$sha")
        if(CloudRules.sha256(data)!=sha)error("$rel: o conteúdo baixado não confere com o hash; nada foi alterado")
        local.write(rel,data);baseline[rel]=sha
    }

    /** `choice` = "local": esta versão passa a substituir todas as cabeças. "remote": baixa a cabeça `sha`. Nada é apagado. */
    fun resolve(rel:String,choice:String,sha:String?=null):CloudResult {
        require(CloudRules.safeRelative(rel)) { "caminho de save inválido: $rel" }
        val heads=heads(manifests())[rel].orEmpty();val file=local.hashes()[rel]
        return when(choice) {
            "local" -> { requireNotNull(file) { "não há versão local para manter" };apply(listOf(CloudItem(rel,"push",file,null,heads.mapValues { it.value }))).first() }
            "remote" -> {
                val pick=sha ?: heads.keys.singleOrNull(); require(pick!=null && pick in heads) { "escolha uma das versões da nuvem" }
                apply(listOf(CloudItem(rel,"pull",file,null,mapOf(pick to heads.getValue(pick))))).first()
            }
            else -> throw IllegalArgumentException("escolha desconhecida: $choice")
        }
    }
}
