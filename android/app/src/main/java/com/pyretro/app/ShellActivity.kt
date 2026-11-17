package com.pyretro.app

import android.content.Intent
import android.content.res.Configuration
import android.hardware.input.InputManager
import android.os.Bundle
import android.view.InputDevice
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp

/**
 * Casca nova (A1): barra inferior em retrato, lateral em paisagem ou com controle, navegação com pilha e o tema do modo TV.
 * Início, Biblioteca, Desejados, Busca, ficha e Situação/Opções são telas daqui; o que ainda depende de seletor de pasta ou diálogo grande abre a tela antiga.
 */
class ShellActivity : ComponentActivity(), InputManager.InputDeviceListener {
    private lateinit var store: LibraryStore
    private var data by mutableStateOf<ShellData?>(null)
    private var gamepad by mutableStateOf(false)
    private var status by mutableStateOf("")
    private var openKey by mutableStateOf<String?>(null)
    private var rev by mutableIntStateOf(0)
    private var showStatus by mutableStateOf(false)
    private var statusNote by mutableStateOf("")
    private var wishKey by mutableStateOf<String?>(null)
    private var wishItems = emptyList<WishItem>()
    private var entries = emptyList<LibEntry>()
    private var info = StatusInfo()
    private val extras by lazy { NotebookExtras(store, filesDir) }
    private val flows by lazy { GameFlows(this, store, drive, work, { games }, ::changed, { syncNow(force = true) }) { g, a -> runLegacyAction(g, a) } }
    private val drive by lazy { GoogleDrive(this, store.prefs) }
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())
    private var games = emptyList<Game>()
    private val work = java.util.concurrent.Executors.newSingleThreadExecutor()

    /** Mesmo critério da tela antiga: controle físico (não virtual) com gamepad ou joystick. */
    private fun gamepadPresent() = InputDevice.getDeviceIds().asSequence().mapNotNull { InputDevice.getDevice(it) }
        .any { !it.isVirtual && (it.supportsSource(InputDevice.SOURCE_GAMEPAD) || it.supportsSource(InputDevice.SOURCE_JOYSTICK)) }
    override fun onInputDeviceAdded(deviceId: Int) { gamepad = gamepadPresent() }
    override fun onInputDeviceRemoved(deviceId: Int) { gamepad = gamepadPresent() }
    override fun onInputDeviceChanged(deviceId: Int) { gamepad = gamepadPresent() }

    private fun wishGames(items: List<WishItem>) = items.map { Game(it.id, ExtrasRules.wishKey(it), it.name, ExtrasRules.STORES.getValue(it.source), cover = it.cover, genre = it.genre) }
    private fun buildData() = ShellData(store, games, entries, true, statusLine(games.isEmpty()), wishGames(wishItems), wishItems.associateBy(ExtrasRules::wishKey), info)
    private fun date(t: Long) = java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault()).format(java.util.Date(t))

    /** Tudo o que Situação e opções mostra, lido fora da thread principal. */
    private fun readInfo(problems: List<String>, list: List<Game>): StatusInfo {
        val folders = runCatching { StatusStore(store).folders() }.getOrDefault(emptyList())
        val rows = runCatching { DownloadQueue.get(store).snapshot().filter { it.state != DownloadState.DONE } }.getOrDefault(emptyList())
        val version = runCatching { packageManager.getPackageInfo(packageName, 0).let { "${it.versionName} (${(if (android.os.Build.VERSION.SDK_INT >= 28) it.longVersionCode else @Suppress("DEPRECATION") it.versionCode.toLong())})" } }.getOrDefault("")
        return StatusInfo(list.count { it.localUri != null }, list.size, store.prefs.getLong("updated", 0), problems, store.base().isBlank(), store.online, drive.connected, drive.email,
            folders.firstOrNull { it.code == "ROOT" }?.access ?: FolderAccess.UNSELECTED, folders.firstOrNull { it.code == "retroarch" }?.access ?: FolderAccess.UNSELECTED,
            store.pending(), store.prefs.getLong("library-sync-at", 0), rows.size, rows.count { it.state == DownloadState.FAILED }, rows.count { it.state == DownloadState.PAUSED }, version)
    }

    /** Carrega os jogos como a tela antiga (catálogo em cache + pastas do celular) e os Desejados em cache; com o notebook online, atualiza os Desejados. */
    private fun reload() {
        work.execute {
            val loaded = runCatching { store.loadGames() }.getOrNull()
            val list = loaded?.games ?: emptyList()
            val ent = list.map(store::entryOf)
            val wishes = runCatching { extras.wishlist(false) }.getOrDefault(emptyList())
            val inf = runCatching { readInfo(loaded?.problems ?: emptyList(), list) }.getOrDefault(StatusInfo())
            runOnUiThread { if (!isDestroyed) { games = list; entries = ent; wishItems = wishes; info = inf; status = statusLine(list.isEmpty()); data = buildData() } }
            if (store.online) runCatching { extras.wishlist(true) }.onSuccess { fresh ->
                runOnUiThread { if (!isDestroyed && fresh != wishItems) { wishItems = fresh; data = buildData() } }
            }
        }
    }
    private fun statusLine(catalogEmpty: Boolean) = AppSync.statusLine(store.online, store.prefs.getLong("updated", 0), catalogEmpty) {
        java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault()).format(java.util.Date(it))
    }

    /** Mesma rotina de abertura e retomada da tela antiga (AppSync): sonda o notebook, sincroniza progresso/catálogo e pré-busca capas. */
    private fun syncNow(force: Boolean) {
        fun update() = AppSync.automaticUpdate(this, store, drive, work, force, games.isEmpty()) { _, _ -> runOnUiThread { if (!isDestroyed) reload() } }
        AppSync.probe(store, force) { ok -> runOnUiThread { if (!isDestroyed) { if (ok) update(); reload() } } }
        update()
        handler.postDelayed({ if (!isFinishing && !isDestroyed) work.execute { AppSync.prefetchCovers(this, store, drive, games) } }, 8000)
    }
    override fun onResume() { super.onResume(); rev++; reload(); syncNow(force = false); flows.onResume() }
    override fun onPause() { flows.onPause(); super.onPause() }
    override fun onDestroy() { handler.removeCallbacksAndMessages(null); (getSystemService(INPUT_SERVICE) as InputManager).unregisterInputDeviceListener(this); work.shutdown(); super.onDestroy() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = LibraryStore(this)
        if (AppSync.enabled && drive.connected) LibraryWorker.schedule(this)
        gamepad = gamepadPresent(); (getSystemService(INPUT_SERVICE) as InputManager).registerInputDeviceListener(this, null)
        val nav = NavStack()
        setContent {
            PyRetroTheme {
                var current by remember { mutableStateOf(nav.current) }
                val landscape = LocalConfiguration.current.orientation == Configuration.ORIENTATION_LANDSCAPE
                val layout = navLayout(landscape, gamepad)
                fun select(d: Destination) { nav.select(d); current = nav.current }
                BackHandler(enabled = flows.page != null || wishKey != null || showStatus || openKey != null || current != Destination.INICIO) {
                    when { flows.page != null -> flows.page = null; wishKey != null -> wishKey = null; showStatus -> showStatus = false; openKey != null -> openKey = null; else -> { nav.back(); current = nav.current } }
                }
                FlowDialogs(flows)
                Scaffold(
                    containerColor = MaterialTheme.colorScheme.background,
                    bottomBar = {
                        if (layout == NavLayout.BOTTOM_BAR) NavigationBar {
                            Destination.values().forEach { d ->
                                NavigationBarItem(selected = d == current, onClick = { select(d) }, icon = { Text(d.symbol) }, label = { Text(d.label) })
                            }
                        }
                    },
                ) { padding ->
                    Row(Modifier.padding(padding).fillMaxSize()) {
                        if (layout == NavLayout.RAIL) NavigationRail(containerColor = MaterialTheme.colorScheme.surface) {
                            Spacer(Modifier.weight(1f))
                            Destination.values().forEach { d ->
                                NavigationRailItem(selected = d == current, onClick = { select(d) }, icon = { Text(d.symbol) }, label = { Text(d.label) })
                            }
                            Spacer(Modifier.weight(1f))
                        }
                        val shell = data ?: ShellData(store, emptyList(), emptyList(), false, status)
                        val wish = wishKey?.let { k -> shell.wish.firstOrNull { it.key == k } }
                        val open = openKey?.let { k -> shell.games.firstOrNull { it.key == k } }
                        val mod = Modifier.weight(1f)
                        val page = flows.page
                        when {
                            page != null -> when (page) {
                                is Page.Downloads -> DownloadsScreen(store, ::openLegacy, { flows.page = null }, mod)
                                is Page.Saves -> SavesScreen(flows, page.game, { flows.page = null }, mod)
                                is Page.Cover -> CoverScreen(flows, page.game, page.target, { flows.page = null }, mod)
                                is Page.Edit -> EditScreen(flows, page.game, { flows.page = null }, mod)
                            }
                            showStatus -> StatusScreen(shell, statusNote, ::date, ::testConnection, ::syncProgress, ::openLegacy, { showStatus = false }, mod)
                            wish != null -> WishDetailScreen(shell, wish, ::leaveWish, { wishKey = null }, mod)
                            open != null -> GameScreen(store, open, remember(open.key, rev, shell) { factsOf(open) }, rev, { runAction(open, it) }, ::changed, { openKey = null }, mod)
                            else -> when (current) {
                                Destination.INICIO -> HomeScreen(shell, ::openGame, ::openStatus, ::openPackage, mod)
                                Destination.BIBLIOTECA -> LibraryScreen(shell, ::openGame, ::openStatus, mod)
                                Destination.DESEJADOS -> WishlistScreen(shell, { g -> wishKey = g.key }, ::openStatus, mod)
                                Destination.BUSCA -> SearchScreen(shell, ::openGame, ::openStatus, mod)
                            }
                        }
                    }
                }
            }
        }
    }

    /** Seletores de pasta, conta Google e opções avançadas ainda abrem a tela antiga (A4b/A4c). */
    private fun openLegacy(screen: String) =
        startActivity(Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_SCREEN, screen))
    private fun openStatus() { statusNote = ""; showStatus = true; reload() }
    private fun openPackage(pkg: String) {
        val intent = packageManager.getLaunchIntentForPackage(pkg)
        if (intent == null) android.widget.Toast.makeText(this, "Aplicativo não instalado: $pkg", android.widget.Toast.LENGTH_SHORT).show() else startActivity(intent)
    }
    private fun testConnection() {
        statusNote = "Testando conexão…"
        work.execute {
            val result = runCatching { store.checkConnection() }
            if (result.isSuccess) store.online = true
            runOnUiThread { statusNote = if (result.isSuccess) "Online. PyRetro respondeu em ${date(System.currentTimeMillis())}." else "Sem resposta. Confira o Tailscale e o notebook; o modo offline continua."; reload() }
        }
    }
    private fun syncProgress() {
        statusNote = "Enviando progresso e tempo…"
        work.execute {
            val result = runCatching { store.synchronize() }
            runOnUiThread { statusNote = result.getOrElse { it.message ?: "Não foi possível sincronizar." }; reload() }
        }
    }
    private fun leaveWish(item: WishItem, bought: Boolean) {
        if (!store.cloudLibrary.ready() && !store.online) { android.widget.Toast.makeText(this, "Esta função precisa do notebook online. Ligue o Tailscale e tente de novo.", android.widget.Toast.LENGTH_LONG).show(); return }
        work.execute {
            val result = runCatching { extras.leaveWishlist(item, bought) }
            if (result.isSuccess && bought) runCatching { store.refresh() }
            runOnUiThread {
                android.widget.Toast.makeText(this, result.fold({ if (bought) "${item.name} entrou na Biblioteca." else "${item.name} saiu dos Desejados." }, { it.message ?: "Não foi possível concluir." }), android.widget.Toast.LENGTH_LONG).show()
                if (result.isSuccess) wishKey = null
                reload()
            }
        }
    }
    private fun openGame(game: Game) { openKey = game.key }
    /** Jogar, baixar, saves, capa, editar e remover rodam aqui (GameFlows); o que depende de seletor de pasta/arquivo ou OAuth abre a tela antiga. */
    private fun runAction(game: Game, action: GameAction) = flows.run(game, action)
    private fun runLegacyAction(game: Game, action: GameAction) =
        startActivity(Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_GAME, game.key).putExtra(MainActivity.EXTRA_ACTION, action.id))
    private fun changed() { rev++; reload() }

    private fun factsOf(game: Game): GameFacts {
        val rom = game.code in store.folders
        val queued = runCatching { DownloadQueue.get(store).contains(game.key) }.getOrDefault(false)
        return GameFacts(game.key, game.id, game.code, game.platform, rom, game.localUri != null, queued, store.prefs.contains("cloud:${game.key}"),
            game.downloadable, game.pcLocal, game.drive, store.online, drive.connected, GameLogic.remotePackage(game.platform),
            GameLogic.streamedThroughNotebook(game.platform), packageManager.getLaunchIntentForPackage("com.github.stenzek.duckstation") != null,
            ExtrasRules.coverTarget(game.id, game.cover) != null, rom && SpaceStore(store).pinned(game), store.favorite(game))
    }

    override fun onKeyDown(keyCode: Int, event: android.view.KeyEvent): Boolean {
        // B do controle volta, como na tela antiga.
        if (keyCode == android.view.KeyEvent.KEYCODE_BUTTON_B) { onBackPressedDispatcher.onBackPressed(); return true }
        return super.onKeyDown(keyCode, event)
    }
}
