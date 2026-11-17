package com.pyretro.app

import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

/** Diálogos dos fluxos da ficha: aviso/confirmação, escolha de arquivo/escopo e registro do tempo jogado. */
@Composable
fun FlowDialogs(flows: GameFlows) {
    flows.busy?.let { b ->
        AlertDialog(
            onDismissRequest = {}, title = { Text("Aguarde") },
            text = { Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator(Modifier.size(32.dp)); Text(b.text, fontSize = 15.sp)
            } },
            confirmButton = {}, dismissButton = { if (b.cancelable) TextButton({ flows.cancelBusy() }) { Text("Cancelar") } },
        )
    }
    flows.notice?.let { n ->
        AlertDialog(
            onDismissRequest = { flows.notice = null }, title = { Text(n.title) },
            text = { Text(n.text, Modifier.verticalScroll(rememberScrollState()), fontSize = 14.sp) },
            confirmButton = { Row { 
                n.extra?.let { label -> TextButton({ flows.notice = null; n.onExtra?.invoke() }) { Text(label) } }
                n.confirm?.let { label -> TextButton({ flows.notice = null; n.onConfirm?.invoke() }) { Text(label) } }
            } },
            dismissButton = { TextButton({ flows.notice = null }) { Text(n.dismiss) } },
        )
    }
    flows.choice?.let { c ->
        AlertDialog(
            onDismissRequest = { flows.choice = null }, title = { Text(c.title) },
            text = { Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                c.labels.forEachIndexed { i, label -> RingButton(label, Modifier.fillMaxWidth()) { flows.choice = null; c.onPick(i) } }
            } },
            confirmButton = {}, dismissButton = { TextButton({ flows.choice = null }) { Text("Voltar") } },
        )
    }
    flows.timePrompt?.let { p ->
        var text by remember(p) { mutableStateOf(p.minutes.toString()) }
        AlertDialog(
            onDismissRequest = { flows.timePrompt = null }, title = { Text("Registrar tempo de ${p.game.name}?") },
            text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Confirme os minutos que jogou. O tempo em outros apps pode estar incluído.", fontSize = 14.sp)
                OutlinedTextField(text, { text = it.filter(Char::isDigit).take(4) }, singleLine = true, label = { Text("Minutos") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            } },
            confirmButton = { Row {
                TextButton({ flows.saveTime(p, text.toIntOrNull(), true) }) { Text("Salvar e ver saves") }
                TextButton({ flows.saveTime(p, text.toIntOrNull(), false) }) { Text("Salvar") }
            } },
            dismissButton = { TextButton({ flows.timePrompt = null }) { Text("Descartar") } },
        )
    }
}

@Composable
private fun PageFrame(title: String, onBack: () -> Unit, modifier: Modifier, content: @Composable ColumnScope.() -> Unit) {
    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) { TextButton(onBack) { Text("‹ Voltar") } }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            content()
        }
    }
}

/** Fila de downloads: iniciar, pausar, tentar de novo e tirar da fila; reordenar e cópias parciais seguem na tela antiga. */
@Composable
fun DownloadsScreen(store: LibraryStore, onLegacy: (String) -> Unit, onBack: () -> Unit, modifier: Modifier = Modifier) {
    var rows by remember { mutableStateOf(emptyList<QueuedDownload>()) }
    var running by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var tick by remember { mutableIntStateOf(0) }
    LaunchedEffect(tick) {
        while (true) {
            runCatching { withContext(Dispatchers.IO) { DownloadQueue.get(store).let { it.snapshot() to it.running } } }
                .onSuccess { rows = it.first; running = it.second; error = null }.onFailure { error = "Fila indisponível: ${it.message}" }
            delay(1000)
        }
    }
    fun act(block: () -> Unit) { runCatching(block).onFailure { error = it.message ?: "Não foi possível alterar a fila." }; tick++ }
    PageFrame("Downloads", onBack, modifier) {
        Text("Um arquivo por vez, na ordem escolhida. Ao sair do app, a fila continua em segundo plano com uma notificação de progresso, que tem Pausar.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        val active = rows.firstOrNull { it.state == DownloadState.RUNNING }
        Text(error ?: "${rows.count { it.state == DownloadState.WAITING }} aguardando · ${rows.count { it.state == DownloadState.PAUSED }} pausado(s) · ${rows.count { it.state == DownloadState.FAILED }} falha(s)" +
            (active?.let { " · baixando ${it.game.name}" } ?: ""))
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item { RingButton("Iniciar / continuar fila") { act { DownloadQueue.get(store).start() } } }
            item { RingButton("Pausar fila") { act { DownloadQueue.get(store).pause(); DownloadStore.pause() } } }
            item { RingButton("Reordenar e cópias parciais") { onLegacy("downloads") } }
        }
        val open = rows.filter { it.state != DownloadState.DONE }
        if (open.isEmpty()) Text("Fila vazia.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        open.forEach { row ->
            val percent = row.total?.takeIf { it > 0 }?.let { " · ${row.bytes * 100 / it}%" } ?: ""
            val state = when (row.state) { DownloadState.RUNNING -> "baixando"; DownloadState.WAITING -> "aguardando"; DownloadState.PAUSED -> "pausado"; DownloadState.FAILED -> "falhou"; else -> "" }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(row.game.name, fontWeight = FontWeight.Bold)
                Text(state + percent + (if (row.state == DownloadState.FAILED && row.error.isNotBlank()) " · ${row.error}" else ""), fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (row.state == DownloadState.FAILED || row.state == DownloadState.PAUSED) item { RingButton("Tentar de novo") { act { DownloadQueue.get(store).retry(row.game.key) } } }
                    if (row.state != DownloadState.RUNNING) item { RingButton("Tirar da fila") { act { DownloadQueue.get(store).remove(row.game.key) } } }
                }
            }
        }
    }
}

