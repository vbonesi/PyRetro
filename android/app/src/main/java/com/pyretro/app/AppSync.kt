package com.pyretro.app

import android.content.Context
import android.net.ConnectivityManager
import android.os.SystemClock
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.Executor
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

/**
 * Atualização automática de abertura e retomada, compartilhada pelas duas activities (casca em Compose e tela antiga):
 * progresso, catálogo do notebook/Drive e capas para o modo offline. O limite de 15 min vale para o processo todo.
 */
object AppSync {
    const val INTERVAL_MS = 15 * 60 * 1000L
    const val STALE_MS = 6 * 60 * 60 * 1000L
    /** Instrumentação desliga (navegar não pode baixar catálogo nem enviar progresso). */
    @Volatile var enabled = true
    @Volatile private var last = 0L

    enum class Step { WORKER_AND_TRACKING, TRACKING, CATALOG, NONE }

    /** No máximo a cada 15 min (a menos que forçado): pendências em conflito continuam pendentes e não podem virar um laço. */
    fun due(now: Long, last: Long, force: Boolean, enabled: Boolean = true) = enabled && (force || last <= 0 || now - last >= INTERVAL_MS)

    fun plan(driveConnected: Boolean, pending: Int, stale: Boolean, catalogEmpty: Boolean) = when {
        driveConnected -> Step.WORKER_AND_TRACKING
        pending > 0 -> Step.TRACKING
        stale || catalogEmpty -> Step.CATALOG
        else -> Step.NONE
    }

    fun isStale(updatedAt: Long, now: Long) = now - updatedAt > STALE_MS

    @Synchronized private fun claim(now: Long, force: Boolean): Boolean {
        if (!due(now, last, force, enabled)) return false
        last = now; return true
    }

    /** Texto do estado no topo do Início. */
    fun statusLine(online: Boolean, updatedAt: Long, catalogEmpty: Boolean, format: (Long) -> String): String = when {
        online && catalogEmpty -> "Online · notebook conectado. Buscando o catálogo…"
        online -> "Online · atualizado" + if (updatedAt > 0) " ${format(updatedAt)}" else ""
        catalogEmpty -> "Offline · sem catálogo em cache"
        else -> "Offline · catálogo em cache" + if (updatedAt > 0) " de ${format(updatedAt)}" else ""
    }

    /** [onFresh] roda na thread de trabalho: quem chama leva o resultado para a thread principal. */
    fun automaticUpdate(context: Context, store: LibraryStore, drive: GoogleDrive, work: Executor, force: Boolean, catalogEmpty: Boolean,
        onFresh: (catalog: List<Game>, message: String) -> Unit) {
        if (!claim(SystemClock.elapsedRealtime(), force)) return
        val step = plan(drive.connected, store.pending(), isStale(store.prefs.getLong("updated", 0), System.currentTimeMillis()), catalogEmpty)
        if (step == Step.WORKER_AND_TRACKING) LibraryWorker.schedule(context)
        when (step) {
            Step.WORKER_AND_TRACKING, Step.TRACKING -> work.execute {
                runCatching { store.synchronize() }.onSuccess { result -> onFresh(store.cached(), "Online · catálogo atualizado. $result") }
            }
            Step.CATALOG -> work.execute {
                runCatching { store.refresh() }.onSuccess { onFresh(it, "Online · catálogo atualizado agora.") }.onFailure { store.online = false }
            }
            Step.NONE -> {}
        }
    }

    private val prefetching = AtomicBoolean(false)
    private val prefetchPool = Executors.newFixedThreadPool(4) { r -> Thread(r).apply { isDaemon = true } }

    /** Capas dos jogos do celular, favoritos e fixados ficam no cache para o modo offline; com Wi-Fi, o resto da biblioteca. */
    fun prefetchCovers(context: Context, store: LibraryStore, drive: GoogleDrive, games: List<Game>) {
        if (!store.online && !drive.connected) return
        val pinned = SpaceStore(store).pinnedChecker()
        val metered = (context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager).isActiveNetworkMetered
        val wanted = games.filter { it.id.isNotBlank() }.sortedByDescending { it.localUri != null || store.favorite(it) || pinned(it) }
            .let { if (metered) it.filter { g -> g.localUri != null || store.favorite(g) || pinned(g) }.take(300) else it }
        if (!prefetching.compareAndSet(false, true)) return
        // Quatro trabalhadores dividem a fila; cada capa já guardada passa direto, então repetir a chamada é barato.
        val queue = ConcurrentLinkedQueue(wanted); val remaining = AtomicInteger(4)
        repeat(4) {
            prefetchPool.execute {
                try { while (true) { val game = queue.poll() ?: break; if (!store.online && !drive.connected) break; runCatching { store.cover(game, publish = false) } } }
                finally { if (remaining.decrementAndGet() == 0) prefetching.set(false) }
            }
        }
    }

    @Volatile private var lastProbe = 0L
    private val probing = AtomicBoolean(false)

    /** Confere o notebook (só /api/csrf, 1×/min; offline, a cada 5 s). [onDone] roda numa thread de trabalho. */
    fun probe(store: LibraryStore, force: Boolean = false, onDone: (Boolean) -> Unit) {
        val now = SystemClock.elapsedRealtime()
        val wait = if (force || !store.online) 5_000 else 60_000
        if (store.base().isBlank() || (lastProbe > 0 && now - lastProbe < wait) || !probing.compareAndSet(false, true)) return
        lastProbe = now
        Thread { try { onDone(store.probe()) } finally { probing.set(false) } }.apply { isDaemon = true }.start()
    }
}
