package com.pyretro.app

import android.graphics.Bitmap
import androidx.activity.ComponentActivity
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import java.util.concurrent.Executor

/** Aviso ou confirmação: [confirm] só aparece quando há uma ação a confirmar; [extra] é um terceiro botão (como o "Só Moonlight" da tela antiga). */
class NoticeState(val title: String, val text: String, val confirm: String? = null, val dismiss: String = "Voltar",
    val extra: String? = null, val onExtra: (() -> Unit)? = null, val onConfirm: (() -> Unit)? = null)
class ChoiceState(val title: String, val labels: List<String>, val onPick: (Int) -> Unit)
class TimePrompt(val game: Game, val minutes: Long)

sealed interface Page {
    object Downloads : Page
    data class Saves(val game: Game) : Page
    data class Cover(val game: Game, val target: CoverTarget) : Page
    data class Edit(val game: Game) : Page
}

/**
 * Fluxos da ficha (A4b) rodando na casca: jogar com registro do tempo, baixar e fila, saves na nuvem, trocar capa, editar e remover.
 * A lógica sem tela é compartilhada (GameLauncher, PlaySession, DownloadFlow, RomRemoval, CloudPhone, NotebookExtras).
 * Só o que depende de seletor de pasta/arquivo ou OAuth (pasta Jogos, outra ROM, arquivo no Drive, conta Google, texturas, adicionar à
 * Biblioteca e saves de PSP/3DS) ainda abre a tela antiga por [legacy].
 */
