package com.pyretro.app

/** Jogos do catálogo em cache ligados às ROMs das pastas do celular; [problems] são as pastas que não deu para ler. */
class LoadedGames(val games: List<Game>, val problems: List<String>)

/** Mesma leitura que a tela antiga fazia em `reloadLocal`; fora da thread principal. */
fun LibraryStore.loadGames(catalog: List<Game> = cached()): LoadedGames {
    val problems = mutableListOf<String>()
    val roms = folders.keys.flatMap { code -> runCatching { files(code) }.getOrElse { problems.add(folders.getValue(code)); emptyList() } }
    return LoadedGames(bind(catalog, roms), problems)
}

/** Entrada da Biblioteca/Início a partir do jogo e do progresso guardado no celular. */
fun LibraryStore.entryOf(game: Game): LibEntry {
    val t = tracking(game)
    return LibEntry(game.key, game.name, game.platform, game.localUri != null, t.optBoolean("iniciado"), t.optBoolean("finalizado"), favorite(game),
        TrackingRules.value(t, "nota") as Double?)
}
