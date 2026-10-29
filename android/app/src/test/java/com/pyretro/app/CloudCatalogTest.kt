package com.pyretro.app
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class CloudCatalogTest {
    private fun row(id:String,name:String)=JSONObject().put("id",id).put("nome",name).put("plataforma","Super Nintendo").put("fontes",JSONArray().put("rom:SFC"))
    private fun catalog(rows:List<JSONObject>,files:List<DriveRef>)=CloudCatalog.games(JSONObject().put("games",JSONArray(rows)),emptyList(),mapOf("SFC" to files)) { _,name -> name.endsWith(".sfc") }
    @Test fun directIndexAddsUnknownGamesAndPreservesEditions() {
        val games=catalog(listOf(row("a","Game")),listOf(DriveRef("one","Game (USA).sfc",100,""),DriveRef("two","Game (Special Edition).sfc",100,"")))
        assertEquals(2,games.size);assertTrue(games.single { it.id=="a" }.drive)
        assertEquals("Game (Special Edition)",games.single { it.id.isEmpty() }.name)
    }
    @Test fun duplicateNamesAndRegionsNeverGuessOwnership() {
        val refs=listOf(DriveRef("one","Game (USA).sfc",100,""))
        assertFalse(catalog(listOf(row("a","Game"),row("b","Game")),refs).first { it.id=="a" }.drive)
        assertFalse(catalog(listOf(row("a","Game")),refs+DriveRef("two","Game (Europe).sfc",100,"")).first { it.id=="a" }.drive)
    }
    @Test fun arcadeDatNamesLinkHumanTitleWithoutNotebookCache() {
        val row=row("kof","The King of Fighters '97").put("fontes",JSONArray().put("rom:ARCADE"))
        val games=CloudCatalog.games(JSONObject().put("games",JSONArray().put(row)),emptyList(),mapOf("ARCADE" to listOf(DriveRef("rom","kof97.zip",100,""))),JSONObject().put("kof97","The King of Fighters '97")) { _,_ -> true }
        assertEquals(1,games.size);assertEquals("kof",games.single().id);assertTrue(games.single().drive);assertEquals("kof97.zip",games.single().romName)
    }
}