class GameFlows(private val activity: ComponentActivity, val store: LibraryStore, private val drive: GoogleDrive, private val work: Executor,
    private val games: () -> List<Game>, private val isLoaded: () -> Boolean, private val changed: () -> Unit, private val syncNow: () -> Unit, private val legacy: (Game, GameAction) -> Unit) {
    var notice by mutableStateOf<NoticeState?>(null)
    var choice by mutableStateOf<ChoiceState?>(null)
    var timePrompt by mutableStateOf<TimePrompt?>(null)
    var page by mutableStateOf<Page?>(null)
    val extras = NotebookExtras(store, activity.filesDir)
    private val session = PrefsSessionStore(store.prefs)

    private fun ui(block: () -> Unit) = activity.runOnUiThread { if (!activity.isDestroyed) block() }
    fun toast(text: String) = android.widget.Toast.makeText(activity, text, android.widget.Toast.LENGTH_LONG).show()
    private fun bytes(size: Long) = android.text.format.Formatter.formatFileSize(activity, size)
    private fun failure(error: Throwable) = toast(error.message ?: "Não foi possível concluir.")

    /** True quando a ação roda aqui; as demais seguem para a tela antiga. */
    fun run(game: Game, action: GameAction) {
        when (action) {
            GameAction.PLAY -> play(game)
            GameAction.QUEUE -> page = Page.Downloads
            GameAction.DOWNLOAD -> download(game)
            GameAction.STREAM -> GameLogic.remotePackage(game.platform)?.let(::openPackage)
            GameAction.SWITCH, GameAction.MOONLIGHT -> moonlight(game)
            GameAction.DUCKSTATION -> openPackage("com.github.stenzek.duckstation")
            GameAction.SAVES -> saves(game)
            GameAction.COVER -> cover(game)
            GameAction.EDIT -> edit(game)
            GameAction.REMOVE -> remove(game)
            else -> legacy(game, action)
        }
    }

    fun openPackage(pkg: String) {
        val intent = activity.packageManager.getLaunchIntentForPackage(pkg)
        if (intent == null) toast("Aplicativo não instalado: $pkg") else activity.startActivity(intent)
    }

    // --- Jogar, com o tempo jogado ---------------------------------------------------------------------------------------------
    fun play(game: Game) {
        runCatching { GameLauncher.intentFor(activity, store, game) }.onSuccess { intent ->
            PlaySession.begin(session, game.key, System.currentTimeMillis())
            store.prefs.edit().putLong("played:${game.key}", System.currentTimeMillis()).apply() // fileira Recentes do Início
            activity.startActivity(intent)
        }.onFailure(::failure)
    }
    fun onPause() = PlaySession.markLeft(session)
    fun isRunning(game: Game) = PlaySession.active(session) == game.key
    /**
     * Voltou do jogo (ou a lista de jogos acabou de chegar): envia os saves dele sem perguntar (conflito nunca é sobrescrito) e oferece registrar o tempo.
     * Se o app nasceu de novo (processo morto durante o jogo) e a lista ainda não chegou, a sessão continua guardada e é tratada na próxima chamada.
     */
    fun deliverSession() {
        val list = games()
        when (val r = PlaySession.resolve(session, System.currentTimeMillis(), list.map { it.key }.toSet(), loaded = isLoaded())) {
            is PlaySession.Resolution.Deliver -> {
                val game = list.first { it.key == r.ended.key }
                work.execute { runCatching { GameSaveSync.run(store, drive, game) }.getOrNull()?.takeIf { it.any }?.let { outcome -> ui { toast(outcome.text()) } } }
                if (r.ended.worthOffering) timePrompt = TimePrompt(game, PlaySession.clamp(r.ended.minutes))
            }
            is PlaySession.Resolution.Missing -> toast("Sessão de ${r.ended.minutes} min de um jogo que não está mais na lista; o tempo não foi registrado.")
            else -> Unit
        }
    }
    fun onResume() = deliverSession()
    fun saveTime(prompt: TimePrompt, value: Int?, thenSaves: Boolean) {
        if (!PlaySession.valid(value)) { toast("Use entre ${PlaySession.MIN} e ${PlaySession.MAX} minutos."); return }
        store.addTime(prompt.game, value!!)
        toast("Tempo salvo neste celular; envio pela nuvem agendado."); timePrompt = null; syncNow(); changed()
        if (thenSaves) saves(prompt.game)
    }

    // --- Baixar e fila ---------------------------------------------------------------------------------------------------------
    private fun askNotifications() {
        val allowed = android.os.Build.VERSION.SDK_INT < 33 || activity.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED
        val asked = store.prefs.getInt("asked-notifications-count", 0)
        if (!allowed && asked < 2) { store.prefs.edit().putInt("asked-notifications-count", asked + 1).apply(); activity.requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 30) }
    }
    private fun enqueue(game: Game) {
        runCatching { DownloadFlow.enqueue(store, game); askNotifications() }
            .onSuccess { toast("⬇ ${game.name}: baixando. O andamento aparece na fila; o jogo fica pronto em Neste celular."); changed() }
            .onFailure { error -> notice = NoticeState("Downloads", error.message ?: "Não foi possível iniciar o download.", "Abrir fila") { page = Page.Downloads } }
    }
    private fun pickFile(game: Game, title: String, labels: List<String>, link: (Int) -> Unit) { choice = ChoiceState(title, labels) { link(it); enqueue(game) } }

    /** Baixar em um toque: arquivo vinculado, ou o que o notebook tem (acervo ou Drive pelo rclone). */
    fun download(game: Game) {
        if (store.tree(game.code) == null) { legacy(game, GameAction.DOWNLOAD); return }          // escolher a pasta Jogos é um seletor do sistema
        val current = store.prefs.getString("cloud:${game.key}", null)
        if (current != null && RomSource.parse(current) == null) { enqueue(game); return }
        if (!store.online && drive.connected) { driveDirect(game); return }
        if (!game.downloadable) { if (current != null) enqueue(game) else if (drive.connected) driveDirect(game) else legacy(game, GameAction.DRIVE_SEARCH); return }
        toast("Consultando o notebook…")
        work.execute {
            val result = runCatching { RomSource.playable(store.romOptions(game)) { store.accepts(game.code, it) } }
            ui {
                result.onSuccess { options -> when (options.size) {
                    0 -> legacy(game, GameAction.DOWNLOAD)                                           // só CUE/M3U (conjunto de discos): fluxo da tela antiga
                    1 -> { DownloadFlow.linkNotebook(store, game, options[0]); enqueue(game) }
                    else -> pickFile(game, "Qual arquivo baixar?", options.map { "${it.file} · ${bytes(it.size)}" }) { DownloadFlow.linkNotebook(store, game, options[it]) }
                } }.onFailure { error ->
                    if (current != null) enqueue(game)
                    else if (drive.connected) driveDirect(game)
                    else notice = NoticeState("Notebook indisponível", "${error.message ?: "Sem resposta."}\n\nSem o notebook, escolha o arquivo no Drive: ele fica vinculado ao jogo e o download começa em seguida.", "Procurar no Drive") { legacy(game, GameAction.DRIVE_SEARCH) }
                }
            }
        }
    }
    private fun driveDirect(game: Game) {
        toast("Procurando ${game.name} no seu Drive…")
        work.execute {
            val result = runCatching { DriveSource.candidates(drive.romFiles(game.code), game.romName.ifBlank { game.name }) { store.accepts(game.code, it) } }
            ui {
                result.onSuccess { found -> when (found.size) {
                    0 -> notice = NoticeState("Não achei no Drive", "Não há em Jogos/ROMs/${game.code} um arquivo de ${game.name} que o celular abra sozinho (PS1 precisa de CHD ou PBP). Escolha o arquivo manualmente.", "Escolher no Drive") { legacy(game, GameAction.DRIVE_SEARCH) }
                    1 -> { DownloadFlow.linkDrive(store, game, found[0]); enqueue(game) }
                    else -> pickFile(game, "Qual arquivo baixar?", found.map { "${it.name} · ${bytes(it.size)}" }) { DownloadFlow.linkDrive(store, game, found[it]) }
                } }.onFailure { error -> if (error is GoogleConsentNeeded) legacy(game, GameAction.DOWNLOAD) else failure(error) }   // consentimento é uma tela do Google
            }
        }
    }

    // --- Jogar no notebook (Moonlight) ------------------------------------------------------------------------------------------
    private fun moonlight(game: Game) {
        notice = NoticeState("Jogar no notebook", "Iniciar o jogo no notebook e abrir o Moonlight? Você escolhe o computador no Moonlight. Essa opção precisa de conexão; os jogos locais continuam offline.",
            "Iniciar e abrir", "Voltar", "Só Moonlight", { openPackage("com.limelight") }) {
            toast("Conferindo jogo no notebook…")
            work.execute {
                val result = runCatching { DownloadFlow.startOnNotebook(store, game) }
                ui { result.onSuccess { toast("Pedido enviado ao notebook."); openPackage("com.limelight") }.onFailure(::failure) }
            }
        }
    }

    // --- Remover ROM (mesma prévia e mesmo texto da tela antiga; nada some sem confirmação) --------------------------------------
    fun remove(game: Game) {
        choice = ChoiceState("Remover ROM: ${game.name}", listOf("Só deste celular", "Só do Drive (lixeira)", "Dos dois")) { which -> removalPreview(game, listOf("local", "drive", "both")[which]) }
    }
    private fun removalPreview(game: Game, scope: String) {
        toast("Conferindo arquivos exclusivos e proteções…")
        work.execute {
            val result = runCatching { RomRemoval(store).plan(game, scope, isRunning(game)) }
            ui { result.onFailure(::failure).onSuccess { plan ->
                val description = listOf("Feche os emuladores. Saves, estados, capa, texturas, cadastro e progresso ficam.",
                    "Celular (${plan.local.size}):\n" + plan.local.joinToString("\n") { "• ${it.path}" },
                    "Drive (${plan.drive.size}):\n" + plan.drive.joinToString("\n") { "• ${it.path}" },
                    if (plan.preserved.isEmpty()) "" else "Compartilhados preservados: ${plan.preserved.joinToString()}",
                    plan.warnings.joinToString("\n"), plan.blocked.joinToString("\n"),
                    "Celular: lixeira recuperável em Opções. Drive: lixeira do Google.").filter { it.isNotBlank() }.joinToString("\n\n")
                val allowed = plan.blocked.isEmpty() && (plan.local.isNotEmpty() || plan.drive.isNotEmpty())
                notice = NoticeState("Prévia: ${game.name}", description, plan.confirmation.takeIf { allowed }, "Manter") {
                    toast("Revalidando a prévia e removendo…")
                    work.execute {
                        val done = runCatching { RomRemoval(store).apply(game, plan, isRunning(game)) }
                        ui { done.onSuccess { rows ->
                            val failures = rows.filter { it.second.isFailure }
                            toast("${rows.size - failures.size} arquivo(s) para a lixeira. " + if (failures.isEmpty()) "Versões recuperáveis; saves preservados." else failures.joinToString { "${it.first}: ${it.second.exceptionOrNull()?.message}" })
                            changed()
                        }.onFailure(::failure) }
                    }
                }
            } }
        }
    }

    // --- Saves, capa, editar ---------------------------------------------------------------------------------------------------
    fun saves(game: Game) {
        val sync = FileSync(store); val retro = game.code != "PSP" && game.code != "3DS"
        val wrong = sync.retroarchTree()?.let { SaveRules.retroarchFolderProblem(android.provider.DocumentsContract.getTreeDocumentId(it)) }
        // PSP/3DS pedem o ID do título e a pasta RetroArch, um seletor: ficam na tela antiga.
        if (!retro || sync.tree("retro-saves") == null || wrong != null) { legacy(game, GameAction.SAVES); return }
        page = Page.Saves(game)
    }
    fun cover(game: Game) {
        val target = ExtrasRules.coverTarget(game.id, game.cover) ?: return
        if (!store.online) { toast("Esta função precisa do notebook online. Ligue o Tailscale e tente de novo."); return }
        page = Page.Cover(game, target)
    }
    fun edit(game: Game) {
        if (!store.cloudLibrary.available() && !store.online) { toast("Esta função precisa do notebook online. Ligue o Tailscale e tente de novo."); return }
        page = Page.Edit(game)
    }

    // modelos das páginas (a tela só desenha) ----------------------------------------------------------------------------------
    fun savesModel(game: Game) = SavesModel(this, game)
    fun coverModel(game: Game, target: CoverTarget) = CoverModel(this, game, target)
    fun editModel(game: Game) = EditModel(this, game)
    internal fun workExecute(block: () -> Unit) = work.execute(block)
    internal fun runUi(block: () -> Unit) = ui(block)
    internal fun phone() = runCatching { CloudPhone(store, FileSync(store), DriveCloudStorage(drive)) }
    internal fun notifyChanged() = changed()
    internal fun toastText(text: String) = toast(text)
}

