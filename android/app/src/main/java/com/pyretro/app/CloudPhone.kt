package com.pyretro.app

import android.content.ContentResolver
import org.json.JSONObject
import java.io.File

/** Pasta local de um grupo de saves do aparelho (SAF), vista pelo motor de nuvem. */
class FileSyncLocalFiles(private val sync:FileSync,private val group:String,private val resolver:ContentResolver,private val cache:File):LocalFiles {
    override fun hashes():Map<String,String> = sync.local(group).mapValues { it.value.sha256 }
    override fun read(rel:String):ByteArray {
        val file=sync.local(group)[rel] ?: error("Arquivo local sumiu: $rel")
        return resolver.openInputStream(file.uri)?.use { it.readBytes() } ?: error("Não foi possível ler $rel")
    }
    /** Usa o mesmo caminho seguro do sync com o notebook: confere o hash e guarda a versão anterior no histórico. */
    override fun write(rel:String,data:ByteArray) {
        val temporary=File.createTempFile("cloud-get-",".tmp",cache)
        try { temporary.writeBytes(data);sync.install(group,rel,temporary,CloudRules.sha256(data),sync.local(group)[rel]?.sha256) } finally { temporary.delete() }
    }
}

/**
 * Saves na nuvem pelo celular: cada grupo de pastas do aparelho vira um prefixo do caminho comum da nuvem,
 * o mesmo que o notebook enxerga em `~/Games/PyRetro/Saves` (ver docs/nuvem.md). Os runtimes ficam de fora.
 */
class CloudPhone(private val store:LibraryStore,private val sync:FileSync,private val storage:CloudStorage,private val device:String="celular") {
    companion object {
        val prefixes=linkedMapOf("retro-saves" to "saves/","retro-states" to "states/","psp-saves" to "PPSSPP/SAVEDATA/","psp-states" to "PPSSPP/PPSSPP_STATE/","3ds-saves" to "Lime3DS/sdmc/")
        fun baselineOf(text:String?):MutableMap<String,String> {
            val out=linkedMapOf<String,String>();val json=runCatching { JSONObject(text ?: "{}") }.getOrDefault(JSONObject())
            for(key in json.keys())out[key]=json.getString(key);return out
        }
    }
    private val prefs=store.context.getSharedPreferences("cloud-sync",0)

    fun groups():List<String> = prefixes.keys.filter { runCatching { sync.tree(it)!=null }.getOrDefault(false) }
    private fun engine(group:String)=CloudSavesEngine(storage,device,FileSyncLocalFiles(sync,group,store.context.contentResolver,store.context.cacheDir),
        baselineOf(prefs.getString("baseline:$group",null)),"saves",prefixes.getValue(group))

    /** Prévia por grupo; um grupo ilegível vira erro de texto, não derruba os outros. */
    fun analyze(filter:((String,String)->Boolean)?=null):Map<String,Result<List<CloudItem>>> = groups().associateWith { group -> runCatching { engine(group).plan().filter { filter==null || filter(group,it.path) } } }

    fun apply(only:Set<String>?=null,filter:((String,String)->Boolean)?=null):Map<String,Result<List<CloudResult>>> = groups().filter { only==null || it in only }.associateWith { group ->
        runCatching {
            val engine=engine(group);val results=engine.apply(engine.plan().filter { filter==null || filter(group,it.path) })
            val edit=prefs.edit().putString("baseline:$group",JSONObject(engine.baseline as Map<*,*>).toString())
            if(results.all { it.ok && it.conflict==null })edit.putLong("at",System.currentTimeMillis())
            edit.apply()
            results
        }
    }

    fun resolve(group:String,path:String,choice:String,sha:String?=null):CloudResult {
        val engine=engine(group);val result=engine.resolve(path,choice,sha)
        prefs.edit().putString("baseline:$group",JSONObject(engine.baseline as Map<*,*>).toString()).apply();return result
    }
    fun lastAt():Long=prefs.getLong("at",0)
}
