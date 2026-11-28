package com.pyretro.app

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusProperties
import androidx.compose.foundation.focusGroup
import androidx.compose.ui.input.key.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.focusRestorer
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Busca (A4a): procura pelo nome entre os jogos carregados; o campo tem anel de foco para o controle. */
@Composable
fun SearchScreen(data: ShellData, onOpen: (Game) -> Unit, onStatus: () -> Unit, modifier: Modifier = Modifier) {
    var query by rememberSaveable { mutableStateOf("") }
    val byKey = remember(data.games) { data.games.associateBy { it.key } }
    val keys = remember(data.entries, query) { LibraryRules.search(data.entries, query) }
    var focused by remember { mutableStateOf(false) }
    val focus = LocalFocusManager.current
    Column(modifier.fillMaxSize()) {
        ScreenHeader("Busca", if (query.isBlank()) "Procure pelo nome, plataforma ou gênero" else "${keys.size} resultado(s)", onStatus, data.statusLabel)
        OutlinedTextField(
            query, { query = it }, Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)
                .border(3.dp, focusRing(focused), RoundedCornerShape(8.dp)).onFocusChanged { focused = it.hasFocus },
            singleLine = true, label = { Text("Buscar jogo") },
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search), keyboardActions = KeyboardActions(onSearch = { focus.clearFocus() }),
        )
        if (query.isNotBlank() && keys.isEmpty()) Text("Nenhum jogo encontrado.", Modifier.padding(16.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
        LazyVerticalGrid(GridCells.Adaptive(132.dp), Modifier.fillMaxSize(), contentPadding = PaddingValues(12.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(keys, key = { it }) { key -> byKey[key]?.let { GameCard(data, it, onOpen) } }
        }
    }
}

/** Desejados (A4a): a lista do notebook, com filtro por loja; abrir um item mostra a ficha da lista. */
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun WishlistScreen(data: ShellData, onOpen: (Game) -> Unit, onStatus: () -> Unit, modifier: Modifier = Modifier) {
    var store by rememberSaveable { mutableStateOf("") }
    var panel by rememberSaveable { mutableStateOf(false) }
    val items = remember(data.wishItems) { data.wishItems.values.toList() }
    val stores = remember(items) { WishRules.stores(items) }
    val visible = remember(items, store, data.wish) { val keys = WishRules.filter(items, store).map(ExtrasRules::wishKey).toSet(); data.wish.filter { it.key in keys } }
    val gridState = rememberLazyGridState()
    val (focusKey, focusRequester) = rememberRestore("desejados", visible.map { it.key }, gridState)
    Column(modifier.fillMaxSize().onPreviewKeyEvent { e -> if (e.type == KeyEventType.KeyDown && e.key == Key.ButtonX && stores.size > 1 && !panel) { panel = true; true } else false }) {
        ScreenHeader("Desejados", "${visible.size} jogo(s) na lista", onStatus, data.statusLabel)
        if (stores.size > 1) Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp)) {
            RingButton("Loja: ${if (store.isBlank()) "Todos" else ExtrasRules.STORES.getValue(store)} ▾", Modifier.weight(1f)) { panel = true }
        }
        if (visible.isEmpty()) Text(if (data.loaded) "Nenhum jogo na lista de desejos. Para adicionar, use o modo TV ou a interface do notebook." else "Carregando…",
            Modifier.padding(16.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
        LazyVerticalGrid(GridCells.Adaptive(132.dp), Modifier.fillMaxSize().focusRestorer(), gridState, contentPadding = PaddingValues(12.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(visible, key = { it.key }) { g -> GameCard(data, g, onOpen, if (g.key == focusKey) Modifier.focusRequester(focusRequester) else Modifier, "desejados") }
        }
    }
    if (panel) SidePanel("Loja", { panel = false }) {
        items(listOf("") + stores) { s -> PanelItem(if (s.isBlank()) "Todos" else ExtrasRules.STORES.getValue(s), s == store, s == store) { store = s; panel = false } }
    }
}

/** Ficha de um desejo: Comprado (vai para a Biblioteca) ou Tirar da lista, sempre com confirmação. */
@Composable
fun WishDetailScreen(data: ShellData, game: Game, onLeave: (WishItem, Boolean) -> Unit, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val item = data.wishItems[game.key]
    var confirm by remember { mutableStateOf<Boolean?>(null) }
    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) { TextButton(onBack) { Text("‹ Voltar") } }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            CoverBox(rememberCover(data.store, game), game.name, Modifier.fillMaxWidth(0.5f).align(androidx.compose.ui.Alignment.CenterHorizontally))
            Text(game.name, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            if (item != null) {
                Text(WishRules.subtitle(item), fontSize = 14.sp)
                RingButton("✅ Comprado", primary = true) { confirm = true }
                RingButton("🗑 Tirar da lista") { confirm = false }
            } else Text("Este desejo já saiu da lista.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
    val bought = confirm
    if (bought != null && item != null) AlertDialog(
        onDismissRequest = { confirm = null },
        text = { Text(if (bought) "Marcar \"${item.name}\" como comprado? Sai dos Desejados e entra na Biblioteca." else "Tirar \"${item.name}\" da lista de desejos?") },
        confirmButton = { TextButton({ confirm = null; onLeave(item, bought) }) { Text(if (bought) "Comprado" else "Tirar") } },
        dismissButton = { TextButton({ confirm = null }) { Text("Voltar") } },
    )
}

/** Situação e opções (A4a): estado do notebook, do Drive, das pastas, da fila e a versão. Seletores de pasta e conta Google ainda abrem a tela antiga. */
@Composable
fun StatusScreen(data: ShellData, note: String, date: (Long) -> String, onTest: () -> Unit, onSync: () -> Unit, onLegacy: (String) -> Unit, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val i = data.info
    @Composable fun Section(title: String, text: String, vararg buttons: Pair<String, () -> Unit>) {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 17.sp)
            Text(text, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (buttons.isNotEmpty()) ButtonFlow() { items(buttons.toList()) { (l, a) -> RingButton(l) { a() } } }
        }
    }
    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) { TextButton(onBack) { Text("‹ Voltar") } }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("Situação e opções", style = MaterialTheme.typography.headlineSmall)
            if (note.isNotBlank()) Text(note, color = MaterialTheme.colorScheme.primary, fontSize = 14.sp)
            Section("🎮 Neste celular", SituationRules.local(i, date))
            Section("🖥 Notebook", SituationRules.notebook(i), *(if (i.serverBlank) arrayOf("Configurar endereço" to { onLegacy("options") }) else arrayOf("Testar conexão" to onTest)))
            Section("☁ Conta Google (Drive)", SituationRules.drive(i), (if (i.driveConnected) "Gerenciar conta" else "Conectar conta Google") to { onLegacy("options") })
            Section("⏳ Biblioteca, progresso e tempo", SituationRules.tracking(i, date), "Sincronizar agora" to onSync)
            Section("⬇ Downloads", SituationRules.downloads(i), "Abrir downloads" to { onLegacy("downloads") })
            Section("📁 Pastas", "Jogos: ${SituationRules.folder(i.rootFolder)}\nRetroArch (saves): ${SituationRules.folder(i.retroarchFolder)}",
                "Escolher pastas" to { onLegacy("options") }, "Saves na nuvem" to { onLegacy("cloud-saves") })
            Section("⚙ Mais opções", "Pastas, endereço do notebook, conta Google, notificações e as telas que ainda são da versão anterior.", "Abrir opções" to { onLegacy("options") })
            Section("ℹ Versão", "PyRetro ${i.version}")
        }
    }
}