/** Saves de um jogo pela nuvem: compara, sincroniza o que é seguro e deixa os conflitos para o usuário decidir. */
class SavesModel(private val flows: GameFlows, val game: Game) {
    var info by mutableStateOf("Comparando com o Drive…")
    var result by mutableStateOf<Map<String, Result<List<CloudItem>>>>(emptyMap())
    var busy by mutableStateOf(false)
    var showAll by mutableStateOf(false)
    var confirm by mutableStateOf<NoticeState?>(null)
    private var phone: Result<CloudPhone>? = null
    private var filter: ((String, String) -> Boolean)? = null

    fun load() {
        busy = true
        flows.workExecute {
            val store = flows.store
            val label = SaveRules.label(game.localUri?.let { runCatching { store.displayName(it) }.getOrNull() } ?: game.romName.substringAfterLast('/').ifBlank { game.name }, store.extensionsFor(game.code))
            val mine: (String, String) -> Boolean = { g, path -> g in setOf("retro-saves", "retro-states") && SaveRules.belongs(path, game.code, label) }
            val p = flows.phone(); val analysis = p.mapCatching { it.analyze(mine, showAll) }
            flows.runUi {
                phone = p; filter = mine; busy = false
                val res = analysis.getOrElse { info = "Não foi possível comparar: ${it.message}"; return@runUi }
                if (res.isEmpty()) { info = "Escolha as pastas de saves em Situação (pasta RetroArch, PPSSPP, 3DS)."; return@runUi }
                result = res
                val counts = res.values.mapNotNull { it.getOrNull() }.flatten().groupingBy { it.action }.eachCount()
                val failed = res.filterValues { it.isFailure }
                info = if (counts.isEmpty() && failed.isEmpty()) "Tudo em dia com a nuvem." else
                    "Enviar: ${counts["push"] ?: 0} · Baixar: ${counts["pull"] ?: 0} · Guardar no histórico: ${counts["forget"] ?: 0} · Conflitos: ${counts["conflict"] ?: 0}" +
                        if (failed.isEmpty()) "" else "\nErro em: ${failed.map { "${it.key}: ${it.value.exceptionOrNull()?.message}" }.joinToString()}"
            }
        }
    }
    val pending get() = result.values.mapNotNull { it.getOrNull() }.flatten().count { it.action in setOf("push", "pull", "forget") }
    val conflicts get() = result.flatMap { (g, r) -> r.getOrNull().orEmpty().filter { it.action == "conflict" }.map { g to it } }
    val forgettable get() = result.flatMap { (g, r) -> r.getOrNull().orEmpty().filter { it.action != "forget" }.map { g to it } }

