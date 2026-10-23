package com.pyretro.app

import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Um desejado como o app mostra: a loja vira a "plataforma". */
data class WishItem(val id:String,val source:String,val name:String,val cover:String,val genre:String)
/** Para onde vai uma capa trocada: cadastro da Biblioteca ou arquivo da ROM no PC. */
data class CoverTarget(val kind:String,val id:String="",val code:String="",val label:String="")

/** Só a requisição mais recente vale: respostas de pedidos anteriores são descartadas. */
class LatestRequest {
    @Volatile private var current=0
    fun start():Int=synchronized(this) { ++current }
    fun isCurrent(id:Int)=id==current
}

/** Regras sem Android: leitura das respostas do notebook e escolhas de exibição. */
object ExtrasRules {
    val STORES=linkedMapOf("steam" to "Steam","psn" to "PlayStation","xbox" to "Xbox")
    /** As três lojas numa lista só, por nome (mesma ordem do modo TV). */
    fun sorted(items:List<WishItem>)=items.sortedBy { it.name.lowercase() }
    fun wishKey(item:WishItem)="wish:${item.source}:${item.id}"
    /** Horas em "X dias e Y h (Z h)", igual ao modo TV. */
    fun hours(value:Double):String { val total=Math.round(value);val days=total/24
        return if(days>0)"$days ${if(days==1L)"dia" else "dias"} e ${total%24} h ($total h)" else "$total h" }
    /** Capa de ROM tem a forma /images/<código>/<label>.png?v=…; o resto é capa da Biblioteca. */
    fun coverTarget(id:String,cover:String):CoverTarget? {
        val match=Regex("^/images/([^/]+)/([^?]+)\\.(png|jpg)(\\?.*)?$",RegexOption.IGNORE_CASE).find(cover)
        fun decode(value:String)=java.net.URLDecoder.decode(value.replace("+","%2B"),"UTF-8")
        if(match!=null)return CoverTarget("rom",code=decode(match.groupValues[1]),label=decode(match.groupValues[2]))
        return if(id.isNotBlank())CoverTarget("biblioteca",id=id) else null
    }
    /** Só o que mudou vai para o notebook (vazio vira null, que limpa o campo). */
    fun changes(before:Map<String,String>,after:Map<String,String>):Map<String,String?> =
        after.filter { (field,value) -> value.trim()!=before[field].orEmpty().trim() }.mapValues { it.value.trim().ifEmpty { null } }
}

/** Funções que dependem do notebook online: Desejados, Estatísticas, editar e capa.
 *  Desejados e Estatísticas ficam em cache para abrir offline com a data da última leitura. */
