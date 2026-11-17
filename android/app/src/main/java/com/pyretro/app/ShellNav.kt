package com.pyretro.app

/** Destinos da casca em Compose. */
enum class Destination(val label: String, val symbol: String) {
    INICIO("Início", "🏠"),
    BIBLIOTECA("Biblioteca", "📚"),
    DESEJADOS("Desejados", "♡"),
    BUSCA("Busca", "🔍");
}

enum class NavLayout { BOTTOM_BAR, RAIL }

/** Barra lateral em paisagem ou com controle ligado; barra inferior em retrato com toque. */
fun navLayout(landscape: Boolean, gamepad: Boolean) = if (landscape || gamepad) NavLayout.RAIL else NavLayout.BOTTOM_BAR

/** Pilha de navegação: o início fica sempre na base; escolher outro destino empilha sobre ele e voltar chega ao início. */
class NavStack(private val start: Destination = Destination.INICIO) {
    private val stack = mutableListOf(start)
    val current get() = stack.last()
    val canGoBack get() = stack.size > 1
    fun select(destination: Destination) {
        stack.clear(); stack.add(start); if (destination != start) stack.add(destination)
    }
    fun back(): Boolean { if (!canGoBack) return false; stack.removeAt(stack.lastIndex); return true }
}
