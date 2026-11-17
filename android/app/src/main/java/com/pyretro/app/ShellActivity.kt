package com.pyretro.app

import android.content.Intent
import android.content.res.Configuration
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
class ShellActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val nav = NavStack()
        setContent {
            PyRetroTheme {
                var current by remember { mutableStateOf(nav.current) }
                val landscape = LocalConfiguration.current.orientation == Configuration.ORIENTATION_LANDSCAPE
                val layout = navLayout(landscape, hasGamepad())
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
                        DestinationScreen(current, Modifier.weight(1f))
                    }
                }
            }
        }
    }

    private fun hasGamepad() = InputDevice.getDeviceIds().any {
        InputDevice.getDevice(it)?.sources?.and(InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
    }

    private fun openLegacy(collection: String) =
        startActivity(Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_COLLECTION, collection))

    @Composable
    private fun DestinationScreen(destination: Destination, modifier: Modifier) {
        Column(modifier.verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(destination.label, style = MaterialTheme.typography.headlineMedium)
            Text("Esta tela ainda é a versão anterior do app; ela migra para o novo desenho nas próximas etapas.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            when (destination) {
                Destination.BIBLIOTECA -> { LegacyButton("Neste celular") { openLegacy("cell") }; LegacyButton("Catálogo") { openLegacy("catalog") } }
                else -> LegacyButton("Abrir ${destination.label}") { openLegacy(destination.legacy) }
            }
            if (destination == Destination.INICIO) {
                HorizontalDivider(Modifier.padding(vertical = 8.dp))
                Text("Outras telas atuais", style = MaterialTheme.typography.titleMedium)
                listOf("systems" to "Sistemas", "favorites" to "Favoritos", "ranking" to "Ranking", "stream" to "Stream").forEach { (id, label) ->
                    LegacyButton(label) { openLegacy(id) }
                }
            }
        }
    }

    @Composable
    private fun LegacyButton(label: String, onClick: () -> Unit) = FilledTonalButton(onClick, Modifier.fillMaxWidth()) { Text(label) }
}
