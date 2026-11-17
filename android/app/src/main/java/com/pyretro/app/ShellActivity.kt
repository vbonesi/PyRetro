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
            val shell = loaded?.let { ShellData(store, it.games, it.games.map(store::entryOf), true) }
            runOnUiThread { if (!isDestroyed) data = shell ?: ShellData(store, emptyList(), emptyList(), true) }
        }
    }
    override fun onResume() { super.onResume(); reload() }
    override fun onDestroy() { (getSystemService(INPUT_SERVICE) as InputManager).unregisterInputDeviceListener(this); work.shutdown(); super.onDestroy() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = LibraryStore(this)
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
                        val shell = data ?: ShellData(store, emptyList(), emptyList(), false)
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
