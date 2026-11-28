package com.pyretro.app

import android.graphics.BitmapFactory
import android.os.Build
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.ui.focus.focusRequester
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusProperties
import androidx.compose.foundation.focusGroup
import kotlinx.coroutines.launch
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.focusRestorer
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.key.*
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

/** Tudo o que as telas em Compose leem; os jogos vêm do mesmo `LibraryStore` da tela antiga. */
class ShellData(val store: LibraryStore, val games: List<Game>, val entries: List<LibEntry>, val loaded: Boolean, val status: String = "",
    val wish: List<Game> = emptyList(), val wishItems: Map<String, WishItem> = emptyMap(), val info: StatusInfo = StatusInfo()) {
    val statusLabel get() = SituationRules.buttonLabel(info)
    /** Montado uma vez: o card não procura o jogo na lista a cada recomposição. */
    val entryByKey: Map<String, LibEntry> by lazy { entries.associateBy { it.key } }
}

@Composable
internal fun focusRing(focused: Boolean) = if (focused) MaterialTheme.colorScheme.primary else Color.Transparent

/** Capa da lista: baixa do cache/Drive fora da thread principal e tenta de novo duas vezes, como a tela antiga. */
@Composable
internal fun rememberCover(store: LibraryStore, game: Game): ImageBitmap? {
    val bitmap by produceState<ImageBitmap?>(null, game.key, game.cover) {
        for (attempt in 0..2) {
            value = withContext(Dispatchers.IO) {
                runCatching { store.cover(game)?.let { BitmapFactory.decodeFile(it.path, BitmapFactory.Options().apply { inSampleSize = 2 })?.asImageBitmap() } }.getOrNull()
            }
            if (value != null || attempt == 2) break
            delay(4000L * (attempt + 1))
        }
    }
    return bitmap
}

/** Moldura 3:4. Capa perto da proporção preenche (corte ancorado no topo); as demais ficam inteiras sobre a própria capa desfocada. */
@Composable
fun CoverBox(bitmap: ImageBitmap?, description: String, modifier: Modifier = Modifier) {
    Box(modifier.fillMaxWidth().aspectRatio(3f / 4f).background(Color(0xFF101D30)), contentAlignment = Alignment.Center) {
        if (bitmap == null) {
            Image(painterResource(R.drawable.ic_pyretro), description, Modifier.fillMaxSize(0.5f))
        } else if (CoverRules.fit(bitmap.width, bitmap.height) == CoverFit.CROP) {
            Image(bitmap, description, Modifier.fillMaxSize(), contentScale = ContentScale.Crop, alignment = Alignment.TopCenter)
        } else {
            // Abaixo do Android 12 não há blur: o fundo fica só escurecido.
            val backdrop = if (Build.VERSION.SDK_INT >= 31) Modifier.blur(16.dp) else Modifier.alpha(0.35f)
            Image(bitmap, null, Modifier.fillMaxSize().then(backdrop), contentScale = ContentScale.Crop)
            Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.35f)))
            Image(bitmap, description, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
        }
    }
}

private fun whereLabel(game: Game) = when {
    game.key.startsWith("wish:") -> "♡ Desejado"
    game.localUri != null -> "▶ Neste celular"
    game.downloadable -> "⬇ Baixar"
    game.pcLocal -> "🖥 No notebook"
    else -> "Catálogo"
}

