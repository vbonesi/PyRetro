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
/** Trabalho do usuário em andamento: fica na tela até a prévia, o erro ou o fim (não é um toast que some). */
class BusyState(val text: String, val cancelable: Boolean = true)

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
    private val games: () -> List<Game>, private val isLoaded: () -> Boolean, private val changed: () -> Unit, private val syncNow: () -> Unit,
    private val pick: (android.content.Intent, (Int, android.content.Intent?) -> Unit) -> Unit,
    private val pickSender: (android.content.IntentSender, (Int, android.content.Intent?) -> Unit) -> Unit,
    private val legacy: (Game, GameAction) -> Unit) {
    var notice by mutableStateOf<NoticeState?>(null)
    var choice by mutableStateOf<ChoiceState?>(null)
    var timePrompt by mutableStateOf<TimePrompt?>(null)
    var page by mutableStateOf<Page?>(null)
    var busy by mutableStateOf<BusyState?>(null)
    private var busyToken = 0
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())
    val extras = NotebookExtras(store, activity.filesDir)
    private val session = PrefsSessionStore(store.prefs)

    private fun log(text: String) { android.util.Log.i("PyRetro", text) }

    /**
     * Roda [job] fora da thread principal (no executor das ações do usuário, que nunca espera sincronização) com um aviso na tela até terminar.
     * Passado [timeoutMs] (0 = sem prazo), o aviso some e o usuário recebe "Demorou demais" com [retry]; o resultado tardio é descartado.
     */
    private fun <T> withBusy(text: String, retry: (() -> Unit)? = null, timeoutMs: Long = 30_000, cancelable: Boolean = true, job: () -> T, done: (Result<T>) -> Unit) {
        val token = ++busyToken; val started = System.currentTimeMillis()
        busy = BusyState(text, cancelable); log("início: $text")
        if (timeoutMs > 0) handler.postDelayed({
            if (busyToken == token) {
                busyToken++; busy = null; log("prazo vencido (${timeoutMs / 1000} s): $text")
                notice = NoticeState("Demorou demais", "\"$text\" passou de ${timeoutMs / 1000} s sem resposta (o Drive ou o notebook podem estar lentos).", retry?.let { "Tentar de novo" }, "Voltar", onConfirm = retry)
            }
        }, timeoutMs)
        work.execute {
            val result = runCatching(job)
            ui {
                if (busyToken == token) { busyToken++; busy = null; log("fim (${System.currentTimeMillis() - started} ms, ${if (result.isSuccess) "ok" else "erro: ${result.exceptionOrNull()?.message}"}): $text"); done(result) }
                else log("resultado tardio descartado: $text")
            }
        }
    }
    fun cancelBusy() { busyToken++; busy = null }
    private fun ui(block: () -> Unit) = activity.runOnUiThread { if (!activity.isDestroyed) block() }
    fun toast(text: String) = android.widget.Toast.makeText(activity, text, android.widget.Toast.LENGTH_LONG).show()
    private fun bytes(size: Long) = android.text.format.Formatter.formatFileSize(activity, size)
    private fun failure(error: Throwable) = toast(error.message ?: "Não foi possível concluir.")

    /** True quando a ação roda aqui; as demais seguem para a tela antiga. */
    fun run(game: Game, action: GameAction) {
        log("ação ${action.id}: ${game.key}")
        when (action) {
            GameAction.PLAY -> play(game)
            GameAction.QUEUE -> page = Page.Downloads
            GameAction.DOWNLOAD -> download(game)
            GameAction.STREAM -> GameLogic.remotePackage(game.platform)?.let(::openPackage)
            GameAction.MOONLIGHT -> moonlight(game)
            GameAction.DUCKSTATION -> openPackage("com.github.stenzek.duckstation")
            GameAction.SAVES -> saves(game)
            GameAction.COVER -> cover(game)
            GameAction.EDIT -> edit(game)
            GameAction.REMOVE -> remove(game)
            GameAction.OTHER_ROM -> pickRom(game, false)
            GameAction.DRIVE_SEARCH, GameAction.DRIVE_PICK -> driveSearch(game)
            GameAction.ADD_LIBRARY -> addToLibrary(game)
            else -> legacy(game, action)               // Texturas HD e saves de PSP/3DS (A5)
        }
    }

    fun openPackage(pkg: String) {
        val intent = activity.packageManager.getLaunchIntentForPackage(pkg)
        if (intent == null) toast("Aplicativo não instalado: $pkg") else activity.startActivity(intent)
    }

    // --- Jogar, com o tempo jogado ---------------------------------------------------------------------------------------------
    fun play(game: Game) {
        log("jogar: ${game.key}")
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
                log("sessão entregue: ${r.ended.key} ${r.ended.minutes} min")
                val game = list.first { it.key == r.ended.key }
                work.execute { runCatching { GameSaveSync.run(store, drive, game) }.getOrNull()?.takeIf { it.any }?.let { outcome -> ui { toast(outcome.text()) } } }
                if (r.ended.worthOffering) timePrompt = TimePrompt(game, PlaySession.clamp(r.ended.minutes))
            }
            is PlaySession.Resolution.Missing -> { log("sessão de jogo ausente: ${r.ended.key}"); toast("Sessão de ${r.ended.minutes} min de um jogo que não está mais na lista; o tempo não foi registrado.") }
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
        if (store.tree(game.code) == null) { toast("Escolha a pasta Jogos do celular; cada sistema fica em Jogos/<sistema>."); pickFolder("ROOT", game); return }
        val current = store.prefs.getString("cloud:${game.key}", null)
        if (current != null && RomSource.parse(current) == null) { enqueue(game); return }
        if (!store.online && drive.connected) { driveDirect(game); return }
        if (!game.downloadable) { if (current != null) enqueue(game) else if (drive.connected) driveDirect(game) else driveSearch(game); return }
        withBusy("Consultando o notebook…", retry = { download(game) }, job = { RomSource.playable(store.romOptions(game)) { store.accepts(game.code, it) } }) { result ->
            run {
                result.onSuccess { options -> when (options.size) {
                    0 -> offerBundle(game)                                                             // só CUE/M3U: oferece o conjunto de discos
                    1 -> { DownloadFlow.linkNotebook(store, game, options[0]); enqueue(game) }
                    else -> pickFile(game, "Qual arquivo baixar?", options.map { "${it.file} · ${bytes(it.size)}" }) { DownloadFlow.linkNotebook(store, game, options[it]) }
                } }.onFailure { error ->
                    if (current != null) enqueue(game)
                    else if (drive.connected) driveDirect(game)
                    else notice = NoticeState("Notebook indisponível", "${error.message ?: "Sem resposta."}\n\nSem o notebook, escolha o arquivo no Drive: ele fica vinculado ao jogo e o download começa em seguida.", "Procurar no Drive") { driveSearch(game) }
                }
            }
        }
    }
    private fun driveDirect(game: Game) {
        withBusy("Procurando ${game.name} no seu Drive…", retry = { driveDirect(game) }, job = { DriveSource.candidates(drive.romFiles(game.code), game.romName.ifBlank { game.name }) { store.accepts(game.code, it) } }) { result ->
            run {
                result.onSuccess { found -> when (found.size) {
                    0 -> notice = NoticeState("Não achei no Drive", "Não há em Jogos/ROMs/${game.code} um arquivo de ${game.name} que o celular abra sozinho (PS1 precisa de CHD ou PBP). Escolha o arquivo manualmente.", "Escolher no Drive") { driveSearch(game) }
                    1 -> { DownloadFlow.linkDrive(store, game, found[0]); enqueue(game) }
                    else -> pickFile(game, "Qual arquivo baixar?", found.map { "${it.name} · ${bytes(it.size)}" }) { DownloadFlow.linkDrive(store, game, found[it]) }
                } }.onFailure { error -> if (error is GoogleConsentNeeded) connectGoogle(game) else failure(error) }
            }
        }
    }

    // --- Jogar no notebook (Moonlight) ------------------------------------------------------------------------------------------
    private fun moonlight(game: Game) {
        notice = NoticeState("Jogar no notebook", "Iniciar o jogo no notebook e abrir o Moonlight? Você escolhe o computador no Moonlight. Essa opção precisa de conexão; os jogos locais continuam offline.",
            "Iniciar e abrir", "Voltar", "Só Moonlight", { openPackage("com.limelight") }) {
            withBusy("Conferindo jogo no notebook…", job = { DownloadFlow.startOnNotebook(store, game) }) { result ->
                result.onSuccess { toast("Pedido enviado ao notebook."); openPackage("com.limelight") }.onFailure(::failure)
            }
        }
    }

    // --- Remover ROM (mesma prévia e mesmo texto da tela antiga; nada some sem confirmação) --------------------------------------
    fun remove(game: Game) {
        choice = ChoiceState("Remover ROM: ${game.name}", listOf("Só deste celular", "Só do Drive (lixeira)", "Dos dois")) { which -> removalPreview(game, listOf("local", "drive", "both")[which]) }
    }
    /** Chamado na thread de UI depois de uma remoção que tirou o arquivo do celular: atualiza a lista na hora. */
    var onRemovedLocally: (String) -> Unit = {}
    private fun removalPreview(game: Game, scope: String) {
        withBusy("Conferindo arquivos exclusivos e proteções…", retry = { removalPreview(game, scope) }, job = { RomRemoval(store).plan(game, scope, isRunning(game)) }) { result ->
            run { result.onFailure { notice = NoticeState("Não foi possível conferir", it.message ?: "Falha ao montar a prévia.", "Tentar de novo", "Voltar") { removalPreview(game, scope) } }.onSuccess { plan ->
                val description = listOf("Feche os emuladores. Saves, estados, capa, texturas, cadastro e progresso ficam.",
                    "Celular (${plan.local.size}):\n" + plan.local.joinToString("\n") { "• ${it.path}" },
                    "Drive (${plan.drive.size}):\n" + plan.drive.joinToString("\n") { "• ${it.path}" },
                    if (plan.preserved.isEmpty()) "" else "Compartilhados preservados: ${plan.preserved.joinToString()}",
                    plan.warnings.joinToString("\n"), plan.blocked.joinToString("\n"),
                    "Celular: lixeira recuperável em Opções. Drive: lixeira do Google.").filter { it.isNotBlank() }.joinToString("\n\n")
                val allowed = plan.blocked.isEmpty() && (plan.local.isNotEmpty() || plan.drive.isNotEmpty())
                notice = NoticeState("Prévia: ${game.name}", description, plan.confirmation.takeIf { allowed }, "Manter") {
                    // Remoção não tem prazo nem cancelamento: revalida a prévia e só então move para a lixeira.
                    withBusy("Revalidando a prévia e removendo…", timeoutMs = 0, cancelable = false, job = { RomRemoval(store).apply(game, plan, isRunning(game)) }) { done ->
                        done.onSuccess { rows ->
                            val failures = rows.filter { it.second.isFailure }
                            notice = NoticeState("Remoção", "${rows.size - failures.size} arquivo(s) para a lixeira. " + if (failures.isEmpty()) "Versões recuperáveis; saves preservados." else failures.joinToString { "${it.first}: ${it.second.exceptionOrNull()?.message}" })
                            if (scope != "drive" && plan.local.isNotEmpty() && failures.isEmpty()) onRemovedLocally(game.key)
                            changed()
                        }.onFailure { notice = NoticeState("Remoção", it.message ?: "Não foi possível remover.") }
                    }
                }
            } }
        }
    }

    // --- Saves, capa, editar ---------------------------------------------------------------------------------------------------
    fun saves(game: Game) {
        val sync = FileSync(store); val retro = game.code != "PSP" && game.code != "3DS"
        val wrong = sync.retroarchTree()?.let { SaveRules.retroarchFolderProblem(android.provider.DocumentsContract.getTreeDocumentId(it)) }
        if (!retro) { legacy(game, GameAction.SAVES); return }                  // PSP/3DS pedem o ID do título (A5)
        if (sync.tree("retro-saves") == null || wrong != null) {
            notice = NoticeState("Saves de ${game.name}", (wrong?.let { "$it\n\n" } ?: "") + "Escolha uma vez a pasta RetroArch do celular (a raiz, normalmente RetroArch no armazenamento interno; não entre em saves nem states).", "Escolher pasta") { pickSyncFolder("retroarch") }
            return
        }
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

    // --- Seletores do sistema (pasta, ROM) e conta Google, agora na casca ---------------------------------------------------------
    private val treeFlags = android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION or android.content.Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
    private fun persist(uri: android.net.Uri, write: Boolean) {
        runCatching { activity.contentResolver.takePersistableUriPermission(uri, if (write) android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION else android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION) }
            .onFailure { toast("Permissão temporária: pode ser necessário selecionar o arquivo novamente após reiniciar.") }
    }
    /** Pasta Jogos (cada sistema em Jogos/<sistema>); [after] é o jogo que esperava a pasta para baixar. */
    fun pickFolder(code: String, after: Game? = null) {
        pick(android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(treeFlags)) { result, data ->
            val uri = data?.data
            if (result == android.app.Activity.RESULT_OK && uri != null) {
                persist(uri, data.flags and android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION != 0)
                store.saveTree(code, uri); changed(); after?.let { download(it) }
            }
        }
    }
    /** Pasta RetroArch (saves e estados por sistema); precisa de leitura e escrita. */
    fun pickSyncFolder(group: String) {
        val intent = android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(treeFlags)
            .putExtra(android.provider.DocumentsContract.EXTRA_INITIAL_URI, android.provider.DocumentsContract.buildDocumentUri("com.android.externalstorage.documents", "primary:RetroArch"))
        pick(intent) { result, data ->
            val uri = data?.data
            if (result == android.app.Activity.RESULT_OK && uri != null) runCatching {
                require(data.flags and android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION != 0) { "A pasta precisa permitir leitura e escrita." }
                activity.contentResolver.takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                FileSync(store).setTree(group, uri); toast("Pasta de sincronização definida."); changed()
            }.onFailure(::failure)
        }
    }
    /** Outra ROM do celular ([cloud] false) ou arquivo do Drive ([cloud] true: vincula e baixa). */
    fun pickRom(game: Game, cloud: Boolean) {
        val intent = android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(android.content.Intent.CATEGORY_OPENABLE)
            .addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        pick(intent) { result, data ->
            val uri = data?.data ?: return@pick
            if (result != android.app.Activity.RESULT_OK) return@pick
            persist(uri, false)
            val name = store.displayName(uri)
            if (!cloud && uri.authority != "com.android.externalstorage.documents") { toast("Escolha uma ROM no armazenamento local. Para o Drive, use Escolher o arquivo no Drive."); return@pick }
            if (!store.accepts(game.code, name)) { toast("Esse formato não corresponde a ${game.code}."); return@pick }
            if (cloud) {
                if (name.substringAfterLast('.').lowercase() in setOf("cue", "m3u")) { toast("CUE/M3U dependem de outros arquivos. Escolha CHD ou PBP."); return@pick }
                // Escolher no Drive já é a decisão: vincula ao jogo e começa o download.
                store.prefs.edit().putString("cloud:${game.key}", uri.toString()).remove("cloud-auto:${game.code}:${game.key}").apply()
                download(game); return@pick
            }
            notice = NoticeState("Usar esta ROM", "Usar $name para ${game.name}?", "Usar", "Cancelar") {
                store.prefs.edit().putString("rom:${game.key}", uri.toString()).apply(); game.localUri = uri; changed()
            }
        }
    }
    fun driveSearch(game: Game) {
        val formats = store.extensionsFor(game.code).filter { it !in setOf("cue", "m3u") }.sorted().joinToString(", ")
        notice = NoticeState("Escolher no Drive", "No seletor, abra o Google Drive e escolha:\nJogos/ROMs/${game.code}/${game.romName.ifBlank { game.name }}\n\nFormatos: $formats. O arquivo fica vinculado a ${game.name} e o download começa em seguida.", "Abrir seletor") { pickRom(game, true) }
    }
    fun connectGoogle(after: Game? = null) {
        toast("Abrindo a conta Google…")
        drive.authorize().addOnSuccessListener { result ->
            if (result.hasResolution()) runCatching {
                pickSender(result.pendingIntent!!.intentSender) { code, data ->
                    if (code != android.app.Activity.RESULT_OK) toast("Conta Google não conectada.")
                    else runCatching { drive.resultFromIntent(data) }.onSuccess { googleConnected(after) }.onFailure(::failure)
                }
            }.onFailure(::failure) else googleConnected(after)
        }.addOnFailureListener { error -> failure(IllegalStateException("O Google recusou a conexão: ${error.message}. Confira se esta conta está entre os usuários de teste do projeto PyRetro no Google Cloud.", error)) }
    }
    private fun googleConnected(after: Game?) {
        withBusy("Conectando a conta Google…", retry = { googleConnected(after) }, job = { drive.account() }) { result ->
            result.onSuccess { email -> toast("Conta Google conectada: $email."); changed(); after?.let { driveDirect(it) } }.onFailure(::failure)
        }
    }
    fun disconnectGoogle() { drive.disconnect(); toast("Conta Google desconectada deste app. Para revogar o acesso, use myaccount.google.com → Segurança."); changed() }

    /** Sem arquivo único: se o notebook tem um CUE/M3U que o sistema abre, oferece o conjunto inteiro. */
    private fun offerBundle(game: Game) {
        withBusy("Conferindo o conjunto de discos no notebook…", retry = { offerBundle(game) }, timeoutMs = 60_000, job = {
            val entries = store.romOptions(game).filter { BundleRules.isDescriptor(it.file) && store.accepts(game.code, it.file.substringAfterLast('/')) }
                .sortedBy { if (it.file.endsWith(".m3u", true)) 0 else 1 } // M3U (todos os discos) antes do CUE de um disco só
            entries.map { option -> val (id, members) = BundleStore(store, SafStorage(store)).manifest(game.code, option.file); Triple(option.file, id, members) }
        }) { result ->
            run {
                val bundles = result.getOrElse { emptyList() }
                if (bundles.isEmpty()) {
                    notice = NoticeState("Formato que o celular não abre", "O notebook tem ${game.name}, mas nem num arquivo único que o celular abra nem num CUE/M3U completo (${result.exceptionOrNull()?.message ?: "PS1 precisa de CHD, PBP ou CUE com todas as faixas"}). Converta no PC ou escolha outro arquivo no Drive.", "Escolher no Drive") { driveSearch(game) }
                    return@run
                }
                choice = ChoiceState("Baixar o conjunto de discos", bundles.map { (entry, _, members) -> "${entry.substringAfterLast('/')} · ${members.size} arquivos · ${bytes(members.sumOf { it.size })}" }) { which ->
                    val (entry, id, members) = bundles[which]
                    store.prefs.edit().putString("cloud:${game.key}", BundleRef(game.code, entry, id, members.sumOf { it.size }).encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
                    enqueue(game)
                }
            }
        }
    }

    fun addToLibrary(game: Game) {
        val name = GameLogic.fileLabel(game.romName.substringAfterLast('/').ifBlank { game.name })
        withBusy("Cadastrando ${game.name} na Biblioteca…", retry = { addToLibrary(game) }, job = { val response = store.cloudLibrary.register(game, name); response to store.cached() }) { result ->
            run {
                result.onSuccess { (response, fresh) ->
                    val id = response.getString("id"); val registered = fresh.firstOrNull { it.id == id }
                    if (registered != null && registered.key != game.key) runCatching { store.migrateKeys(mapOf(game.key to registered.key)) }
                    if (game.localUri != null) registered?.let { store.prefs.edit().putString("rom:${it.key}", game.localUri.toString()).apply() }
                    toast(if (response.optBoolean("created")) "${game.name} entrou na Biblioteca." else "${game.name} já estava na Biblioteca; agora está ligado a este arquivo.")
                    changed()
                }.onFailure(::failure)
            }
        }
    }

    // --- Opções, Estatísticas ---------------------------------------------------------------------------------------------------
    fun saveServer(address: String) {
        runCatching { store.setBase(address) }.onFailure { failure(it); return }
        AppSync.probe(store, force = true) { ui { changed() } }; toast("Endereço salvo."); changed()
    }
    fun refreshCatalog() {
        withBusy("Atualizando Biblioteca e catálogo…", retry = { refreshCatalog() }, timeoutMs = 120_000, job = { store.refresh() }) { r ->
            r.onSuccess { toast("Catálogo atualizado. As capas são guardadas conforme você navega."); changed() }.onFailure(::failure)
        }
    }
    fun notificationSettings() = runCatching { activity.startActivity(android.content.Intent(android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE, activity.packageName)) }.onFailure(::failure)
    fun notificationsAllowed() = android.os.Build.VERSION.SDK_INT < 33 || activity.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED

    /** Estatísticas da Biblioteca (vêm do notebook; ficam guardadas para ver offline). */
    fun showStats() {
        withBusy("Consultando as estatísticas…", retry = { showStats() }, job = {
            val online = store.online
            val fresh = if (online) runCatching { extras.stats(true) }.getOrNull() else null
            val stats = fresh ?: extras.stats(false)
            val wish = (if (online) runCatching { extras.wishlist(true).size }.getOrNull() else null) ?: extras.wishlist(false).size
            Triple(fresh, stats, wish)
        }) { result ->
            run {
                val (fresh, stats, wish) = result.getOrElse { Triple(null, null, 0) }
                val at = store.prefs.getLong("stats-at", 0)
                notice = if (stats == null) NoticeState("📊 Estatísticas", "As estatísticas vêm do notebook. Conecte uma vez e elas ficam guardadas para ver offline.")
                else {
                    val media = if (stats.isNull("nota_media")) "—" else "%.2f".format(java.util.Locale("pt", "BR"), stats.getDouble("nota_media"))
                    NoticeState("📊 Estatísticas", listOf("🎮 ${stats.getInt("total")} jogos na Biblioteca", "▶ ${stats.getInt("jogando")} jogando agora", "✓ ${stats.getInt("zerados")} finalizados · 🏆 ${stats.getInt("platinados")} platinados",
                        "★ nota média $media · ${stats.getInt("com_nota")} com nota", "◷ ${ExtrasRules.hours(stats.getDouble("tempo_total_horas"))} de jogo registrado", "♡ $wish nos Desejados",
                        if (fresh != null) "" else "Offline · dados de ${if (at > 0) java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault()).format(java.util.Date(at)) else "—"}.").filter { it.isNotBlank() }.joinToString("\n"))
                }
            }
        }
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
