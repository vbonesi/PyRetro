package com.pyretro.app
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
class LibraryViewTest {
    private fun data()=JSONObject("""{"games":[{"id":"a","nome":"A","plataforma":"PSN","fontes":["wishlist:psn"],"tempo":"10:30:00","nota":9,"iniciado":true,"_play_sessions":{"phone:a":1800}},{"id":"b","nome":"B","plataforma":"Steam","fontes":["steam","wishlist:steam"],"oculto":true}]}""")
    @Test fun localStatsIncludeUniqueSessionsAndWishlistKeepsOwnedGames() {
        val data=data();val stats=LibraryView.stats(data)
        assertEquals(1,stats.getInt("total"));assertEquals(11.0,stats.getDouble("tempo_total_horas"),0.001)
        val wishes=LibraryView.wishlist(data);assertEquals(2,wishes.size)
        val bought=LibraryView.leaveWishlist(data,wishes.single { it.id=="a" },true)
        assertEquals("PlayStation 4",JournalRules.games(bought).getValue("a").getString("plataforma"))
        val removed=LibraryView.leaveWishlist(data,wishes.single { it.id=="b" },false)
        assertTrue("b" in JournalRules.games(removed));assertEquals(1,LibraryView.wishlist(removed).size)
        assertEquals(2,LibraryView.wishlist(data).size)
    }
}
