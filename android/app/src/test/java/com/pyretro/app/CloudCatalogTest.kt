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
        val games=CloudCatalog.games(JSONObject().put("games",JSONArray().put(row)),emptyList(),mapOf("ARCADE" to listOf(DriveRef("rom","kof97.zip",100,""))),JSONObject().put("kof97","The King of Fighters '97 (NGM-2320)")) { _,_ -> true }
        assertEquals(1,games.size);assertEquals("kof",games.single().id);assertTrue(games.single().drive);assertEquals("kof97.zip",games.single().romName)
    }
    @Test fun titlesWithDotsAreNotCutLikeExtensions() {
        val files=listOf(DriveRef("1","Super Mario Bros..sfc",100,""),DriveRef("2","Super Mario Bros. 2.sfc",100,""),DriveRef("3","Super Mario Bros. 3.sfc",100,""))
        val games=catalog(listOf(row("a","Super Mario Bros."),row("b","Super Mario Bros. 2"),row("c","Super Mario Bros. 3")),files)
        assertEquals(3,games.size);assertTrue(games.all { it.drive && it.id.isNotEmpty() })
        assertEquals("Super Mario Bros. 2.sfc",games.single { it.id=="b" }.romName)
    }
    @Test fun arcadeAlternativeTitlesLinkTheRecord() {
        val row=row("ss","Samurai Shodown").put("fontes",JSONArray().put("rom:ARCADE"))
        val games=CloudCatalog.games(JSONObject().put("games",JSONArray().put(row)),emptyList(),mapOf("ARCADE" to listOf(DriveRef("rom","samsho.zip",100,""))),JSONObject().put("samsho","Samurai Shodown / Samurai Spirits (NGM-045)")) { _,_ -> true }
        assertEquals(1,games.size);assertEquals("ss",games.single().id);assertTrue(games.single().drive)
    }
    @Test fun extraDiscsShowTheFirstDiscRecord() {
        val row=row("ff","Final Fantasy VII (Disk 1)").put("fontes",JSONArray().put("rom:PS"))
        val files=listOf(DriveRef("1","Final Fantasy VII (Disk 1).chd",100,""),DriveRef("2","Final Fantasy VII (Disk 2).chd",100,""),DriveRef("3","Other (Disk 2).chd",100,""))
        val games=CloudCatalog.games(JSONObject().put("games",JSONArray().put(row)),emptyList(),mapOf("PS" to files)) { _,_ -> true }
        assertEquals(3,games.size)
        val disc2=games.single { it.romName=="Final Fantasy VII (Disk 2).chd" }
        assertEquals("ff",disc2.id);assertEquals("cloud-cover:ff",disc2.cover);assertEquals("Final Fantasy VII (Disk 2)",disc2.name)
        assertEquals("",games.single { it.romName=="Other (Disk 2).chd" }.id)
    }
}