    private fun perform(action: () -> CloudFeedback) {
        if (busy) return
        busy = true; info = "Conferindo e aplicando…"
        flows.workExecute {
            val feedback = action()
            flows.runUi { busy = false; info = feedback.message; if (feedback.complete) { flows.toastText(feedback.message); flows.notifyChanged(); load() } }
        }
    }
    fun syncAll() { val p = phone?.getOrNull() ?: return; perform { CloudFeedback.batch { p.apply(filter = filter) } } }
    fun keepLocal(group: String, item: CloudItem) { val p = phone?.getOrNull() ?: return; perform { CloudFeedback.resolve("Mantido o do celular: ${item.path}") { p.resolve(group, item.path, "local") } } }
    fun useRemote(group: String, item: CloudItem, sha: String) {
        val p = phone?.getOrNull() ?: return
        val deleted = sha in item.deletedHeads
        confirm = NoticeState(item.path, if (deleted) "Guardar a cópia local no histórico e aceitar a exclusão explícita deste save?" else "Usar esta versão da nuvem? A versão local fica no histórico.", "Confirmar", "Manter") {
            perform { CloudFeedback.resolve("Versão escolhida: ${item.path}") { p.resolve(group, item.path, "remote", sha) } }
        }
    }
    fun forget(group: String, item: CloudItem) {
        val p = phone?.getOrNull() ?: return
        confirm = NoticeState("Esquecer este save: ${item.path}", "Retirar somente este save do uso e impedir que os outros aparelhos restaurem a versão antiga? Cópias locais vão para o histórico na próxima sincronização; blobs antigos permanecem. Saves de outros jogos ficam.", "Esquecer este save", "Manter") {
            perform { CloudFeedback.resolve("Save esquecido com histórico: ${item.path}") { p.forget(group, item) } }
        }
    }
    fun toggleAll() { showAll = !showAll; load() }
}

