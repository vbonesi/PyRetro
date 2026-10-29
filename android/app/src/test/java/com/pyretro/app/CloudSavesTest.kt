package com.pyretro.app

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MemoryLocal:LocalFiles {
    val files=linkedMapOf<String,ByteArray>();val history=mutableListOf<Pair<String,ByteArray>>()
    override fun hashes()=files.mapValues { CloudRules.sha256(it.value) }
    override fun read(rel:String)=files.getValue(rel)
    override fun write(rel:String,data:ByteArray) { files[rel]?.let { history.add(rel to it) };files[rel]=data }
    override fun forget(rel:String,expected:String?) { require(hashes()[rel]==expected);files.remove(rel)?.let { history.add(rel to it) } }
    fun put(rel:String,text:String) { files[rel]=text.toByteArray() }
}

class CloudSavesTest {
    private val store=MemoryCloudStorage()
    private val pc=MemoryLocal();private val phone=MemoryLocal()
    private var clock=1000L
    private val a=CloudSavesEngine(store,"pc",pc,now={ clock++ })
    private val b=CloudSavesEngine(store,"celular",phone,now={ clock++ })
    private fun actions(e:CloudSavesEngine)=e.plan().associate { it.path to it.action }

    @Test fun decideTableMatchesTheNotebook() {
        val cases=listOf(
            listOf(null,null,setOf<String>(),"none"),listOf("a",null,setOf<String>(),"push"),listOf("a","a",setOf("a"),"same"),
            listOf(null,"a",setOf("a"),"pull"),listOf(null,null,setOf("a","b"),"conflict"),listOf("a","a",setOf("b"),"pull"),
            listOf("a","a",setOf("b","c"),"conflict"),listOf("b","a",setOf("a"),"push"),listOf("b","a",setOf("c"),"conflict"),
            listOf("b",null,setOf("c"),"conflict"),listOf("b","a",setOf("b"),"same"),listOf("b","a",setOf("b","c"),"conflict"))
        for(c in cases)assertEquals(c.toString(),c[3],CloudRules.decide(c[0] as String?,c[1] as String?,c[2] as Set<String>))
    }

    @Test fun firstPushThenOtherDevicePullsAndBothAreInSync() {
        pc.put("SFC/Jogo.srm","v1")
        assertEquals(mapOf("SFC/Jogo.srm" to "push"),actions(a));assertTrue(a.apply().all { it.ok })
        assertEquals(mapOf("SFC/Jogo.srm" to "pull"),actions(b));b.apply()
        assertEquals("v1",String(phone.files.getValue("SFC/Jogo.srm")))
        assertTrue(actions(a).isEmpty());assertTrue(actions(b).isEmpty())
    }

    @Test fun fastForwardKeepsReplacedFileInHistory() {
        pc.put("Jogo.srm","v1");a.apply();b.apply()
        phone.put("Jogo.srm","v2");assertEquals(mapOf("Jogo.srm" to "push"),actions(b));b.apply()
        assertEquals(mapOf("Jogo.srm" to "pull"),actions(a));a.apply()
        assertEquals("v2",String(pc.files.getValue("Jogo.srm")));assertEquals(listOf("v1"),pc.history.map { String(it.second) })
    }

    @Test fun divergenceIsAConflictAndResolveWorksBothWays() {
        pc.put("Jogo.srm","v1");a.apply();b.apply()
        pc.put("Jogo.srm","do-pc");phone.put("Jogo.srm","do-celular");b.apply()
        assertEquals(mapOf("Jogo.srm" to "conflict"),actions(a))
        assertFalse(a.apply().first().ok.not().not() && a.plan().first().action!="conflict")
        assertEquals("do-pc",String(pc.files.getValue("Jogo.srm")))
        assertTrue(a.resolve("Jogo.srm","local").ok);assertEquals(mapOf("Jogo.srm" to "pull"),actions(b));b.apply()
        assertEquals("do-pc",String(phone.files.getValue("Jogo.srm")))
        pc.put("Jogo.srm","a2");phone.put("Jogo.srm","b2");b.apply()
        assertTrue(a.resolve("Jogo.srm","remote").ok);assertEquals("b2",String(pc.files.getValue("Jogo.srm")))
        assertTrue(pc.history.any { String(it.second)=="a2" })
    }

