package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import java.util.UUID

object QueueSpaceSmoke {
    fun run(store:LibraryStore,sourceFolder:Uri) {
        val resolver=store.context.contentResolver
        val queue=DownloadQueue.get(store)
        fun waitForStop() { for(i in 0 until 1000) { if(!queue.running)return;Thread.sleep(20) };error("Fila não concluiu a pausa/cópia.") }
        try {
            val payload=ByteArray(800000) { (it%239).toByte() }
            fun game(label:String):Game {
                val name="Queue-$label-"+UUID.randomUUID()
                val source=DocumentsContract.createDocument(resolver,sourceFolder,"application/octet-stream","$name.nes")!!
                resolver.openOutputStream(source,"w")!!.use { it.write(payload) }
                val game=Game("",name,name,"NES","FC","$name.nes")
                store.prefs.edit().putString("cloud:${game.key}",source.toString()).commit();return game
            }
            val first=game("A");val second=game("B")
            SpaceStore(store).setPinned(first,true)
            queue.enqueue(first);queue.enqueue(second)
            val recoveryName=store.preferenceName+"-recovery"
            try {
                val recover=LibraryStore(store.context,recoveryName)
                val data=org.json.JSONArray(store.prefs.getString("download-queue","[]"))
                data.getJSONObject(0).put("state","RUNNING")
                recover.prefs.edit().putString("download-queue",data.toString()).commit()
                val recovered=DownloadQueue.get(recover)
                check(!recovered.running && recovered.snapshot().first().state==DownloadState.PAUSED)
            } finally { store.context.deleteSharedPreferences(recoveryName) }
            var refused=false;try { queue.enqueue(first) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            queue.move(second.key,-1);check(queue.snapshot().first().game.key==second.key)
            queue.start { if(it.bytes>0)queue.pause() };waitForStop()
            check(queue.snapshot().first().state==DownloadState.PAUSED)
            check(queue.snapshot().last().state==DownloadState.WAITING)
            val checkpoint=DownloadStore(store).jobs().first { it.getString("key")==second.key }
            check(checkpoint.getLong("bytes") in 1 until payload.size.toLong())
            queue.remove(second.key);check(DownloadStore(store).jobs().any { it.getString("key")==second.key })
            queue.enqueue(second);queue.start();waitForStop()
            check(queue.snapshot().all { it.state==DownloadState.DONE })
            check(DownloadStore(store).jobs().isEmpty())
            val rows=SpaceStore(store).scan(listOf(first,second));check(rows.errors.isEmpty())
            check(rows.roms.size==2 && rows.roms.all { it.stamp.size==payload.size.toLong() })
            val pinned=rows.roms.first { it.game.key==first.key }
            check(pinned.pinned)
            val alias=pinned.game.copy(key="another-catalog-key")
            check(SpaceStore(store).pinned(alias))
            refused=false;try { store.removeLocal(alias,pinned.stamp) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            SpaceStore(store).setPinned(alias,false);check(!SpaceStore(store).pinned(pinned.game))
            resolver.openOutputStream(pinned.game.localUri!!,"w")!!.use { it.write(byteArrayOf(1,2,3)) }
            refused=false;try { store.removeLocal(pinned.game,pinned.stamp) } catch(_:IllegalArgumentException) { refused=true };check(refused)
            val removable=rows.roms.first { it.game.key==second.key }
            store.removeLocal(removable.game,removable.stamp)
            check(store.files("FC",true).size==1)
        } finally { queue.pause();waitForStop() }
    }
}
