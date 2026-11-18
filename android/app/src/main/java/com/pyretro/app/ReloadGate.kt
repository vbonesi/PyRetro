package com.pyretro.app

import java.util.concurrent.atomic.AtomicInteger

/** Recarga da lista: cada leitura recebe um número; só a mais nova pode publicar (uma leitura antiga e lenta nunca sobrescreve a atual). */
class ReloadGate {
    private val counter = AtomicInteger()
    fun next(): Int = counter.incrementAndGet()
    fun isCurrent(generation: Int): Boolean = generation == counter.get()
}

object RemovalView {
    /** Remoção bem-sucedida: o arquivo local sai do jogo; entrada que só existia no celular (sem cadastro, PC ou Drive) sai da lista. */
    fun afterLocalRemoval(games: List<Game>, key: String): List<Game> {
        val game = games.firstOrNull { it.key == key } ?: return games
        game.localUri = null
        val onlyLocal = game.id.isEmpty() && !game.pcLocal && !game.drive
        return if (onlyLocal) games.filter { it.key != key } else games
    }
}