    @Test fun rerunIsIdempotentAndDeletedFileIsRestoredNotPropagated() {
        pc.put("Jogo.srm","v1");a.apply();val before=store.files.keys.toSet()
        a.apply();assertEquals(before,store.files.keys.toSet())
        pc.files.remove("Jogo.srm");assertEquals(mapOf("Jogo.srm" to "pull"),actions(a));a.apply()
        assertEquals("v1",String(pc.files.getValue("Jogo.srm")))
    }

    @Test fun hostileManifestPathsAndTamperedBlobsAreNotTrusted() {
        pc.put("Jogo.srm","v1");a.apply()
        val manifest=JSONObject(String(store.files.getValue("saves/devices/pc.json")))
        val entry=manifest.getJSONObject("files").getJSONObject("Jogo.srm")
        manifest.getJSONObject("files").put("../../fora",entry).put(".pyretro-history/x",entry)
        store.files["saves/devices/pc.json"]=manifest.toString().toByteArray()
        assertEquals(mapOf("Jogo.srm" to "pull"),actions(b))
        store.files["saves/blobs/${entry.getString("sha256")}"]="adulterado".toByteArray()
        val r=b.apply().first();assertFalse(r.ok);assertTrue(r.error!!.contains("não confere"));assertTrue(phone.files.isEmpty())
    }

    @Test fun prefixMapsALocalFolderToTheCommonCloudPath() {
        // o notebook enxerga "saves/SFC/Jogo.srm"; o celular tem a pasta de saves do RetroArch com "SFC/Jogo.srm"
        val notebook=MemoryLocal();notebook.put("saves/SFC/Jogo.srm","v1")
        CloudSavesEngine(store,"pc",notebook,now={ clock++ }).apply()
        val retro=CloudSavesEngine(store,"celular",phone,prefix="saves/",now={ clock++ })
        assertEquals(mapOf("SFC/Jogo.srm" to "pull"),retro.plan().associate { it.path to it.action });retro.apply()
        phone.put("SFC/Outro.srm","novo");retro.apply()
        assertTrue(JSONObject(String(store.files.getValue("saves/devices/celular.json"))).getJSONObject("files").has("saves/SFC/Outro.srm"))
    }

    @Test fun manifestFromTheNotebookFormatIsUnderstood() {
        // formato escrito por core/cloud_saves.py (sha256, size, base, at + cabeçalho)
        val sha="a".repeat(64);val blob="conteudo".toByteArray();val real=CloudRules.sha256(blob)
        store.put("saves/blobs/$real",blob)
        store.put("saves/devices/pc.json","""{"version":1,"device":"pc","generation":3,"updated":5,"files":{"X/Y.srm":{"sha256":"$real","size":8,"base":[],"at":4},"ruim":{"sha256":"$sha"}}}""".toByteArray())
        val engine=CloudSavesEngine(store,"celular",phone)
        assertEquals(mapOf("X/Y.srm" to "pull"),engine.plan().associate { it.path to it.action }.filterKeys { it=="X/Y.srm" })
    }

    @Test fun twoEntriesThatCiteEachOtherKeepTheNewerOneAsTheOnlyHead() {
        val a="a".repeat(64);val b="b".repeat(64)
        store.put("saves/devices/pc.json","{\"files\":{\"Jogo.srm\":{\"sha256\":\"$b\",\"base\":[\"$a\"],\"at\":100}}}".toByteArray())
        store.put("saves/devices/celular.json","{\"files\":{\"Jogo.srm\":{\"sha256\":\"$a\",\"base\":[\"$b\"],\"at\":200}}}".toByteArray())
        val engine=CloudSavesEngine(store,"x",phone)
        assertEquals(mapOf("Jogo.srm" to mapOf(a to listOf("celular"))),engine.heads(engine.manifests()))
    }

    @Test fun storageContractAndPathValidation() {
        store.put("a/b","1".toByteArray());assertThrows(CloudExists::class.java) { store.put("a/b","2".toByteArray()) }
        store.put("a/b","3".toByteArray(),overwrite=true);assertEquals("3",String(store.get("a/b")))
        assertThrows(CloudNotFound::class.java) { store.get("nao/existe") }
        for(bad in listOf("../x","/abs","a//b","a/./b",""))assertThrows(bad,IllegalArgumentException::class.java) { store.put(bad,ByteArray(0)) }
        store.trash("a/b");assertFalse(store.exists("a/b"));assertEquals(listOf("a/b"),store.trashed)
    }
}
