package com.pyretro.app

/** Onde a sessão fica guardada; no app é o SharedPreferences, nos testes um mapa. */
interface SessionStore {
    fun getString(key: String): String?
    fun getLong(key: String): Long
    fun getBoolean(key: String): Boolean
    fun put(values: Map<String, Any?>)
}

class PrefsSessionStore(private val prefs: android.content.SharedPreferences) : SessionStore {
    override fun getString(key: String) = prefs.getString(key, null)
    override fun getLong(key: String) = prefs.getLong(key, 0)
    override fun getBoolean(key: String) = prefs.getBoolean(key, false)
    override fun put(values: Map<String, Any?>) {
        val edit = prefs.edit()
        values.forEach { (k, v) -> when (v) { null -> edit.remove(k); is String -> edit.putString(k, v); is Long -> edit.putLong(k, v); is Boolean -> edit.putBoolean(k, v) } }
        edit.apply()
    }
}

/** O que sobra de uma sessão de jogo quando o usuário volta ao PyRetro. */
data class EndedSession(val key: String, val minutes: Long) { val worthOffering get() = PlaySession.worthOffering(minutes) }

/**
 * Sessão de jogo: começa ao abrir o emulador, marca que o PyRetro saiu de cena e, na volta, devolve o tempo para o usuário confirmar.
 * Fica guardada (relógio de parede) para não se perder se o Android encerrar o app enquanto se joga.
 */
object PlaySession {
    const val MIN = 1; const val MAX = 1440
    private const val KEY = "session:key"; private const val START = "session:start"; private const val LEFT = "session:left"

    fun minutes(startedAt: Long, now: Long) = ((now - startedAt) / 60_000).coerceAtLeast(0)
    fun worthOffering(minutes: Long) = minutes >= MIN
    fun clamp(minutes: Long) = minutes.coerceIn(MIN.toLong(), MAX.toLong())
    fun valid(value: Int?) = value != null && value in MIN..MAX

    fun begin(store: SessionStore, gameKey: String, now: Long) = store.put(mapOf(KEY to gameKey, START to now, LEFT to false))
    fun active(store: SessionStore): String? = store.getString(KEY)
    /** O PyRetro foi para segundo plano (o emulador abriu). Sem sessão ativa, não faz nada. */
    fun markLeft(store: SessionStore) { if (active(store) != null) store.put(mapOf(LEFT to true)) }
    /** Na volta: só encerra se o app realmente saiu de cena; devolve o jogo e o tempo. */
    fun end(store: SessionStore, now: Long): EndedSession? {
        val key = active(store) ?: return null
        if (!store.getBoolean(LEFT)) return null
        val minutes = minutes(store.getLong(START), now)
        store.put(mapOf(KEY to null, START to null, LEFT to null))
        return EndedSession(key, minutes)
    }
    /** Como [end], mas sem apagar: a sessão só sai do disco quando o jogo for achado ([finish]). */
    fun peek(store: SessionStore, now: Long): EndedSession? {
        val key = active(store) ?: return null
        if (!store.getBoolean(LEFT)) return null
        return EndedSession(key, minutes(store.getLong(START), now))
    }
    fun finish(store: SessionStore) = cancel(store)

    sealed interface Resolution {
        object None : Resolution
        /** A lista de jogos ainda não chegou (o app acabou de nascer): a sessão continua guardada. */
        object Pending : Resolution
        data class Deliver(val ended: EndedSession) : Resolution
        /** O jogo não está mais na lista: avisar em vez de sumir em silêncio. */
        data class Missing(val ended: EndedSession) : Resolution
    }

    /** Decide o que fazer com a sessão guardada; só apaga quando entrega ou quando tem certeza de que o jogo sumiu. */
    fun resolve(store: SessionStore, now: Long, knownKeys: Set<String>, loaded: Boolean): Resolution {
        val ended = peek(store, now) ?: return Resolution.None
        return when {
            ended.key in knownKeys -> { finish(store); Resolution.Deliver(ended) }
            !loaded -> Resolution.Pending
            else -> { finish(store); Resolution.Missing(ended) }
        }
    }

    fun cancel(store: SessionStore) = store.put(mapOf(KEY to null, START to null, LEFT to null))
}
