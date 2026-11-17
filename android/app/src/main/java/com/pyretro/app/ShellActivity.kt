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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp

/**
 * Casca nova (A1): barra inferior em retrato, lateral em paisagem ou com controle, navegação com pilha e o tema do modo TV.
 * Enquanto Início, Biblioteca e Desejados não migram (A2 a A4), cada destino abre a tela antiga (MainActivity) na coleção certa.
 */
class ShellActivity : ComponentActivity(), InputManager.InputDeviceListener {
    private lateinit var store: LibraryStore
    private var data by mutableStateOf<ShellData?>(null)
    private var gamepad by mutableStateOf(false)
    private var status by mutableStateOf("")
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

    /** Carrega os jogos como a tela antiga (catálogo em cache + pastas do celular), fora da thread principal. */
    private fun reload() {
        work.execute {
            val loaded = runCatching { store.loadGames() }.getOrNull()
            val list = loaded?.games ?: emptyList()
            val entries = list.map(store::entryOf)
            val line = statusLine(list.isEmpty())
            runOnUiThread { if (!isDestroyed) { games = list; status = line; data = ShellData(store, list, entries, true, line) } }
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
    override fun onResume() { super.onResume(); reload(); syncNow(force = false) }
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
                BackHandler(enabled = current != Destination.INICIO) { nav.back(); current = nav.current }
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
                        when (current) {
                            Destination.INICIO -> HomeScreen(shell, ::openGame, ::openLegacy, Modifier.weight(1f))
                            Destination.BIBLIOTECA -> LibraryScreen(shell, ::openGame, ::openLegacy, Modifier.weight(1f))
                            else -> DestinationScreen(current, Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }

    private fun openLegacy(collection: String) =
        startActivity(Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_COLLECTION, collection))
    /** A ficha continua sendo a da tela antiga até o A3. */
    private fun openGame(game: Game) =
        startActivity(Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_GAME, game.key))

    @Composable
    private fun DestinationScreen(destination: Destination, modifier: Modifier) {
        Column(modifier.verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(destination.label, style = MaterialTheme.typography.headlineMedium)
            Text("Esta tela ainda é a versão anterior do app; ela migra para o novo desenho nas próximas etapas.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            LegacyButton("Abrir ${destination.label}") { openLegacy(destination.legacy) }
        }
    }

    @Composable
    private fun LegacyButton(label: String, onClick: () -> Unit) = FilledTonalButton(onClick, Modifier.fillMaxWidth()) { Text(label) }
}
