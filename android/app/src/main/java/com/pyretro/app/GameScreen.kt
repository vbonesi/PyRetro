package com.pyretro.app

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.focusRestorer
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Botão com anel de foco visível (controle e teclado). */
@Composable
internal fun RingButton(label: String, modifier: Modifier = Modifier, primary: Boolean = false, selected: Boolean = false, onClick: () -> Unit) {
    var focused by remember { mutableStateOf(false) }
    val m = modifier.border(3.dp, focusRing(focused), RoundedCornerShape(50)).onFocusChanged { focused = it.hasFocus }
    when {
        primary -> Button(onClick, m.fillMaxWidth().heightIn(min = 56.dp)) { Text(label, fontSize = 17.sp, fontWeight = FontWeight.Bold) }
        selected -> FilledTonalButton(onClick, m) { Text(label) }
        else -> OutlinedButton(onClick, m) { Text(label) }
    }
}

/**
 * Ficha do jogo (A3): uma ação principal conforme o contexto, fileira secundária, progresso e nota direto aqui e o resto em "⋯ Mais".
 * Os fluxos pesados (baixar, jogar, saves, ROMs, Drive, editar, capa, remover) ainda são os da tela antiga: [onAction] os abre.
 */
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun GameScreen(store: LibraryStore, game: Game, facts: GameFacts, rev: Int, onAction: (GameAction) -> Unit, onChanged: () -> Unit, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val tracking = remember(game.key, rev) { store.tracking(game) }
    val nota = remember(game.key, rev) { TrackingRules.value(tracking, "nota") as Double? }
    val minutes = remember(game.key, rev) { store.prefs.getLong("time:${game.key}", 0) / 60 }
    val sinopse = tracking.optString("sinopse").takeUnless { tracking.isNull("sinopse") }.orEmpty()
    val primary = GameRules.primary(facts)
    var progressOpen by rememberSaveable(game.key) { mutableStateOf(false) }
    var moreOpen by rememberSaveable(game.key) { mutableStateOf(false) }
    val firstFocus = remember { FocusRequester() }
    LaunchedEffect(game.key) { runCatching { firstFocus.requestFocus() } }
    val cover = rememberCover(store, game)

    @Composable fun Info() {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(game.name, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(listOfNotNull(game.platform, GameRules.state(facts), GameRules.playedLabel(minutes)).joinToString(" · "), fontSize = 14.sp)
            nota?.let { Text(NotaRules.symbol(it) + " " + TrackingRules.label(it) + if (NotaRules.special(it)) " · jogo muito especial" else "",
                color = NotaRules.color(it)?.let { c -> Color(c) } ?: MaterialTheme.colorScheme.onBackground, fontSize = 16.sp) }
            OndeRoda.selos(tracking).takeIf { it.isNotEmpty() }?.let { Text("Onde jogar: " + OndeRoda.detalhe(tracking).ifBlank { it.joinToString(" · ") }, fontSize = 15.sp, fontWeight = FontWeight.Bold) }
            if (sinopse.isNotBlank()) Text(sinopse, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            primary?.let { (action, label) -> RingButton(label, Modifier.focusRequester(firstFocus), primary = true) { onAction(action) } }
            GameRules.notes(facts).forEach { Text(it, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant) }
            // Fileira secundária: favorito, fixar e as ações de uso comum.
            ButtonFlow() {
                item { RingButton(if (facts.favorite) "★ Favorito" else "☆ Favoritar", selected = facts.favorite) { store.setFavorite(game, !facts.favorite); onChanged() } }
                if (facts.rom) item { RingButton(if (facts.pinned) "📌 Fixado" else "📌 Fixar", selected = facts.pinned) {
                    runCatching { SpaceStore(store).setPinned(game, !facts.pinned) }; onChanged() } }
                items(GameRules.secondary(facts)) { a -> RingButton(GameRules.label(a)) { onAction(a) } }
            }
            // Progresso e tempo.
            RingButton((if (progressOpen) "▾ " else "▸ ") + "Progresso e tempo") { progressOpen = !progressOpen }
            if (progressOpen) Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                ButtonFlow() {
                    items(listOf("iniciado" to "Iniciado", "finalizado" to "Finalizado", "platinado" to "Platinado")) { (field, label) ->
                        val on = tracking.optBoolean(field)
                        RingButton((if (on) "✓ " else "○ ") + label, selected = on) {
                            store.setProgress(game, field, !on)
                            val finished = store.tracking(game).optBoolean("finalizado")
                            if (GameLogic.offerRemoval(tracking.optBoolean("finalizado"), finished, game.localUri != null) && !facts.pinned) onAction(GameAction.REMOVE) else onChanged()
                        }
                    }
                }
                if (game.id.isNotBlank()) { // nota só vale para jogo da Biblioteca; ROM solta não cria cadastro
                    Text("Nota (0–11): ${if (NotaRules.special(nota)) "✦ " else ""}${TrackingRules.label(nota)}", fontWeight = FontWeight.Bold)
                    ButtonFlow() {
                        items(listOf("−1" to -1.0, "−0,1" to -0.1, "+0,1" to 0.1, "+1" to 1.0)) { (label, delta) ->
                            RingButton(label) { store.setNota(game, TrackingRules.adjust(nota, delta)); onChanged() }
                        }
                        if (nota != null) item { RingButton("Limpar") { store.setNota(game, null); onChanged() } }
                    }
                }
                val sessions = tracking.optJSONObject("_play_sessions")?.let { v -> v.keys().asSequence().sumOf { v.optLong(it) } } ?: 0L
                Text("$minutes min neste celular · ${sessions / 60} min em sessões compartilhadas na Biblioteca.", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            // O raro fica no menu ⋯.
            val more = GameRules.more(facts)
            if (more.isNotEmpty()) {
                RingButton("⋯ Mais" + if (moreOpen) " ▾" else "") { moreOpen = !moreOpen }
                if (moreOpen) more.forEach { a -> RingButton(GameRules.label(a), Modifier.fillMaxWidth()) { onAction(a) } }
            }
        }
    }

    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) { TextButton(onBack) { Text("‹ Voltar") } }
        BoxWithConstraints(Modifier.fillMaxSize()) {
            if (maxWidth >= 600.dp) Row(Modifier.fillMaxSize().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                CoverBox(cover, game.name, Modifier.width(220.dp).clipToBounds())
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(bottom = 24.dp)) { Info() }
            } else Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                CoverBox(cover, game.name, Modifier.fillMaxWidth(0.6f).align(androidx.compose.ui.Alignment.CenterHorizontally))
                Info()
            }
        }
    }
}