class NotebookExtras(private val store:LibraryStore,private val dir:File) {
    private fun cache(name:String)=File(dir,name)
    private fun save(name:String,raw:String) { val tmp=File(dir,"$name.tmp");tmp.writeText(raw);tmp.renameTo(cache(name)) }
    fun wishlist(fresh:Boolean):List<WishItem> {
        if(fresh) { val raw=store.request("/api/wishlist");save("wishlist.json",raw);store.prefs.edit().putLong("wishlist-at",System.currentTimeMillis()).apply() }
        return runCatching { val data=JSONObject(cache("wishlist.json").readText())
            ExtrasRules.sorted(ExtrasRules.STORES.keys.flatMap { source -> val list=data.optJSONArray(source) ?: JSONArray()
                (0 until list.length()).map { list.getJSONObject(it) }.map { g -> fun text(k:String)=if(g.isNull(k))"" else g.optString(k)
                    WishItem(g.getString("id"),source,g.getString("nome"),text("capa_url"),text("genero")) } }) }.getOrDefault(emptyList())
    }
    fun stats(fresh:Boolean):JSONObject? {
        if(fresh) { val raw=store.request("/api/estatisticas");save("stats.json",raw);store.prefs.edit().putLong("stats-at",System.currentTimeMillis()).apply() }
        return runCatching { JSONObject(cache("stats.json").readText()) }.getOrNull()
    }
    fun leaveWishlist(item:WishItem,bought:Boolean) {
        store.request(if(bought)"/api/wishlist/comprado" else "/api/wishlist/remove",JSONObject().put("source",item.source).put("id",item.id))
        wishlist(true)
    }
    /** Registro completo de um jogo da Biblioteca (gênero, comentário, tempo, data). */
    fun record(id:String):JSONObject? {
        val all=JSONArray(store.request("/api/library"))
        return (0 until all.length()).map { all.getJSONObject(it) }.firstOrNull { it.optString("id")==id }
    }
    fun genres():List<String> = runCatching { val list=JSONObject(store.request("/api/sortear/systems")).getJSONArray("generos");(0 until list.length()).map { list.getString(it) } }.getOrDefault(emptyList())
    fun edit(id:String,changes:Map<String,String?>) {
        val campos=JSONObject();for((field,value) in changes)campos.put(field,value ?: JSONObject.NULL)
        store.request("/api/library/edit",JSONObject().put("id",id).put("campos",campos))
    }
    fun searchCovers(query:String):List<Pair<String,String>> {
        // O SteamGridDB oscila (a busca chegou a 60 s em 23/10): prazo maior só aqui.
        val raw=store.request("/api/cover/search_sgdb?q=${Uri.encode(query)}",readTimeout=150_000)
        val list=runCatching { JSONArray(raw) }.getOrElse { throw IllegalArgumentException(JSONObject(raw).optString("error","Busca falhou.")) }
        return (0 until list.length()).map { list.getJSONObject(it) }.map { it.getString("url") to it.optString("nome") }
    }
    /** Organizar do notebook: pasta de organizar + Downloads, ROMs de dentro de compactados. */
    fun organizePending():List<JSONObject> { val items=JSONObject(store.request("/api/organize/pending")).getJSONArray("items");return (0 until items.length()).map(items::getJSONObject) }
    /** Extrair um PS1 de centenas de MB e buscar capa/gênero leva minutos: prazo longo só aqui. */
    fun organizeMove(id:String,code:String):JSONObject = JSONObject(store.request("/api/organize/move",JSONObject().put("id",id).put("code",code),readTimeout=900_000))
    fun organizeDiscard(id:String) { store.request("/api/organize/discard",JSONObject().put("id",id)) }
    /** ROM que só existe no celular vira cadastro da Biblioteca (`docs/mobile-library.md`). */
    fun addRom(name:String,code:String):JSONObject = JSONObject(store.request("/api/library/add-rom",JSONObject().put("nome",name).put("code",code)))
    /** ID do título dos saves PSP/3DS (`docs/mobile-save-ids.md`); guardado para uso offline. */
    fun saveIds(id:String):JSONObject {
        val raw=store.request("/api/mobile/saves/game?id=${Uri.encode(id)}");store.prefs.edit().putString("save-ids:$id",raw).apply();return JSONObject(raw)
    }
    fun cachedSaveIds(id:String)=store.prefs.getString("save-ids:$id",null)?.let { runCatching { JSONObject(it) }.getOrNull() }
    fun applyCover(target:CoverTarget,url:String) {
        val body=JSONObject().put("kind",target.kind).put("url",url)
        if(target.kind=="rom")body.put("code",target.code).put("label",target.label) else body.put("id",target.id)
        store.request("/api/cover/apply_url",body)
    }
}

/** Miniatura de uma capa externa (SteamGridDB), reduzida para a grade da busca. */
fun NotebookExtras.thumbnail(url:String):android.graphics.Bitmap? {
    require(url.startsWith("https://")) { "endereço de imagem inválido" }
    val connection=java.net.URL(url).openConnection() as java.net.HttpURLConnection
    connection.connectTimeout=10000;connection.readTimeout=20000
    try {
        val bytes=connection.inputStream.use { input -> val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(65536)
            while(true) { val n=input.read(buffer);if(n<0)break;require(out.size()+n<=15*1024*1024) { "imagem grande demais" };out.write(buffer,0,n) };out.toByteArray() }
        return android.graphics.BitmapFactory.decodeByteArray(bytes,0,bytes.size,android.graphics.BitmapFactory.Options().apply { inSampleSize=4 })
    } finally { connection.disconnect() }
}
