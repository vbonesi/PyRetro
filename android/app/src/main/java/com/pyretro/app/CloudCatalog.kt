package com.pyretro.app

import org.json.JSONArray
import org.json.JSONObject

object CloudCatalog {
    private val tags=Regex("\\[[^]]*]")
    private val regions=Regex("\\((?:USA|Europe|Japan|World|Rev\\s*[0-9]+|(?:En|Fr|De|Es|It|Nl|Pt)(?:,[A-Za-z]{2})*)\\)",RegexOption.IGNORE_CASE)
    private val codes=mapOf("nes" to "FC","snes" to "SFC","gb" to "GB","gbc" to "GBC","gba" to "GBA","n64" to "N64","nds" to "NDS","3ds" to "3DS","mastersystem" to "SMS","megadrive" to "MD","gamegear" to "GG","pcengine" to "PCE","pcenginecd" to "PCECD","arcade" to "ARCADE","ps1" to "PS","psp" to "PSP")
    fun code(game:JSONObject):String {
        val sources=game.optJSONArray("fontes") ?: JSONArray()
        for(i in 0 until sources.length())sources.optString(i).takeIf { it.startsWith("rom:") }?.removePrefix("rom:")?.takeIf { it in codes.values }?.let { return it }
        return codes[PlatformRules.find(game.optString("plataforma")).id].orEmpty()
    }
    private val setCode=Regex("\\s*\\([^)]*\\)")
    fun romName(value:String):String=GameLogic.normalized(GameLogic.fileLabel(value)
        .replace(tags,"").replace(regions,""))
    fun libraryFrom(games:List<Game>):JSONObject {
        val rows=games.filter { it.id.isNotBlank() }.distinctBy { it.id }.map { g -> JournalRules.copy(g.tracking)
            .put("id",g.id).put("nome",g.name).put("plataforma",g.platform).put("genero",g.genre).put("nomes_alt",JSONArray(g.aliases)) }
        return JSONObject().put("games",JSONArray(rows))
    }
    fun games(library:JSONObject,legacy:List<Game>,files:Map<String,List<DriveRef>>,arcadeNames:JSONObject=JSONObject(),accepts:(String,String)->Boolean):List<Game> {
        val old=legacy.filter { it.id.isNotBlank() }.groupBy { it.id };val result=mutableListOf<Game>()
        fun label(code:String,name:String)=if(code=="ARCADE")arcadeNames.optString(name.substringBeforeLast('.'),GameLogic.fileLabel(name)) else GameLogic.fileLabel(name)
        val indexed=files.mapValues { (code,refs) -> refs.filter { it.size>0 && accepts(code,it.name) }.flatMap { ref -> listOf(romName(ref.name),romName(label(code,ref.name)),romName(label(code,ref.name).let { if(code=="ARCADE")it.replace(setCode,"") else it })).distinct().map { it to ref } }.groupBy({ it.first },{ it.second }) }
        val rows=JournalRules.games(library);val candidates=rows.mapValues { (_,g) ->
            val aliases=g.optJSONArray("nomes_alt") ?: JSONArray();val wanted=(listOf(g.optString("nome"))+(0 until aliases.length()).map { aliases.optString(it) }).map(::romName).toSet()
            wanted.flatMap { indexed[code(g)]?.get(it).orEmpty() }.distinctBy { it.id }
        }
        val owners=candidates.values.flatten().groupingBy { it.id }.eachCount();val used=mutableSetOf<String>()
        for((id,g) in rows) {
            if(g.optBoolean("oculto"))continue
            val sources=g.optJSONArray("fontes") ?: JSONArray()
            if(sources.length()>0 && (0 until sources.length()).all { sources.optString(it).startsWith("wishlist:") })continue
            val code=code(g);val previous=old[id]?.firstOrNull { it.code==code } ?: old[id]?.firstOrNull()
            val aliases=g.optJSONArray("nomes_alt") ?: JSONArray();val names=listOf(g.optString("nome"))+(0 until aliases.length()).map { aliases.optString(it) }
            val ref=candidates[id]?.singleOrNull()?.takeIf { owners[it.id]==1 };ref?.let { used.add(it.id) };val key=previous?.key ?: "pc:$id"
            result.add(Game(id,key,g.optString("nome"),g.optString("plataforma"),code,ref?.name ?: previous?.romName ?: g.optString("nome"),
                if(id.isNotBlank())"cloud-cover:$id" else previous?.cover.orEmpty(),g.optString("genero").takeUnless { g.isNull("genero") }.orEmpty(),
                names.drop(1),JournalRules.copy(g),drive=ref!=null || previous?.drive==true))
        }
        for((code,refs) in files)for(ref in refs)if(ref.id !in used && ref.size>0 && accepts(code,ref.name)) {
            result.add(Game("", "drive:$code:${ref.id}",label(code,ref.name),PlatformRules.find(code).name,code,ref.name,drive=true))
        }
        return result.sortedBy { GameLogic.normalized(it.name) }
    }
}
