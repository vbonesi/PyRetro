package com.pyretro.app

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.focusRestorer
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.key.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.grid.LazyGridState
import kotlinx.coroutines.delay
import androidx.compose.foundation.lazy.items
import androidx.compose.ui.text.font.FontWeight

/** N15: nenhuma faixa de botões rola para o lado; os botões quebram em linhas (mesma DSL item/items da antiga LazyRow). */
class FlowScope { val parts = mutableListOf<@Composable () -> Unit>()
    fun item(content: @Composable () -> Unit) { parts += content }
    fun <T> items(list: List<T>, content: @Composable (T) -> Unit) { list.forEach { x -> parts += { content(x) } } } }

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ButtonFlow(modifier: Modifier = Modifier, content: FlowScope.() -> Unit) {
    val scope = FlowScope().apply(content)
    FlowRow(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) { scope.parts.forEach { it() } }
}

/** Último card focado por tela: voltar da ficha devolve o foco a ele (N14). */
object FocusMemory { private val last = mutableMapOf<String, String>()
    fun set(screen: String, key: String) { last[screen] = key }
    fun get(screen: String): String? = last[screen] }

/** Painel lateral com lista vertical (N11): ↑/↓ move, A escolhe, B ou Voltar fecham sem mudar nada. */
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun SidePanel(title: String, onDismiss: () -> Unit, content: LazyListScope.() -> Unit) {
    Dialog(onDismiss, DialogProperties(usePlatformDefaultWidth = false)) {
        Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.45f)).clickable { onDismiss() }
            .onPreviewKeyEvent { e -> if (e.type == KeyEventType.KeyDown && (e.key == Key.ButtonB || e.key == Key.Escape)) { onDismiss(); true } else false },
            contentAlignment = Alignment.CenterEnd) {
            Surface(Modifier.fillMaxHeight().width(340.dp).clickable(enabled = false) {}, color = MaterialTheme.colorScheme.surface) {
                Column(Modifier.padding(16.dp).statusBarsPadding().navigationBarsPadding()) {
                    Text(title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 8.dp))
                    LazyColumn(Modifier.fillMaxSize().focusRestorer(), verticalArrangement = Arrangement.spacedBy(6.dp), content = content)
                }
            }
        }
    }
}

/** Item do painel; o marcado como [initial] recebe o foco ao abrir. */
@Composable
fun PanelItem(label: String, selected: Boolean = false, initial: Boolean = false, onClick: () -> Unit) {
    val fr = remember { FocusRequester() }
    if (initial) LaunchedEffect(Unit) { runCatching { fr.requestFocus() } }
    RingButton((if (selected) "✓ " else "") + label, Modifier.fillMaxWidth().focusRequester(fr), selected = selected, onClick = onClick)
}

/** Foco inicial e memória (N14): devolve o card da última visita (ou o primeiro) e foca nele ao abrir a tela. A chave que recebe o [FocusRequester] vem em `first`. */
@Composable
fun rememberRestore(screen: String, keys: List<String>, state: LazyGridState): Pair<String?, FocusRequester> {
    val target = remember { FocusMemory.get(screen) }
    val fr = remember { FocusRequester() }
    val key = target?.takeIf { it in keys } ?: keys.firstOrNull()
    LaunchedEffect(key != null) {
        val i = key?.let { keys.indexOf(it) } ?: -1
        if (i >= 0) { state.scrollToItem(i); delay(200); runCatching { fr.requestFocus() } }
    }
    return key to fr
}