/** Trocar capa: busca no SteamGridDB (só a busca mais recente desenha) e aplica depois de confirmar. */
class CoverModel(private val flows: GameFlows, val game: Game, private val target: CoverTarget) {
    var query by mutableStateOf(game.name)
    var status by mutableStateOf("")
    var results by mutableStateOf<List<Pair<String, String>>>(emptyList())
    val thumbs = mutableStateMapOf<String, ImageBitmap>()
    var confirm by mutableStateOf<NoticeState?>(null)
    private val searches = LatestRequest()

    fun search() {
        val term = query.trim(); if (term.length < 2) return
        val current = searches.start(); status = "Buscando… o SteamGridDB pode levar até dois minutos."; results = emptyList(); thumbs.clear()
        flows.workExecute {
            val found = runCatching { flows.extras.searchCovers(term) }
            flows.runUi {
                if (!searches.isCurrent(current)) return@runUi
                found.onFailure { status = it.message ?: "Busca falhou." }.onSuccess { list ->
                    status = if (list.isEmpty()) "Nada encontrado. Troque o termo." else "Escolha uma capa para usar."
                    results = list.take(12)
                    results.forEach { (url, _) -> flows.workExecute {
                        if (searches.isCurrent(current)) { val bitmap: Bitmap? = runCatching { flows.extras.thumbnail(url) }.getOrNull(); if (bitmap != null) flows.runUi { if (searches.isCurrent(current)) thumbs[url] = bitmap.asImageBitmap() } }
                    } }
                }
            }
        }
    }
    fun choose(url: String) {
        confirm = NoticeState(game.name, "Usar esta capa para ${game.name}? A capa atual no notebook é substituída.", "Usar capa", "Voltar") {
            status = "Aplicando a capa…"
            flows.workExecute {
                val done = runCatching { flows.extras.applyCover(target, url) }
                if (done.isSuccess) runCatching { flows.store.refresh() }
                flows.runUi { status = done.fold({ "Capa trocada." }, { it.message ?: "Não foi possível trocar a capa." }); if (done.isSuccess) flows.notifyChanged() }
            }
        }
    }
}

