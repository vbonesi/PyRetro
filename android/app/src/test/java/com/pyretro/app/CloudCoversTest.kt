package com.pyretro.app
import org.junit.Assert.*
import org.junit.Test
class CloudCoversTest {
    @Test fun contentAddressingHistoryAndCorruption() {
        val store=MemoryCloudStorage();CloudCovers.publish(store,"água","first".toByteArray());CloudCovers.publish(store,"água","first".toByteArray());assertEquals(2,store.files.size)
        CloudCovers.publish(store,"água","second".toByteArray());assertEquals("second",String(CloudCovers.get(store,"água")));assertEquals(3,store.files.size)
        store.put("capas/blobs/"+CloudRules.sha256("second".toByteArray()),"wrong".toByteArray(),true)
        assertThrows(IllegalArgumentException::class.java) { CloudCovers.get(store,"água") }
        assertEquals("capas/items/"+CloudRules.sha256("água".toByteArray())+".json",CloudCovers.item("água"))
    }
}