/** Opções (A4c): pastas, endereço do notebook, conta Google e notificações na casca; o resto ainda abre telas da versão anterior (A5). */
@Composable
fun OptionsScreen(data: ShellData, flows: GameFlows, onLegacy: (String) -> Unit, onBack: () -> Unit, modifier: Modifier = Modifier) {
    val i = data.info
    var address by remember { mutableStateOf(flows.store.base()) }
    @Composable fun Block(title: String, text: String? = null, content: @Composable ColumnScope.() -> Unit) {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 17.sp)
            if (text != null) Text(text, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            content()
        }
    }
    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) { TextButton(onBack) { Text("‹ Voltar") } }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
            Text("Opções", style = MaterialTheme.typography.headlineSmall)
            Block("📁 Pastas", "Jogos: ${SituationRules.folder(i.rootFolder)}\nRetroArch (saves e estados): ${SituationRules.folder(i.retroarchFolder)}\nROMs ficam em Jogos/<sistema>; saves e estados, por sistema na pasta RetroArch.") {
                ButtonFlow() {
                    item { RingButton("Escolher pasta Jogos") { flows.pickFolder("ROOT") } }
                    item { RingButton("Escolher pasta RetroArch") { flows.pickSyncFolder("retroarch") } }
                }
            }
            Block("🖥 Notebook", SituationRules.notebook(i)) {
                OutlinedTextField(address, { address = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("https://endereço-do-pyretro") })
                ButtonFlow() {
                    item { RingButton("Salvar endereço") { flows.saveServer(address) } }
                    item { RingButton("Atualizar Biblioteca e catálogo") { flows.refreshCatalog() } }
                }
            }
            Block("☁ Conta Google", SituationRules.drive(i)) {
                if (i.driveConnected) RingButton("Desconectar conta Google") { flows.disconnectGoogle() } else RingButton("Conectar conta Google") { flows.connectGoogle() }
            }
            if (!flows.notificationsAllowed()) Block("🔔 Notificações", "Sem permissão, o download em segundo plano não mostra o progresso.") { RingButton("Permitir notificações de download") { flows.notificationSettings() } }
            Block("Telas da versão anterior", "Ainda não foram redesenhadas (A5); abrem em outra tela e voltam para cá.") {
                listOf("Espaço e jogos fixados" to "space", "Lixeira de ROMs deste celular" to "trash", "Saves e estados · todos os jogos" to "sync-files", "Saves na nuvem" to "cloud-saves",
                    "Organizar ROMs novas (notebook)" to "organize", "Texturas HD" to "textures", "Índice manual do Drive" to "index", "Playlists do RetroArch" to "playlists", "Pastas e permissões" to "folders",
                    "Apps instalados" to "apps", "Alterações pendentes" to "pending").chunked(2).forEach { pair ->
                    ButtonFlow() { items(pair) { (l, id) -> RingButton(l) { onLegacy(id) } } }
                }
            }
            Text("PyRetro ${i.version}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