@Composable
fun GameCard(data: ShellData, game: Game, onOpen: (Game) -> Unit, modifier: Modifier = Modifier, screen: String = "") {
    var focused by remember { mutableStateOf(false) }
    val shape = RoundedCornerShape(12.dp)
    val favorite = data.entryByKey[game.key]?.favorite == true
    Column(
        modifier.clip(shape).background(MaterialTheme.colorScheme.surface)
            .border(3.dp, focusRing(focused), shape)
            .onFocusChanged { focused = it.hasFocus; if (it.hasFocus && screen.isNotEmpty()) FocusMemory.set(screen, game.key) }
            .clickable { onOpen(game) },
    ) {
        CoverBox(rememberCover(data.store, game), game.name)
        Column(Modifier.padding(horizontal = 8.dp, vertical = 6.dp)) {
            Text((if (favorite) "★ " else "") + game.name, fontWeight = FontWeight.Bold, fontSize = 13.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text("${game.platform} · ${whereLabel(game)}", fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, color = MaterialTheme.colorScheme.onSurfaceVariant)
            val selos = remember(game.key, game.tracking) { OndeRoda.selos(game.tracking) }
            if (selos.isNotEmpty()) Text(selos.joinToString(" · "), fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        }
    }
}

@Composable
internal fun ScreenHeader(title: String, subtitle: String, onOptions: () -> Unit, optionsLabel: String = "Situação") {
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp, top = 12.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.headlineSmall)
            Text(subtitle, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        TextButton(onOptions) { Text(optionsLabel) }
    }
}

@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun HomeScreen(data: ShellData, onOpen: (Game) -> Unit, onStatus: () -> Unit, onPackage: (String) -> Unit, onSeeAll: () -> Unit = {}, modifier: Modifier = Modifier) {
    val byKey = remember(data.games) { data.games.associateBy { it.key } }
    val homeEntries = remember(data.games, data.entries) {
        val prefs = data.store.prefs
        data.entries.map { HomeEntry(it.key, it.name, it.onPhone, it.started, it.finished, it.favorite, prefs.getLong("played:${it.key}", 0), prefs.getLong("time:${it.key}", 0)) }
    }
    val rows = remember(homeEntries) { HomeRules.rows(homeEntries) }
    val firstShelf = remember { FocusRequester() }
    Column(modifier.fillMaxSize().focusProperties { enter = { if (rows.firstOrNull()?.second?.any { byKey[it] != null } == true) firstShelf else FocusRequester.Default } }.focusGroup()) {
        ScreenHeader("Início", listOf("${data.games.size} jogos", data.status).filter { it.isNotBlank() }.joinToString(" · "), onStatus, data.statusLabel)
        LazyColumn(Modifier.fillMaxSize().focusRestorer(), contentPadding = PaddingValues(bottom = 24.dp)) {
            if (rows.isEmpty()) item {
                Text(if (data.loaded) "Escolha a pasta Jogos em Situação e opções ou carregue o catálogo. Jogos iniciados, abertos por aqui e favoritos aparecem em fileiras."
                    else "Carregando…", Modifier.padding(16.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            itemsIndexed(rows, key = { _, r -> r.first }) { rowIndex, (title, keys) ->
                Text(title, Modifier.padding(start = 16.dp, top = 14.dp, bottom = 4.dp), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Shelf(data, "inicio:$title", keys, byKey, onOpen, onSeeAll, if (rowIndex == 0) firstShelf else null)
            }
            item {
                // Stream deixou de ser um destino: são três atalhos para os clientes de transmissão.
                Text("Stream", Modifier.padding(start = 16.dp, top = 20.dp, bottom = 4.dp), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                LazyRow(Modifier.focusRestorer(), contentPadding = PaddingValues(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(StreamRules.clients) { c -> RingButton(c.label) { onPackage(c.pkg) } }
                }
                Text("Login e escolha do console ficam nos clientes. Abrir um deles não liga o console nem inicia transmissão.", Modifier.padding(horizontal = 16.dp, vertical = 6.dp), fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun LibraryScreen(data: ShellData, onOpen: (Game) -> Unit, onStatus: () -> Unit, onDraw: (List<String>) -> Unit, onStats: () -> Unit, modifier: Modifier = Modifier) {
    var filter by rememberSaveable { mutableStateOf(QuickFilter.TUDO) }
    var panel by rememberSaveable { mutableStateOf("") } // "", "filtro" ou "acoes"
    val counts = remember(data.entries) { LibraryRules.counts(data.entries) }
    val byKey = remember(data.games) { data.games.associateBy { it.key } }
    val keys = remember(data.entries, filter) { LibraryRules.apply(data.entries, filter) }
    val gridState = rememberLazyGridState()
    val (focusKey, focusRequester) = rememberRestore("biblioteca", keys, gridState)
    Column(modifier.fillMaxSize().onPreviewKeyEvent { event ->
        // LB/RB trocam o filtro rápido; X abre os filtros e Start as ações (N11), como no modo TV.
        if (event.type != KeyEventType.KeyDown || panel.isNotEmpty()) false
        else when (event.key) {
            Key.ButtonL1 -> { filter = LibraryRules.step(filter, -1); true }
            Key.ButtonR1 -> { filter = LibraryRules.step(filter, 1); true }
            Key.ButtonX -> { panel = "filtro"; true }
            Key.ButtonStart -> { panel = "acoes"; true }
            else -> false
        }
    }) {
        ScreenHeader("Biblioteca", "${keys.size} de ${data.games.size} jogos", onStatus, data.statusLabel)
        Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            RingButton("Filtro: ${filter.label} (${counts[filter] ?: 0}) ▾", Modifier.weight(1f)) { panel = "filtro" }
            RingButton("⋯ Ações") { panel = "acoes" }
        }
        if (keys.isEmpty()) Text(if (data.loaded) "Nenhum jogo neste filtro." else "Carregando…", Modifier.padding(16.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
        LazyVerticalGrid(GridCells.Adaptive(132.dp), Modifier.fillMaxSize().focusRestorer(), gridState, contentPadding = PaddingValues(12.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(keys, key = { it }) { key -> byKey[key]?.let { GameCard(data, it, onOpen, if (key == focusKey) Modifier.focusRequester(focusRequester) else Modifier, "biblioteca") } }
        }
    }
    if (panel == "filtro") SidePanel("Filtro", { panel = "" }) {
        items(QuickFilter.values().toList()) { f -> PanelItem("${f.label} (${counts[f] ?: 0})", f == filter, f == filter) { filter = f; panel = "" } }
    }
    if (panel == "acoes") SidePanel("Ações", { panel = "" }) {
        items(OndeRoda.Grupo.values().toList()) { g ->
            PanelItem("🎲 Sortear: ${g.label}", initial = g == OndeRoda.Grupo.RETRO) {
                panel = ""
                val pool = (data.games + data.wish).filter { OndeRoda.noGrupo(g, it.code, it.tracking) }
                onDraw(if (g == OndeRoda.Grupo.TODOS) keys.ifEmpty { pool.map { it.key } } else pool.map { it.key })
            }
        }
        item { PanelItem("📊 Estatísticas") { panel = ""; onStats() } }
    }
}

/**
 * Prateleira do Início com foco fixo (N12): o card focado vai para a 1ª coluna e a fileira desliza por baixo; o fim tem "Ver tudo →".
 * LB/RB pulam uma tela; o último card focado da fileira volta a ter o foco (e a posição) ao retornar.
 */
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun Shelf(data: ShellData, screen: String, keys: List<String>, byKey: Map<String, Game>, onOpen: (Game) -> Unit, onSeeAll: () -> Unit, entry: FocusRequester?) {
    val memory = remember { FocusMemory.get(screen)?.let { keys.indexOf(it) } ?: -1 }
    val state = rememberLazyListState(initialFirstVisibleItemIndex = maxOf(memory, 0))
    val scope = rememberCoroutineScope()
    val focusManager = LocalFocusManager.current
    val start = entry ?: remember { FocusRequester() }
    if (memory >= 0 || entry != null) LaunchedEffect(Unit) { kotlinx.coroutines.delay(250); runCatching { start.requestFocus() } }
    LazyRow(Modifier.focusRestorer().onPreviewKeyEvent { e ->
        if (e.type != KeyEventType.KeyDown) false
        else when (e.key) {
            Key.ButtonR1, Key.ButtonL1 -> { val dir = if (e.key == Key.ButtonR1) FocusDirection.Right else FocusDirection.Left; repeat(maxOf(state.layoutInfo.visibleItemsInfo.size - 1, 1)) { focusManager.moveFocus(dir) }; true }
            else -> false
        }
    }, state = state, contentPadding = PaddingValues(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        itemsIndexed(keys, key = { _, k -> k }) { index, key ->
            byKey[key]?.let { g ->
                val mine = if (memory >= 0) index == memory else index == 0
                GameCard(data, g, onOpen, Modifier.width(132.dp).then(if (mine) Modifier.focusRequester(start) else Modifier)
                    .onFocusChanged { if (it.hasFocus) { FocusMemory.set(screen, key); scope.launch { state.animateScrollToItem(index) } } }, screen = "")
            }
        }
        item(key = "ver-tudo") { RingButton("Ver tudo →", Modifier.width(132.dp).padding(vertical = 40.dp)) { onSeeAll() } }
    }
}