/** Saves do jogo pela nuvem: nada é sobrescrito sem escolha; esquecer um save e resolver conflito pedem confirmação. */
@Composable
fun SavesScreen(flows: GameFlows, game: Game, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val model = remember(game.key) { flows.savesModel(game) }
    LaunchedEffect(game.key) { model.load() }
    PageFrame("💾 ${game.name}", onBack, modifier) {
        Text(model.info, fontSize = 14.sp)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item { RingButton("Comparar novamente") { if (!model.busy) model.load() } }
            item { RingButton(if (model.showAll) "Mostrar só pendentes" else "Ver também saves em dia") { if (!model.busy) model.toggleAll() } }
            if (model.pending > 0) item { RingButton("Sincronizar agora (${model.pending})") { model.syncAll() } }
        }
        model.conflicts.forEach { (group, item) ->
            Text("⚠ Conflito: ${item.path}", fontWeight = FontWeight.Bold)
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (item.local != null) item { RingButton("Manter o do celular") { model.keepLocal(group, item) } }
                items(item.heads.entries.toList()) { (sha, devices) ->
                    RingButton((if (sha in item.deletedHeads) "Usar exclusão confirmada" else "Usar da nuvem") + " · ${devices.joinToString()} · ${sha.take(12)}") { model.useRemote(group, item, sha) }
                }
            }
        }
        model.forgettable.forEach { (group, item) -> RingButton("Esquecer este save… · ${item.path}", Modifier.fillMaxWidth()) { model.forget(group, item) } }
    }
    model.confirm?.let { n ->
        AlertDialog(onDismissRequest = { model.confirm = null }, title = { Text(n.title) }, text = { Text(n.text, fontSize = 14.sp) },
            confirmButton = { TextButton({ model.confirm = null; n.onConfirm?.invoke() }) { Text(n.confirm ?: "Confirmar") } },
            dismissButton = { TextButton({ model.confirm = null }) { Text(n.dismiss) } })
    }
}

@Composable
fun CoverScreen(flows: GameFlows, game: Game, target: CoverTarget, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val model = remember(game.key) { flows.coverModel(game, target) }
    LaunchedEffect(game.key) { model.search() }
    PageFrame("🖼 Capa de ${game.name}", onBack, modifier) {
        OutlinedTextField(model.query, { model.query = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Buscar") })
        RingButton("Buscar no SteamGridDB") { model.search() }
        if (model.status.isNotBlank()) Text(model.status, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        // Grade simples (a página já rola): três por linha.
        model.results.chunked(3).forEach { line ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                line.forEach { (url, name) ->
                    var focused by remember { mutableStateOf(false) }
                    val shape = RoundedCornerShape(10.dp)
                    Box(Modifier.weight(1f).aspectRatio(3f / 4f).border(3.dp, focusRing(focused), shape).onFocusChanged { focused = it.hasFocus }.clickable { model.choose(url) },
                        contentAlignment = Alignment.Center) {
                        model.thumbs[url]?.let { Image(it, name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit) } ?: Text("…")
                    }
                }
                repeat(3 - line.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
    model.confirm?.let { n ->
        AlertDialog(onDismissRequest = { model.confirm = null }, title = { Text(n.title) }, text = { Text(n.text, fontSize = 14.sp) },
            confirmButton = { TextButton({ model.confirm = null; n.onConfirm?.invoke() }) { Text(n.confirm ?: "Confirmar") } },
            dismissButton = { TextButton({ model.confirm = null }) { Text(n.dismiss) } })
    }
}

@Composable
fun EditScreen(flows: GameFlows, game: Game, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val model = remember(game.key) { flows.editModel(game) }
    LaunchedEffect(game.key) { model.load() }
    var genreMenu by remember { mutableStateOf(false) }
    PageFrame("✎ ${game.name}", onBack, modifier) {
        if (model.message.isNotBlank()) Text(model.message, fontSize = 14.sp)
        if (model.loaded) {
            model.fields.forEach { (field, label) ->
                if (field == "genero") {
                    Text(label, fontSize = 13.sp)
                    RingButton(model.values["genero"].orEmpty().ifBlank { "Sem gênero" } + " ▾") { genreMenu = true }
                    if (genreMenu) AlertDialog(onDismissRequest = { genreMenu = false }, title = { Text("Gênero") },
                        text = { Column(Modifier.verticalScroll(rememberScrollState())) { model.genres.forEach { g -> TextButton({ model.values["genero"] = g; genreMenu = false }, Modifier.fillMaxWidth()) { Text(g.ifBlank { "Sem gênero" }) } } } },
                        confirmButton = {}, dismissButton = { TextButton({ genreMenu = false }) { Text("Voltar") } })
                } else OutlinedTextField(model.values[field].orEmpty(), { model.values[field] = it }, Modifier.fillMaxWidth(), label = { Text(label) }, minLines = if (field == "observacoes" || field == "sinopse") 3 else 1)
            }
            RingButton("Salvar", primary = true) { model.save(onBack) }
        }
    }
}