/** Editar dados do jogo na Biblioteca (gênero, datas, tempo, comentário, sinopse); só grava o que mudou. */
class EditModel(private val flows: GameFlows, val game: Game) {
    val fields = listOf("genero" to "Gênero", "data_final" to "Data que finalizou (aaaa-mm-dd)", "tempo" to "Tempo jogado (ex.: 31:40:00)", "observacoes" to "Comentário", "sinopse" to "Sinopse (resumo do jogo)")
    var loaded by mutableStateOf(false)
    var message by mutableStateOf("Lendo os dados de ${game.name}…")
    var genres by mutableStateOf<List<String>>(emptyList())
    val values = mutableStateMapOf<String, String>()
    private var before = emptyMap<String, String>()

    fun load() {
        flows.workExecute {
            val result = runCatching { flows.extras.record(game.id) to flows.extras.genres() }
            flows.runUi {
                result.onFailure { message = it.message ?: "Não foi possível ler." }.onSuccess { (record, list) ->
                    if (record == null) { message = "Este jogo não está mais na Biblioteca do notebook."; return@onSuccess }
                    before = fields.associate { (f, _) -> f to (record.optString(f).takeUnless { record.isNull(f) } ?: "") }
                    genres = (listOf("") + list + listOf(before.getValue("genero"))).distinct()
                    values.putAll(before); loaded = true; message = ""
                }
            }
        }
    }
    fun save(done: () -> Unit) {
        val after = fields.associate { (f, _) -> f to (values[f] ?: "") }
        val changes = ExtrasRules.changes(before, after)
        if (changes.isEmpty()) { message = "Nada alterado."; return }
        flows.workExecute {
            val result = runCatching { flows.extras.edit(game.id, changes) }
            flows.runUi {
                result.onFailure { message = it.message ?: "Não foi possível salvar." }.onSuccess { flows.toastText("Dados de ${game.name} salvos; envio pela nuvem agendado."); flows.notifyChanged(); done() }
            }
        }
    }
}
