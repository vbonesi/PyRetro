package com.pyretro.app

import android.app.Activity
import android.app.AlertDialog
import android.content.ClipData
import android.content.ComponentName
import android.content.Intent
import android.content.pm.ActivityInfo
import android.hardware.input.InputManager
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Rect
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.ConnectivityManager
import android.net.Network
import android.net.Uri
import android.os.Bundle
import android.os.Build
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.Gravity
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowInsets
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.widget.*
import android.text.Editable
import android.text.TextWatcher
import org.json.JSONObject
import org.json.JSONArray
import java.util.concurrent.Executors

/** Telas da versão anterior que ainda não foram redesenhadas (A5); a casca em Compose (ShellActivity) as abre por EXTRA_SCREEN/EXTRA_ACTION. Fecha sozinha ao terminar. */
class MainActivity:Activity() {
    companion object {
        const val EXTRA_GAME="game"
        const val EXTRA_ACTION="action"
        const val EXTRA_SCREEN="screen"
        /** A instrumentação mantém a activity aberta para montar a tela sozinha. */
        @Volatile var keepOpen=false
    }
    private lateinit var store:LibraryStore
    private val extras by lazy { NotebookExtras(store,filesDir) }
    private val drive by lazy { GoogleDrive(this,store.prefs) }
    private var saveStorageOverride:CloudStorage?=null
    private fun saveStorage():CloudStorage=saveStorageOverride ?: DriveCloudStorage(drive)
    private var glyphFamily="generic"
    private val work=Executors.newSingleThreadExecutor()
    private val images=Executors.newFixedThreadPool(2)
    private var catalog=emptyList<Game>()
    private var games=emptyList<Game>()
    private var localProblems=emptyList<String>()
    private var localScanAt=0L
    private var updateLocalStatus:(()->Unit)?=null
    private var updateQueueStatus:(()->Unit)?=null
    private val queueHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private fun queue()=DownloadQueue.get(store)
    private fun bytesLabel(value:Long)=android.text.format.Formatter.formatFileSize(this,value)
    /** Saves/estados do RetroArch no celular por sistema (nomes de arquivo), lidos junto com as pastas. */
    private var saveNames:Map<String,List<String>> = emptyMap()
    private var dialog:AlertDialog?=null
    private var pickingCode="NDS"
    private var syncPicking="retroarch"
    private var textureCode="PSP"
    private var textureId=""
    private var lastMotion=0L
    @Volatile private var probing=false
    private var leftTrigger=false
    private var rightTrigger=false
    private val appBackground=Color.rgb(11,18,32)
    private val appForeground=Color.rgb(237,244,253)
    private val accent=Color.rgb(129,225,202)
    private fun dp(value:Int)=(value*resources.displayMetrics.density).toInt()
    private fun shape(selected:Boolean=false,focused:Boolean=false)=GradientDrawable().apply { cornerRadius=dp(12).toFloat();setColor(if(selected)Color.rgb(35,94,87) else Color.rgb(26,43,63));setStroke(dp(if(focused)3 else if(selected)2 else 1),if(focused)Color.WHITE else if(selected)accent else Color.rgb(60,81,102)) }
    /** Selo colorido da plataforma, igual ao da web e do modo TV; decorativo (o nome vem escrito ao lado). */
    private fun platformChip(vararg names:String?):TextView {
        val info=PlatformRules.find(*names)
        return TextView(this).apply {
            text=info.short;setTextColor(Color.WHITE);setTypeface(null,Typeface.BOLD);gravity=android.view.Gravity.CENTER
            textSize=if(info.short.length>=5)8.5f else if(info.short.length==4)9.5f else 11f;maxLines=1
            setPadding(dp(5),dp(2),dp(5),dp(2));minWidth=dp(34)
            background=android.graphics.drawable.GradientDrawable().apply { cornerRadius=dp(5).toFloat();setColor(info.color) }
            importantForAccessibility=View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
    }
    private fun text(value:CharSequence,size:Float=16f)=TextView(this).apply { text=value;textSize=size;setTextColor(appForeground);setPadding(dp(4),dp(4),dp(4),dp(4)) }
    private fun button(value:String,action:()->Unit)=Button(this).apply { text=value;isAllCaps=false;minHeight=dp(48);setTextColor(appForeground);background=shape();setPadding(dp(12),dp(6),dp(12),dp(6));setOnClickListener { action() };setOnFocusChangeListener { _,focused -> background=shape(focused=focused) } }
    private fun row()=LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL }
    private fun column()=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setPadding(dp(12),dp(8),dp(12),dp(8)) }
    private fun add(parent:LinearLayout,view:View,weight:Float=0f) { parent.addView(view,LinearLayout.LayoutParams(if(weight>0)0 else ViewGroup.LayoutParams.WRAP_CONTENT,ViewGroup.LayoutParams.WRAP_CONTENT,weight).apply { setMargins(dp(3),dp(3),dp(3),dp(3)) }) }
    private fun horizontal(parent:LinearLayout,content:LinearLayout) { parent.addView(HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled=false;addView(content) },LinearLayout.LayoutParams(-1,-2)) }
    private fun failure(error:Throwable) {
        val offline=generateSequence(error) { it.cause }.any { it is java.net.UnknownHostException || it is java.net.ConnectException || it is java.net.SocketTimeoutException }
        message(if(offline)"Sem conexão com a internet agora. Mostrando o que está salvo no celular; o app tenta de novo sozinho." else error.message ?: "Não foi possível concluir.")
    }
    private fun firstEnabledButton(view:View):Button? {
        if(view.visibility!=View.VISIBLE)return null
        if(view is Button && view.isEnabled)return view
        if(view is ViewGroup)for(index in 0 until view.childCount)firstEnabledButton(view.getChildAt(index))?.let { return it }
        return null
    }
    private fun show(builder:AlertDialog.Builder):AlertDialog {
        dialog?.dismiss();return builder.create().also { opened ->
            dialog=opened;opened.setOnDismissListener { if(dialog===opened) { dialog=null;updateLocalStatus=null;updateQueueStatus=null;maybeFinish() } }
            opened.setOnKeyListener { _,code,event ->
                when(code) {
                    KeyEvent.KEYCODE_DPAD_UP,KeyEvent.KEYCODE_DPAD_DOWN,KeyEvent.KEYCODE_DPAD_LEFT,KeyEvent.KEYCODE_DPAD_RIGHT ->
                        event.action==KeyEvent.ACTION_DOWN && opened.currentFocus !is ListView && (!navReady(if(event.repeatCount>0)110L else 60L) || padNavigate(opened.window?.decorView,code))
                    KeyEvent.KEYCODE_BUTTON_A -> {
                        if(event.action==KeyEvent.ACTION_DOWN && event.repeatCount==0) {
                            val list=opened.listView;val focused=opened.currentFocus
                            if(list!=null && focused !is Button && list.count>0) {
                                val position=list.selectedItemPosition.takeIf { it>=0 } ?: list.checkedItemPosition.takeIf { it>=0 } ?: 0
                                list.performItemClick(list.getChildAt(position-list.firstVisiblePosition) ?: list,position,list.adapter.getItemId(position))
                            } else focused?.performClick()
                        };true
                    }
                    KeyEvent.KEYCODE_BUTTON_B -> { if(event.action==KeyEvent.ACTION_DOWN)opened.dismiss();true }
                    else -> false
                }
            }
            opened.show()
            val list=opened.listView
            if(list!=null)list.apply { isFocusableInTouchMode=true;requestFocus();setSelection(checkedItemPosition.takeIf { it>=0 } ?: 0) }
            else opened.findViewById<View>(android.R.id.custom)?.let(::firstEnabledButton)?.apply { isFocusableInTouchMode=true;requestFocus() }
            opened.window?.decorView?.setOnGenericMotionListener { _,event -> navigateMotion(event,opened.currentFocus) }
        }
    }
    private fun glyph(key:String)=GlyphRules.key(glyphFamily,key)
    // --- Desejados, Estatísticas, editar e capa (precisam do notebook; leitura fica em cache) ---
    private fun needsNotebook():Boolean { if(store.online)return true;message("Esta função precisa do notebook online. Ligue o Tailscale e tente de novo.");return false }
    private fun textures(game:Game?=null) {
        val helper=TextureStore(store);val box=column();box.addView(text("Texturas HD",22f))
        box.addView(text("PSP e 3DS: instalar nas pastas compartilhadas escolhidas. Feche o emulador antes. ZIP local funciona offline; fontes RAR/7z usam o notebook para preparar o pacote. Ative carregar/substituir texturas no emulador.",13f))
        if(game?.code=="PS")box.addView(text("DuckStation guarda texturas em Android/data. No aparelho atual, a instalação exige o gerenciador do notebook via USB; o seletor Android não libera essa pasta.",13f))
        val systems=listOf("PSP","3DS");val system=Spinner(this).apply { adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,systems);setSelection(if(game?.code=="3DS")1 else 0) };box.addView(system)
        val id=EditText(this).apply { hint="ID: ULUS10279 ou title ID de 16 hexadecimais";setTextColor(appForeground);setHintTextColor(Color.LTGRAY);setSingleLine() };box.addView(id)
        add(box,button("Escolher pacote local ZIP / 7z / RAR") {
            textureCode=system.selectedItem.toString();textureId=id.text.toString().trim().uppercase()
            if(!(if(textureCode=="PSP")Regex("[A-Z]{4}[0-9]{5}") else Regex("[0-9A-F]{16}")).matches(textureId)) { message("Informe o ID exato do jogo/região antes de importar.");return@button }
            dialog?.dismiss();startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION),12)
        })
        add(box,button("Atualizar fontes disponíveis do notebook") {
            dialog?.dismiss();work.execute { runCatching { helper.catalog() }.onSuccess { runOnUiThread { textures(game) } }.onFailure { runOnUiThread { failure(it) } } }
        })
        val catalog=helper.cached()
        box.addView(text("Fontes PSP: confira o ID/região do seu jogo. Nenhum pacote é instalado automaticamente.",13f))
        for(i in 0 until catalog.length()) {
            val pack=catalog.getJSONObject(i)
            add(box,button(pack.getString("nome")+" · "+pack.getString("id_jogo")+" · ${pack.optLong("tamanho")/1024/1024} MB") {
                show(AlertDialog.Builder(this).setTitle("Baixar texturas?").setMessage("${pack.getString("nome")}\n${pack.getString("id_jogo")}\nO notebook baixa/confere a fonte, prepara e envia ao celular. Pode levar vários minutos.").setNegativeButton("Cancelar",null).setPositiveButton("Baixar e instalar") { _,_ -> runTexture { progress -> val ready=helper.prepare(JSONObject().put("id",pack.getString("id")),progress);try { helper.install(ready.first,ready.second.getString("sistema"),ready.second.getString("id_jogo"),progress) } finally { ready.first.delete() } } })
            })
        }
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun runTexture(action:((String)->Unit)->Int) {
        message("Preparando texturas…");var last=0L
        work.execute { runCatching { action { status -> val now=SystemClock.elapsedRealtime();if(now-last>500){last=now;runOnUiThread { message(status) }} } }.onSuccess { count -> runOnUiThread { message("$count textura(s) adicionada(s). Arquivos existentes preservados; confira carregar texturas no emulador.") } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun romTrash() {
        val items=store.prefs.all.filterKeys { it.startsWith("rom-trash:") };val box=column();box.addView(text("Lixeira de ROMs deste celular",22f))
        box.addView(text("Arquivos ficam na pasta original com nome .pyretro-trash-. Saves e estados não entram nesta lixeira. No Drive, recupere pela lixeira do Google.",13f))
        for((key,value) in items)add(box,button("Restaurar $value") { work.execute { val result=runCatching { RomRemoval(store).restore(key.removePrefix("rom-trash:")) };runOnUiThread { result.onSuccess { reloadLocal();romTrash() }.onFailure(::failure) } } })
        if(items.isEmpty())box.addView(text("Nenhuma ROM nesta lixeira.",15f))
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun folderState(code:String)=when(StatusStore(store).folders().firstOrNull { it.code==code }?.access) {
        FolderAccess.READ_WRITE -> "✓";FolderAccess.READ_ONLY -> "somente leitura";FolderAccess.RESELECT -> "permissão expirada";else -> "escolher"
    }
    private fun refreshCatalog(silent:Boolean=false) {
        if(!silent) { dialog?.dismiss();message("Atualizando Biblioteca e catálogo…") }
        work.execute { runCatching { store.refresh() }.onSuccess { fresh -> runOnUiThread {
            catalog=fresh;message(if(silent)"Online · catálogo atualizado agora." else "Catálogo atualizado. As capas são guardadas conforme você navega.");reloadLocal { AppSync.prefetchCovers(this,store,drive,games) }
        } }.onFailure { store.online=false;runOnUiThread { if(!silent)failure(it) } } }
    }
    private fun syncTracking(silent:Boolean=false) {
        if(!silent) { dialog?.dismiss();message("Enviando progresso e tempo…") }
        work.execute { runCatching { store.synchronize() }.onSuccess { result -> val fresh=store.cached();runOnUiThread {
            catalog=fresh;message(if(silent)"Online · catálogo atualizado. $result" else result);reloadLocal { AppSync.prefetchCovers(this,store,drive,games) }
        } }.onFailure { runOnUiThread { if(!silent)failure(it) } } }
    }
    /** Saves e estados pela nuvem (core/cloud_saves no notebook): compara, mostra e só então sincroniza. */
    private fun cloudSaves(title:String="☁ Saves na nuvem",filter:((String,String)->Boolean)?=null,showAll:Boolean=false) {
        val box=column();box.addView(text(title,23f));val info=text("Comparando com o Drive…",15f);box.addView(info)
        val area=column();box.addView(area)
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Fechar",null))
        var busy=false
        fun confirmItem(title:String,description:String,label:String,action:()->Unit) {
            val popup=AlertDialog.Builder(this).setTitle(title).setMessage(description).setNegativeButton("Manter",null).setPositiveButton(label) { _,_ -> action() }.create()
            popup.setOnKeyListener { _,code,event ->
                when(code) {
                    KeyEvent.KEYCODE_BUTTON_A -> { if(event.action==KeyEvent.ACTION_DOWN && event.repeatCount==0)(popup.currentFocus as? Button)?.performClick();true }
                    KeyEvent.KEYCODE_BUTTON_B -> { if(event.action==KeyEvent.ACTION_UP)popup.dismiss();true }
                    else -> false
                }
            };popup.show();popup.getButton(AlertDialog.BUTTON_NEGATIVE).requestFocus()
        }
        fun enable(view:View,value:Boolean) { if(view is Button)view.isEnabled=value;if(view is ViewGroup)for(i in 0 until view.childCount)enable(view.getChildAt(i),value) }
        fun perform(action:()->CloudFeedback) {
            if(busy)return
            busy=true;info.text="Conferindo e aplicando…";enable(area,false)
            work.execute {
                val feedback=action()
                runOnUiThread {
                    if(dialog!==opened || isFinishing || isDestroyed)return@runOnUiThread
                    busy=false;enable(area,true);info.text=feedback.message
                    if(feedback.complete) { message(feedback.message);render();cloudSaves(title,filter) }
                }
            }
        }
        work.execute {
            val phone=runCatching { CloudPhone(store,FileSync(store),saveStorage()) }
            val analysis=phone.mapCatching { it.analyze(filter,showAll) }
            runOnUiThread {
                if(dialog!==opened)return@runOnUiThread
                val result=analysis.getOrElse { info.text="Não foi possível comparar: ${it.message}";return@runOnUiThread }
                if(result.isEmpty()) { info.text="Escolha as pastas de saves em Situação (pasta RetroArch, PPSSPP, 3DS).";return@runOnUiThread }
                val counts=result.values.mapNotNull { it.getOrNull() }.flatten().groupingBy { it.action }.eachCount()
                val failed=result.filterValues { it.isFailure }
                add(area,button("Comparar novamente") { cloudSaves(title,filter,showAll) })
                info.text=if(counts.isEmpty() && failed.isEmpty())"Tudo em dia com a nuvem." else
                    "Enviar: ${counts["push"] ?: 0} · Baixar: ${counts["pull"] ?: 0} · Guardar no histórico: ${counts["forget"] ?: 0} · Conflitos: ${counts["conflict"] ?: 0}"+if(failed.isEmpty())"" else "\nErro em: ${failed.map { it.key+" ("+it.value.exceptionOrNull()?.message+")" }.joinToString()}"
                add(area,button(if(showAll)"Mostrar só pendentes" else "Ver também saves em dia") { cloudSaves(title,filter,!showAll) })
                val pending=counts.filterKeys { it in setOf("push","pull","forget") }.values.sum()
                if(pending>0)add(area,button("Sincronizar agora ($pending)") {
                    perform { CloudFeedback.batch { phone.getOrThrow().apply(filter=filter) } }
                })
                for((group,items) in result)for(item in items.getOrNull().orEmpty().filter { it.action=="conflict" }) {
                    add(area,text("⚠ Conflito: ${item.path}",15f))
                    val line=row();horizontal(area,line)
                    if(item.local!=null)add(line,button("Manter o do celular") { perform { CloudFeedback.resolve("Mantido o do celular: ${item.path}") { phone.getOrThrow().resolve(group,item.path,"local") } } })
                    for((sha,devices) in item.heads)add(line,button((if(sha in item.deletedHeads)"Usar exclusão confirmada" else "Usar da nuvem")+" · ${devices.joinToString()} · ${sha.take(12)}") {
                        confirmItem(item.path,if(sha in item.deletedHeads)"Guardar a cópia local no histórico e aceitar a exclusão explícita deste save?" else "Usar esta versão da nuvem? A versão local fica no histórico.","Confirmar") {
                            perform { CloudFeedback.resolve("Versão escolhida: ${item.path}") { phone.getOrThrow().resolve(group,item.path,"remote",sha) } }
                        }
                    })
                }
                for((group,items) in result)for(item in items.getOrNull().orEmpty().filter { it.action!="forget" })add(area,button("Esquecer este save… · ${item.path}") {
                    confirmItem("Esquecer este save: ${item.path}","Retirar somente este save do uso e impedir que os outros aparelhos restaurem a versão antiga? Cópias locais vão para o histórico na próxima sincronização; blobs antigos permanecem. Saves de outros jogos ficam.","Esquecer este save") {
                        perform { CloudFeedback.resolve("Save esquecido com histórico: ${item.path}") { phone.getOrThrow().forget(group,item) } }
                    }
                })
            }
        }
    }
    private fun pendingChanges() {
        val pending=StatusStore(store).pending().groupBy { it.key }
        paged("Alterações pendentes",pending.map { (key,items) ->
            val game=games.find { it.key==key }
            ((game?.name ?: "Jogo fora do catálogo atual")+" · ${items.count { !it.time }} progresso / ${items.count { it.time }} tempo"+
                if(items.any { it.conflict })" · conferir no notebook" else "") to {
                if(game!=null)details(game) else show(AlertDialog.Builder(this).setTitle("Pendência preservada").setMessage("Este jogo não está no catálogo atual. Atualize o catálogo e confira o registro no notebook. Jogos exclusivamente locais não criam um cadastro no PC automaticamente.").setPositiveButton("Voltar") { _,_ -> pendingChanges() })
                Unit
            }
        })
    }
    private fun folderStatuses() {
        val sync=FileSync(store)
        // Estrutura fixa: Jogos e RetroArch, mais pastas avulsas que já tenham sido escolhidas antes.
        val explicit=store.prefs.all.keys.filter { it.startsWith("tree:") }.map { it.removePrefix("tree:") }.toSet()
        paged("Pastas e permissões",StatusStore(store).folders().filter { it.code=="ROOT" || it.code=="retroarch" || it.code in explicit }.map { folder ->
            val state=when(folder.access) {
                FolderAccess.UNSELECTED -> "não escolhida"
                FolderAccess.RESELECT -> "sem leitura persistente · escolher novamente"
                FolderAccess.READ_ONLY -> "leitura salva · conceder escrita para copiar"
                FolderAccess.READ_WRITE -> "leitura e escrita salvas"
            }
            "${folder.label} · $state" to {
                if(folder.code=="retroarch" || folder.code in sync.groups)pickSyncFolder(folder.code) else { dialog?.dismiss();pickFolder(folder.code) }
                Unit
            }
        })
    }
    private fun connectionApps() {
        val apps=listOf("Tailscale" to listOf("com.tailscale.ipn"),"RetroArch" to listOf("com.retroarch.aarch64","com.retroarch"),
            "PPSSPP" to listOf("org.ppsspp.ppssppgold","org.ppsspp.ppsspp"),"3DS · Lime3DS / Azahar" to listOf("io.github.lime3ds.android","io.github.azahar_emu.azahar"),
            "Xbox · XBXPlay" to listOf("com.grill.xbxplay"),"PC · Moonlight" to listOf("com.limelight"))
        val box=column();box.addView(text("Emuladores e conexões",22f))
        box.addView(text("Aplicativo encontrado significa apenas que pode ser aberto. Login, pareamento, VPN, cores e funcionamento em jogo precisam ser conferidos no próprio aplicativo.",14f))
        for((label,packages) in apps) {
            val installed=packages.firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null }
            add(box,button("$label · ${if(installed==null)"não encontrado" else "abrir"}") {
                if(installed!=null)openPackage(installed)
            }.apply { isEnabled=installed!=null;alpha=if(installed!=null)1f else 0.55f })
        }
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun paged(title:String,items:List<Pair<String,()->Unit>>,page:Int=0) {
        val box=column();box.addView(text(title,22f))
        if(items.isEmpty())box.addView(text("Nenhum item disponível.",15f))
        items.drop(page*16).take(16).forEach { (label,action) -> add(box,button(label,action)) }
        val navigation=row()
        if(page>0)add(navigation,button("Anterior") { paged(title,items,page-1) })
        if((page+1)*16<items.size)add(navigation,button("Próxima") { paged(title,items,page+1) })
        box.addView(navigation)
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun versionDate(timestamp:Long)=java.text.SimpleDateFormat("dd/MM/yyyy HH:mm",java.util.Locale.getDefault()).format(java.util.Date(timestamp))
    private fun localVersions(group:String) {
        dialog?.dismiss();message("Consultando versões locais…")
        work.execute { runCatching { FileSync(store).localHistory(group) }.onSuccess { versions -> runOnUiThread {
            paged("Versões neste celular",versions.map { version ->
                "${versionDate(version.created)} · ${version.path} · ${version.file.size} B" to {
                    show(AlertDialog.Builder(this).setTitle("Restaurar versão local?").setMessage("${version.path}\n${versionDate(version.created)}\nFeche o emulador. O arquivo atual também será preservado no histórico. A restauração funciona offline.").setNegativeButton("Cancelar",null).setPositiveButton("Restaurar") { _,_ ->
                        work.execute { runCatching { FileSync(store).restoreLocal(version) }.onSuccess { runOnUiThread { message("Versão restaurada. Analise a sincronização antes de copiar ao notebook.") } }.onFailure { runOnUiThread { failure(it) } } }
                    });Unit
                }
            })
        } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun playlists() {
        paged("Playlists do RetroArch",PlaylistStore(store).names.map { (code,label) -> label to {
            val box=column();box.addView(text(label,22f))
            add(box,button("Analisar atualização") { analyzePlaylist(code,label) })
            add(box,button("Recuperar versão anterior") { playlistVersions(code) })
            add(box,button("Desativar atualização automática") { store.prefs.edit().putBoolean("playlist-auto:$code",false).apply();message("Atualização automática desativada para $label.") })
            show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null));Unit
        } }+listOf("Último resultado" to { show(AlertDialog.Builder(this).setTitle("Playlists").setMessage(store.prefs.getString("playlist-last","Nenhuma atualização aplicada.")).setPositiveButton("Fechar",null));Unit }))
    }
    private fun analyzePlaylist(code:String,label:String) {
        dialog?.dismiss();message("Analisando playlist de $label…")
        work.execute { runCatching { PlaylistStore(store).plan(code) }.onSuccess { plan -> runOnUiThread {
            val box=column();box.addView(text(plan.name,20f))
            box.addView(text("${plan.added} entrada(s) nova(s), ${plan.removed} ausente(s) da pasta local a retirar. Campos das entradas mantidas e itens de outras pastas serão preservados. O arquivo atual fica no histórico. Feche o RetroArch antes de aplicar.",14f))
            val auto=CheckBox(this).apply { text="Atualizar também após baixar/remover uma ROM pelo PyRetro";isChecked=store.prefs.getBoolean("playlist-auto:$code",false);minHeight=dp(48);setTextColor(appForeground) };box.addView(auto)
            show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Cancelar",null).setPositiveButton("Aplicar") { _,_ ->
                val automatic=auto.isChecked
                work.execute { runCatching { PlaylistStore(store).apply(plan,automatic) }.onSuccess { runOnUiThread { message("Playlist atualizada. Versão anterior preservada.") } }.onFailure { runOnUiThread { failure(it) } } }
            })
        } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun playlistVersions(code:String) {
        dialog?.dismiss();message("Consultando histórico da playlist…")
        work.execute { runCatching { PlaylistStore(store).versions(code) }.onSuccess { versions -> runOnUiThread {
            paged("Versões da playlist",versions.map { version -> "${versionDate(version.created)} · ${version.name}" to {
                show(AlertDialog.Builder(this).setTitle("Restaurar playlist?").setMessage("Feche o RetroArch. A versão atual será preservada. A atualização automática será desativada até você analisar novamente.").setNegativeButton("Cancelar",null).setPositiveButton("Restaurar") { _,_ ->
                    work.execute { runCatching { PlaylistStore(store).restore(version,code) }.onSuccess { runOnUiThread { message("Playlist restaurada; histórico preservado.") } }.onFailure { runOnUiThread { failure(it) } } }
                });Unit
            } })
        } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun cloudMenu() {
        paged("Catálogo da nuvem / Drive",store.folders.map { (code,label) -> label to { cloudCode(code);Unit } })
    }
    private fun cloudCode(code:String) {
        val box=column();box.addView(text("Nuvem · ${store.folders[code]}",22f))
        box.addView(text("Escolha arquivos em lote ou uma pasta, se o provedor oferecer essa opção. O app indexa nomes e tamanhos, sem baixar ROMs. Associações únicas são propostas; homônimos ficam para sua escolha. Não precisa do notebook/Tailscale.",14f))
        fun pick(tree:Boolean) {
            store.prefs.edit().putString("index-picking",code).apply();dialog?.dismiss()
            val intent=if(tree)Intent(Intent.ACTION_OPEN_DOCUMENT_TREE) else Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(intent,if(tree)15 else 14)
        }
        add(box,button("Adicionar arquivos em lote") { pick(false) })
        add(box,button("Adicionar pasta do provedor") { pick(true) })
        add(box,button("Atualizar índice das origens escolhidas") { analyzeCloud(code,CloudIndex(store).sources(code)) })
        add(box,button("Limpar somente este índice") {
            show(AlertDialog.Builder(this).setTitle("Limpar índice de ${store.folders[code]}?").setMessage("Remove apenas a lista de fontes e vínculos automáticos. ROMs locais, arquivos da nuvem e vínculos manuais ficam preservados.").setNegativeButton("Cancelar",null).setPositiveButton("Limpar índice") { _,_ ->
                CloudIndex(store).apply(CloudPlan(code,JSONArray(),emptyList(),emptyMap(),0));reloadLocal()
            })
        })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun analyzeCloud(code:String,sources:JSONArray) {
        dialog?.dismiss();message("Lendo nomes de arquivos na nuvem…");val snapshot=catalog.toList()
        work.execute { runCatching { CloudIndex(store).analyze(code,sources,snapshot) }.onSuccess { plan -> runOnUiThread {
            show(AlertDialog.Builder(this).setTitle("Aplicar catálogo da nuvem?").setMessage("${plan.files.size} ROM(s) no índice, ${plan.matches.size} associação(ões) única(s), ${plan.ambiguous} jogo(s) ambíguo(s). Arquivos sem associação aparecem como entradas da nuvem. Vínculos manuais prevalecem. Nenhum download será iniciado.").setNegativeButton("Cancelar",null).setPositiveButton("Aplicar índice") { _,_ ->
                runCatching { CloudIndex(store).apply(plan) }.onSuccess { reloadLocal();message("Índice atualizado. Escolha um jogo para baixar sob demanda.") }.onFailure(::failure)
            })
        } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun queueAction(action:()->Unit) {
        runCatching(action).onSuccess { downloads() }.onFailure { error ->
            show(AlertDialog.Builder(this).setTitle("Downloads").setMessage(error.message ?: "Não foi possível alterar a fila.").setPositiveButton("Voltar") { _,_ -> downloads() })
        }
    }
    private fun queueLabel(row:QueuedDownload):String {
        val state=when(row.state) { DownloadState.WAITING -> "Aguardando";DownloadState.RUNNING -> if(queue().pausing)"Pausa solicitada" else "Baixando";DownloadState.PAUSED -> "Pausado";DownloadState.FAILED -> "Falhou";DownloadState.DONE -> "Concluído" }
        return "$state · ${bytesLabel(row.bytes)}"+(row.total?.let { " / ${bytesLabel(it)}" } ?: "")
    }
    private fun queueList() {
        runCatching {
            val rows=queue().snapshot()
            paged("Fila de downloads",listOf("Atualizar lista" to { queueList();Unit })+rows.map { row ->
                "${row.game.name}\n${queueLabel(row)}" to { queueItem(row.game.key);Unit }
            })
        }.onFailure(::failure)
    }
    private fun queueItem(key:String) {
        val entry=queue().snapshot().firstOrNull { it.game.key==key } ?: return
        val box=column();box.addView(platformChip(entry.game.code,entry.game.platform));box.addView(text(entry.game.name,21f));val state=text(queueLabel(entry),14f);box.addView(state)
        if(entry.error.isNotBlank())box.addView(text(entry.error,13f))
        if(entry.state in setOf(DownloadState.PAUSED,DownloadState.FAILED))add(box,button("Tentar novamente · deixar aguardando") { queueAction { queue().retry(key) } })
        if(entry.state!=DownloadState.RUNNING) {
            val order=row();add(order,button("↑ Antes") { queueAction { queue().move(key,-1) } });add(order,button("↓ Depois") { queueAction { queue().move(key,1) } });horizontal(box,order)
            add(box,button("Retirar da fila · manter parcial") {
                show(AlertDialog.Builder(this).setTitle("Retirar da fila?").setMessage("${entry.game.name}\nA ROM local, a origem e qualquer cópia parcial serão preservadas. Descarte de parcial é separado.").setNegativeButton("Cancelar",null).setPositiveButton("Retirar") { _,_ -> queueAction { queue().remove(key) } })
            })
        } else add(box,button("Pausar fila") { queueAction { queue().pause() } })
        if(entry.state==DownloadState.DONE)add(box,button("Ver jogo") { dialog?.dismiss();reloadLocal { games.find { it.key==key }?.let(::details) } })
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar") { _,_ -> queueList() })
        updateQueueStatus={ if(dialog===opened)state.text=queue().snapshot().firstOrNull { it.game.key==key }?.let(::queueLabel) ?: "Retirado da fila." }
    }
    private fun help(box:LinearLayout,label:String,value:String) {
        val explanation=text(value,13f).apply { visibility=View.GONE }
        val toggle=button("▸ $label") {}
        toggle.setOnClickListener { explanation.visibility=if(explanation.visibility==View.GONE)View.VISIBLE else View.GONE;toggle.text=(if(explanation.visibility==View.VISIBLE)"▾ " else "▸ ")+label }
        add(box,toggle);box.addView(explanation)
    }
    private fun expandable(box:LinearLayout,label:String,expanded:Boolean=false,changed:(Boolean)->Unit={}):LinearLayout {
        val panel=column().apply { visibility=if(expanded)View.VISIBLE else View.GONE }
        val toggle=button((if(expanded)"▾ " else "▸ ")+label) {}
        toggle.setOnClickListener { val open=panel.visibility==View.GONE;panel.visibility=if(open)View.VISIBLE else View.GONE;toggle.text=(if(open)"▾ " else "▸ ")+label;changed(open) }
        add(box,toggle);box.addView(panel);return panel
    }
    private fun spaceManager() {
        val loading=show(AlertDialog.Builder(this).setTitle("Espaço e jogos fixados").setMessage("Lendo nomes e tamanhos das ROMs locais…").setNegativeButton("Fechar",null))
        val snapshot=catalog.toList()
        work.execute { runCatching { SpaceStore(store).scan(snapshot) }.onSuccess { result -> runOnUiThread {
            if(dialog===loading && !isFinishing && !isDestroyed)spaceOverview(result)
        } }.onFailure { error -> runOnUiThread { if(dialog===loading)show(AlertDialog.Builder(this).setTitle("Espaço").setMessage(error.message).setPositiveButton("Fechar",null)) } } }
    }
    private fun spaceOverview(snapshot:SpaceSnapshot) {
        val box=column();box.addView(text("Espaço e jogos fixados",22f))
        box.addView(text("${snapshot.roms.size} ROM(s) · ${bytesLabel(snapshot.roms.sumOf { it.stamp.size ?: 0 })} medidos · ${snapshot.roms.count { it.stamp.size==null }} tamanho(s) desconhecido(s).\nLivre para o app/checkpoints: ${bytesLabel(snapshot.privateFree)}.",14f))
        if(snapshot.errors.isNotEmpty())box.addView(text("Leitura parcial: ${snapshot.errors.joinToString()}. Atualize as permissões; os totais cobrem apenas o que pôde ser lido.",13f))
        help(box,"O que esta tela inclui","Somente ROMs das pastas escolhidas, uma vez por documento. Tamanho desconhecido não significa zero. Saves, estados, texturas, BIOS e históricos ficam preservados e não entram nesse total. Fixar protege a ROM; desfixar não apaga. A remoção é individual, confirmada e confere novamente a ROM. Downloads precisam de espaço para checkpoint privado e cópia final.")
        val systems=listOf("Todos os sistemas")+snapshot.roms.map { it.game.code }.distinct().sorted()
        val filters=listOf("Todos","Finalizados","Não finalizados","Fixados","Finalizados removíveis")
        val system=Spinner(this).apply { adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,systems.map { store.folders[it] ?: it }) }
        val filter=Spinner(this).apply { adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,filters) }
        val controls=row();add(controls,system);add(controls,filter);horizontal(box,controls)
        val listing=column();box.addView(listing);var currentPage=0
        fun refresh() {
            val selected=snapshot.roms.filter { item ->
                val pinned=SpaceStore(store).pinned(item.game)
                (system.selectedItemPosition==0 || item.game.code==systems[system.selectedItemPosition]) && when(filter.selectedItemPosition) {
                    1 -> item.finished;2 -> !item.finished;3 -> pinned
                    4 -> item.finished && DownloadQueueRules.removable(pinned,queue().contains(item.game.key),item.stamp.name.substringAfterLast('.'))
                    else -> true
                }
            }
            val pages=((selected.size+11)/12).coerceAtLeast(1);currentPage=currentPage.coerceIn(0,pages-1);listing.removeAllViews()
            listing.addView(text("${selected.size} ROM(s) · ${bytesLabel(selected.sumOf { it.stamp.size ?: 0 })} medidos · ${currentPage+1}/$pages",13f))
            for(item in selected.drop(currentPage*12).take(12))add(listing,button((if(SpaceStore(store).pinned(item.game))"📌 " else "")+item.game.name+"\n"+(item.stamp.size?.let(::bytesLabel) ?: "Tamanho desconhecido")+" · ${store.folders[item.game.code]}") { spaceItem(item) })
            val navigation=row();if(currentPage>0)add(navigation,button("Anterior") { currentPage--;refresh() });if(currentPage+1<pages)add(navigation,button("Próxima") { currentPage++;refresh() });horizontal(listing,navigation)
        }
        val listener=object:AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long) { currentPage=0;refresh() }
            override fun onNothingSelected(parent:AdapterView<*>?){}
        }
        system.onItemSelectedListener=listener;filter.onItemSelectedListener=listener
        add(box,button("Atualizar leitura de espaço") { spaceManager() });add(box,button("Downloads e cópias parciais") { downloads() })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Fechar",null));refresh()
    }
    private fun spaceItem(item:SpaceRom) {
        val box=column();val pinned=SpaceStore(store).pinned(item.game)
        box.addView(text(item.game.name,21f));box.addView(text((item.stamp.size?.let(::bytesLabel) ?: "Tamanho desconhecido")+" · ${store.folders[item.game.code]}"+(if(item.finished)" · finalizado" else ""),14f))
        add(box,button(if(pinned)"Desfixar · permitir remoção" else "Fixar · manter baixado") {
            runCatching { SpaceStore(store).setPinned(item.game,!pinned);render();spaceItem(item) }.onFailure { error -> show(AlertDialog.Builder(this).setTitle("Fixação").setMessage(error.message).setPositiveButton("Fechar",null)) }
        })
        val removable=DownloadQueueRules.removable(pinned,queue().contains(item.game.key),item.stamp.name.substringAfterLast('.'))
        add(box,button("Remover somente esta ROM local") {
            show(AlertDialog.Builder(this).setTitle("Excluir ROM local?").setMessage("${item.game.name}\n${item.stamp.name}\nApenas esta ROM será removida. Saves, estados, BIOS, texturas, progresso, histórico e origem permanecem. A ROM será conferida novamente.").setNegativeButton("Cancelar") { _,_ -> spaceItem(item) }.setPositiveButton("Excluir ROM") { _,_ ->
                dialog?.dismiss();work.execute { runCatching { store.removeLocal(item.game,item.stamp);PlaylistStore(store).afterChange(item.game.code) }.onSuccess { result -> runOnUiThread { message("ROM removida. $result");reloadLocal();spaceManager() } }.onFailure { error -> runOnUiThread { failure(error) } } }
            })
        }.apply { isEnabled=removable;alpha=if(removable)1f else .55f })
        if(!removable)box.addView(text("Para remover, desfixe/retire da fila. CUE/M3U exigem conferir o conjunto no notebook.",13f))
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar") { _,_ -> spaceManager() })
    }
    private fun downloads() {
        val box=column();box.addView(text("Downloads",22f))
        help(box,"Como funciona a fila","Um arquivo por vez, na ordem escolhida. Ao sair do app, a fila continua em segundo plano com uma notificação de progresso, que tem Pausar; ao terminar, avisa o resultado. Se o Android encerrar o app, a fila não recomeça sozinha: abra Downloads e continue. Retirar um item não descarta o parcial; descartá-lo exige uma ação separada. Na retomada, todo o prefixo é conferido e pode ser relido pelo provedor. A publicação final de um arquivo já conferido pode terminar durante a pausa. Não abre jogos automaticamente.")
        val progress=text("",14f);box.addView(progress)
        val start=button("Iniciar / continuar fila") { queueAction { queue().start() } };add(box,start)
        val pause=button("Pausar fila") { queueAction { queue().pause();DownloadStore.pause() } };add(box,pause)
        add(box,button("Ver fila / reordenar itens") { queueList() })
        add(box,button("Ver cópias parciais") {
            dialog?.dismiss()
            work.execute { runCatching { DownloadStore(store).jobs() }.onSuccess { jobs -> runOnUiThread {
                paged("Cópias parciais",jobs.map { job -> "${job.optString("title")} · ${job.getLong("bytes")/1024/1024} MB" to {
                    val game=games.find { it.key==job.getString("key") } ?: Game("",job.getString("key"),job.getString("title"),store.folders[job.getString("code")] ?: "",job.getString("code"))
                    show(AlertDialog.Builder(this).setTitle(game.name).setMessage("Continuar a cópia ou descartar somente o checkpoint deste download? O jogo existente e a origem não serão apagados.").setNegativeButton("Voltar",null).setNeutralButton("Descartar parcial") { _,_ ->
                        work.execute { runCatching { queue().remove(game.key);DownloadStore(store).discard(game.key) }.onSuccess { runOnUiThread { message("Cópia parcial descartada.") } }.onFailure { runOnUiThread { failure(it) } } }
                    }.setPositiveButton("Adicionar à fila") { _,_ -> runCatching { DownloadFlow.enqueue(store,game) }.onSuccess { message("⬇ ${game.name}: na fila.") }.onFailure(::failure) });Unit
                } })
            } }.onFailure { runOnUiThread { failure(it) } } }
        })
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
        fun update() { if(dialog===opened) {
            runCatching { val helper=queue();val rows=helper.snapshot();val active=rows.firstOrNull { it.state==DownloadState.RUNNING }
                progress.text="${rows.count { it.state==DownloadState.WAITING }} aguardando · ${rows.count { it.state==DownloadState.PAUSED }} pausado(s) · ${rows.count { it.state==DownloadState.FAILED }} falha(s) · ${rows.count { it.state==DownloadState.DONE }} concluído(s)"+(active?.let { "\n${it.game.name}: ${queueLabel(it)}" } ?: "")
                start.isEnabled=!helper.running;pause.isEnabled=helper.running
            }.onFailure { progress.text="Fila indisponível: ${it.message}";start.isEnabled=false;pause.isEnabled=false }
        } }
        updateQueueStatus={update()};update()
    }
    private fun pickSyncFolder(group:String) {
        syncPicking=group;dialog?.dismiss()
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            .putExtra(DocumentsContract.EXTRA_INITIAL_URI,DocumentsContract.buildDocumentUri("com.android.externalstorage.documents","primary:RetroArch")),13)
    }
    /** Saves e estados de um jogo pela nuvem (mesmo motor e protocolo do notebook). */
    private fun gameSaves(game:Game) {
        val sync=FileSync(store);val retro=game.code!="PSP" && game.code!="3DS"
        val wrongFolder=sync.retroarchTree()?.let { SaveRules.retroarchFolderProblem(DocumentsContract.getTreeDocumentId(it)) }
        if(retro && (sync.tree("retro-saves")==null || wrongFolder!=null)) {
            show(AlertDialog.Builder(this).setTitle("Saves de ${game.name}").setMessage((wrongFolder?.let { "$it\n\n" } ?: "")+"Escolha uma vez a pasta RetroArch do celular (a raiz, normalmente RetroArch no armazenamento interno; não entre em saves nem states).")
                .setNegativeButton("Voltar") { _,_ -> details(game) }.setPositiveButton("Escolher pasta") { _,_ -> pickSyncFolder("retroarch") });return
        }
        dialog?.dismiss()
        if(!retro) { titleSaveChoice(game);return }
        work.execute {
            val label=SaveRules.label(game.localUri?.let { runCatching { store.displayName(it) }.getOrNull() } ?: game.romName.substringAfterLast('/').ifBlank { game.name },store.extensionsFor(game.code))
            val mine:(String,String)->Boolean={ g,path -> g in setOf("retro-saves","retro-states") && SaveRules.belongs(path,game.code,label) }
            runOnUiThread { cloudSaves("💾 ${game.name}",mine) }
        }
    }
    private fun titleSaveChoice(game:Game) {
        work.execute {
            val source=CloudRules.sha256((store.prefs.getString("cloud:${game.key}",null) ?: game.localUri?.let { uri -> "$uri|${runCatching { SpaceStore(store).stamp(uri) }.getOrNull()}" } ?: game.romName).toByteArray())
            val mapping=if(store.online && game.id.isNotBlank())runCatching { extras.saveIds(game.id) }.getOrNull() else extras.cachedSaveIds(game.id)
            val local=if(game.code=="3DS")game.localUri?.let { runCatching { read3dsId(it) }.getOrNull() } else null
            val identified=mapping?.optJSONArray("titleIds")?.let { ids -> if(ids.length()==1 && mapping.optString("status")=="identified")ids.optString(0) else null }
            val saved=store.prefs.getString("save-title:${game.key}",null)?.takeIf { store.prefs.getString("save-title-source:${game.key}",null)==source }
            val title=local ?: saved?.takeIf { SaveIdRules.valid(game.code,it) } ?: identified
            runOnUiThread {
                if(title!=null && SaveIdRules.valid(game.code,title)) { titleSaves(game,title);return@runOnUiThread }
                val candidates=mapping?.optJSONArray("candidates") ?: JSONArray()
                val box=column();box.addView(text("Saves de ${game.name}",22f));box.addView(text("Não há ID verificado deste jogo. Escolha a região/ID ou abra explicitamente todos os jogos do emulador. Extdata de 3DS exige escolha do grupo completo.",14f))
                for(i in 0 until candidates.length()) { val c=candidates.getJSONObject(i);val id=c.optString("titleId")
                    if(SaveIdRules.valid(game.code,id))add(box,button("${c.optString("name")} · $id") { store.prefs.edit().putString("save-title:${game.key}",id).putString("save-title-source:${game.key}",source).apply();titleSaves(game,id) }) }
                val input=EditText(this).apply { hint=if(game.code=="PSP")"Serial da região, ex.: ULUS12345" else "Program ID: 00040000xxxxxxxx";setTextColor(appForeground) };box.addView(input)
                add(box,button("Usar este ID") { val id=input.text.toString().trim().let { if(game.code=="PSP")it.uppercase() else it.lowercase() }
                    if(!SaveIdRules.valid(game.code,id)) { message("ID inválido; confira a região do jogo.");return@button };store.prefs.edit().putString("save-title:${game.key}",id).putString("save-title-source:${game.key}",source).apply();titleSaves(game,id) })
                add(box,button("Todos os jogos de ${if(game.code=="PSP")"PPSSPP" else "3DS (inclui extdata)"}") { emulatorSaves(game) })
                show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar") { _,_ -> details(game) })
            }
        }
    }
    private fun emulatorSaves(game:Game) {
        val groups=SaveIdRules.groups(game.code).toSet()
        cloudSaves("💾 Todos os jogos de ${if(game.code=="PSP")"PPSSPP" else "3DS · saves e extdata"}",filter={ group,_ -> group in groups })
    }
    private fun titleSaves(game:Game,title:String) {
        fun open(tree:String?)=cloudSaves("💾 ${game.name} · $title",filter={ group,path -> SaveIdRules.matches(group,path,title) && (tree==null || path.startsWith("$tree/")) })
        if(game.code!="3DS") { open(null);return }
        dialog?.dismiss();message("Conferindo árvores de saves 3DS…")
        work.execute {
            val result=runCatching { CloudPhone(store,FileSync(store),saveStorage()).paths("3ds-saves").let { SaveIdRules.trees(it,title) } }
            runOnUiThread { result.onSuccess { trees ->
                if(trees.size<=1)open(trees.singleOrNull())
                else show(AlertDialog.Builder(this).setTitle("Qual árvore 3DS o emulador usa?").setItems(trees.toTypedArray()) { _,which -> open(trees[which]) }.setNegativeButton("Voltar",null))
            }.onFailure { show(AlertDialog.Builder(this).setTitle("Saves 3DS indisponíveis").setMessage(it.message).setPositiveButton("Escolher pasta") { _,_ -> pickSyncFolder("3ds-saves") }.setNegativeButton("Voltar",null)) } }
        }
    }
    /** PSP/3DS: o notebook diz o ID do título do jogo (Redump para PSP, cabeçalho da ROM para 3DS).
     *  Sem ID seguro (ou jogo sem cadastro), abre o grupo inteiro como antes. Vários candidatos
     *  viram escolha, guardada por jogo; nunca copia todos. */
    /** Program ID da ROM 3DS deste celular (lê só os cabeçalhos, sem copiar o arquivo). */
    private fun read3dsId(uri:Uri):String = contentResolver.openFileDescriptor(uri,"r")!!.use { fd ->
        java.io.FileInputStream(fd.fileDescriptor).channel.use { channel ->
            SaveIdRules.programId(channel.size()) { offset -> val buffer=java.nio.ByteBuffer.allocate(512);channel.position(offset)
                while(buffer.hasRemaining() && channel.read(buffer)>0) {};require(!buffer.hasRemaining()) { "Cabeçalho truncado." };buffer.array() }
        }
    }
    /** Organizar do notebook pelo celular: mesmas regras do modo TV (nome limpo, capa da imagem ao lado
     *  ou das bases de ROM, gênero, substitui o que já existe com o antigo na lixeira do PC). */
    private fun organizeRoms() {
        if(!needsNotebook())return
        message("Lendo a pasta de organizar e os Downloads do notebook…")
        work.execute {
            val result=runCatching { extras.organizePending() }
            runOnUiThread { if(isFinishing || isDestroyed)return@runOnUiThread
                result.onFailure(::failure).onSuccess { items ->
                    val box=column();box.addView(text("🗂 Organizar ROMs novas",22f))
                    box.addView(text("Pasta de organizar e Downloads do notebook. Escolha o sistema: o nome sai limpo, a capa e o gênero são preenchidos; se já existir, o antigo vai para a lixeira do PC.",13f))
                    if(items.isEmpty())box.addView(text("Nada esperando organização.",15f))
                    for(item in items) {
                        val member=item.optString("member").takeIf { it.isNotBlank() && it!="null" }
                        val status=item.getString("status");val exists=item.getJSONArray("exists_in")
                        box.addView(text((if(item.getString("source")=="downloads")"⬇ " else "")+(member ?: item.getString("name"))+
                            (if(status!="pronto")" · $status" else " → ${item.getString("final")}")+
                            (if(!item.isNull("cover_image"))" · 🖼 capa ao lado" else "")+(if(exists.length()>0)" · substitui o que existe" else ""),14f).apply { setTypeface(null,Typeface.BOLD) })
                        val line=row();horizontal(box,line)
                        val candidates=item.getJSONArray("candidates")
                        if(status=="pronto")for(i in 0 until candidates.length()) { val code=candidates.getJSONObject(i).getString("code")
                            add(line,button("→ $code") { confirmOrganize("Mover ${item.getString("final")} para $code?") {
                                message("Organizando ${item.getString("final")}… capa e gênero podem levar um pouco.")
                                work.execute { val done=runCatching { extras.organizeMove(item.getString("id"),code) }
                                    runOnUiThread { done.onSuccess { d -> message("${d.optString("message")} · capa: ${d.optString("cover").takeIf { it.isNotBlank() && it!="null" } ?: "não achada"} · gênero: ${d.optString("genero").takeIf { it.isNotBlank() && it!="null" } ?: "não achado"}");organizeRoms() }.onFailure(::failure) } } } }) }
                        if(status!="baixando")add(line,button("Descartar") { confirmOrganize("Mandar ${item.getString("name")} para a lixeira do notebook?") {
                            work.execute { val done=runCatching { extras.organizeDiscard(item.getString("id")) };runOnUiThread { done.onSuccess { message("${item.getString("name")} foi para a lixeira.");organizeRoms() }.onFailure(::failure) } } } })
                    }
                    show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
                }
            }
        }
    }
    private fun confirmOrganize(question:String,action:()->Unit) { show(AlertDialog.Builder(this).setMessage(question).setNegativeButton("Voltar") { _,_ -> organizeRoms() }.setPositiveButton("Confirmar") { _,_ -> action() }) }
    private fun syncFiles() {
        val sync=FileSync(store);val box=column();box.addView(text("Saves e estados",22f))
        box.addView(text("Sincroniza direto pelo Drive (pasta Jogos/PyRetro-Nuvem), sem o notebook ligado. Feche os emuladores. Conflito nunca sobrescreve: você escolhe; versões substituídas ficam no histórico.",13f))
        box.addView(text("Estados ficam separados por aparelho. Saves e extdata de 3DS continuam compartilhados; jogos instalados ficam fora.",13f))
        add(box,button("☁ Comparar e sincronizar tudo") { dialog?.dismiss();cloudSaves() })
        add(box,button("Escolher pasta RetroArch") { pickSyncFolder("retroarch") })
        for((group,label) in sync.groups.filterKeys { it in CloudPhone.prefixes })add(box,button("Pasta de $label") { pickSyncFolder(group) })
        for((group,label) in sync.groups.filterKeys { it in CloudPhone.prefixes })add(box,button("Versões deste celular · $label") { localVersions(group) })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun pickFolder(code:String) { pickingCode=code;startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),10) }
    private fun openPackage(name:String) {
        val intent=packageManager.getLaunchIntentForPackage(name)
        if(intent==null) { message("Aplicativo não instalado: $name");return }
        startActivity(intent)
    }
    private fun isDpad(code:Int)=code==KeyEvent.KEYCODE_DPAD_UP || code==KeyEvent.KEYCODE_DPAD_DOWN || code==KeyEvent.KEYCODE_DPAD_LEFT || code==KeyEvent.KEYCODE_DPAD_RIGHT
    private fun fromPad(event:KeyEvent)=event.source and (InputDevice.SOURCE_GAMEPAD or InputDevice.SOURCE_JOYSTICK)!=0
    /** Um passo por vez: se o controle manda tecla e eixo juntos para o mesmo toque, só o primeiro vale. */
    private fun navReady(gap:Long):Boolean { val now=SystemClock.elapsedRealtime();if(now-lastMotion<gap)return false;lastMotion=now;return true }
    /** Foco por geometria (ignora recortes de rolagem): alcança as abas ocultas à direita, Sortear, Estatísticas e os botões de diálogos. */
    private fun padNavigate(root:View?,code:Int):Boolean {
        root ?: return false
        val items=ArrayList<View>();collectFocusable(root,items)
        if(items.isEmpty())return false
        val current=root.findFocus()?.takeIf { it in items }
        val target=if(current==null) items.first()
        else {
            val c=boundsOf(current);var best:View?=null;var bestScore=Long.MAX_VALUE
            for(view in items) {
                if(view===current)continue
                val r=boundsOf(view)
                val ahead=when(code) { KeyEvent.KEYCODE_DPAD_RIGHT -> r.centerX()>c.centerX() && r.right>c.right;KeyEvent.KEYCODE_DPAD_LEFT -> r.centerX()<c.centerX() && r.left<c.left
                    KeyEvent.KEYCODE_DPAD_DOWN -> r.centerY()>c.centerY() && r.bottom>c.bottom;else -> r.centerY()<c.centerY() && r.top<c.top }
                if(!ahead)continue
                // Esquerda/direita só andam na mesma linha; entre linhas é com cima/baixo.
                if((code==KeyEvent.KEYCODE_DPAD_LEFT || code==KeyEvent.KEYCODE_DPAD_RIGHT) && (r.top>=c.bottom || r.bottom<=c.top))continue
                val horizontal=code==KeyEvent.KEYCODE_DPAD_LEFT || code==KeyEvent.KEYCODE_DPAD_RIGHT
                val major=(if(horizontal) (if(code==KeyEvent.KEYCODE_DPAD_RIGHT)r.left-c.right else c.left-r.right) else (if(code==KeyEvent.KEYCODE_DPAD_DOWN)r.top-c.bottom else c.top-r.bottom)).let { if(it>0)it else (if(horizontal)Math.abs(r.centerX()-c.centerX()) else Math.abs(r.centerY()-c.centerY())) }.toLong()
                val minor=(if(horizontal)Math.abs(r.centerY()-c.centerY()) else Math.abs(r.centerX()-c.centerX())).toLong()
                val score=13*major*major+minor*minor
                if(score<bestScore) { bestScore=score;best=view }
            }
            best ?: return true
        }
        target.requestFocus();target.requestRectangleOnScreen(Rect(0,0,target.width,target.height),false)
        return true
    }
    private fun boundsOf(view:View):Rect { val at=IntArray(2);view.getLocationOnScreen(at);return Rect(at[0],at[1],at[0]+view.width,at[1]+view.height) }
    private fun collectFocusable(view:View,out:MutableList<View>) {
        if(view.visibility!=View.VISIBLE)return
        val container=view is ScrollView || view is HorizontalScrollView || view is AbsListView
        if(!container && view.isFocusable && view.isEnabled && view.width>0 && view.height>0)out.add(view)
        if(view is ViewGroup && view.descendantFocusability!=ViewGroup.FOCUS_BLOCK_DESCENDANTS)for(index in 0 until view.childCount)collectFocusable(view.getChildAt(index),out)
    }
    private fun navigateMotion(event:MotionEvent,focused:View?):Boolean {
        if(event.isFromSource(InputDevice.SOURCE_JOYSTICK) && event.action==MotionEvent.ACTION_MOVE) {
            val lt=maxOf(event.getAxisValue(MotionEvent.AXIS_LTRIGGER),event.getAxisValue(MotionEvent.AXIS_BRAKE))>.55
            val rt=maxOf(event.getAxisValue(MotionEvent.AXIS_RTRIGGER),event.getAxisValue(MotionEvent.AXIS_GAS))>.55
            leftTrigger=lt;rightTrigger=rt
            val x=event.getAxisValue(MotionEvent.AXIS_X)+event.getAxisValue(MotionEvent.AXIS_HAT_X)
            val y=event.getAxisValue(MotionEvent.AXIS_Y)+event.getAxisValue(MotionEvent.AXIS_HAT_Y)
            val moveCode=when { y>.55 -> KeyEvent.KEYCODE_DPAD_DOWN;y<-.55 -> KeyEvent.KEYCODE_DPAD_UP;x>.55 -> KeyEvent.KEYCODE_DPAD_RIGHT;x<-.55 -> KeyEvent.KEYCODE_DPAD_LEFT;else -> return false }
            val root=dialog?.window?.decorView ?: pageRoot
            // Depois de um toque na tela o Android está em modo toque: deixa o sistema virar o eixo em tecla, o que o tira desse modo.
            if(root.isInTouchMode)return false
            if(!navReady(180))return true
            if(focused is ListView) { focused.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN,moveCode));focused.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_UP,moveCode));return true }
            padNavigate(root,moveCode)
            return true
        }
        return false
    }

    private var awaitingResult=false
    private lateinit var pageRoot:LinearLayout
    private fun message(raw:String) { Toast.makeText(this,raw,Toast.LENGTH_LONG).show() }
    private fun render() {}
    private fun details(game:Game) {}
    private fun maybeFinish() { queueHandler.postDelayed({ if(!keepOpen && !isFinishing && !isDestroyed && dialog==null && !awaitingResult)finish() },350) }
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState);store=LibraryStore(this)
        window.statusBarColor=appBackground;window.navigationBarColor=appBackground
        pageRoot=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setBackgroundColor(appBackground);gravity=Gravity.CENTER;addView(text("Abrindo…",18f)) }
        setContentView(pageRoot);catalog=store.cached();reloadLocal { dispatch(intent) }
    }
    override fun onNewIntent(intent:Intent) { super.onNewIntent(intent);setIntent(intent);reloadLocal { dispatch(intent) } }
    override fun onDestroy() { queueHandler.removeCallbacksAndMessages(null);work.shutdown();images.shutdown();runCatching { store.closeJournal() };super.onDestroy() }
    private fun reloadLocal(after:(()->Unit)?=null) {
        work.execute {
            val loaded=store.loadGames(catalog)
            val saves=runCatching { val sync=FileSync(store);if(sync.retroarchTree()==null)emptyMap() else listOf("retro-saves","retro-states").flatMap { sync.local(it).keys }.groupBy({ it.substringBefore('/') },{ it.substringAfter('/') }) }.getOrDefault(emptyMap())
            runOnUiThread { games=loaded.games;saveNames=saves;localProblems=loaded.problems;localScanAt=System.currentTimeMillis();updateLocalStatus?.invoke();after?.invoke() }
        }
    }
    /** O que a casca pediu: uma tela (EXTRA_SCREEN) ou uma ação de um jogo (EXTRA_GAME + EXTRA_ACTION: Texturas HD e saves de PSP/3DS). */
    private fun dispatch(intent:Intent?) {
        val screen=intent?.getStringExtra(EXTRA_SCREEN);val key=intent?.getStringExtra(EXTRA_GAME);val action=GameAction.of(intent?.getStringExtra(EXTRA_ACTION))
        intent?.removeExtra(EXTRA_SCREEN);intent?.removeExtra(EXTRA_GAME);intent?.removeExtra(EXTRA_ACTION)
        when {
            screen!=null -> when(screen) {
                "space" -> spaceManager();"trash" -> romTrash();"sync-files" -> syncFiles();"cloud-saves" -> cloudSaves();"organize" -> organizeRoms();"textures" -> textures()
                "index" -> cloudMenu();"playlists" -> playlists();"folders" -> folderStatuses();"apps" -> connectionApps();"pending" -> pendingChanges();"downloads" -> downloads()
                else -> if(!keepOpen)finish()
            }
            key!=null && action!=null -> { val game=games.firstOrNull { it.key==key } ?: return if(keepOpen)Unit else finish()
                when(action) { GameAction.TEXTURES -> textures(game);GameAction.SAVES -> gameSaves(game);else -> finish() } }
            else -> if(!keepOpen)finish()
        }
    }
    @Deprecated("Compatibilidade com Activity sem dependências extras")
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(requestCode,resultCode,data);awaitingResult=false
        try {
            if(resultCode!=RESULT_OK || data==null)return
            if(requestCode in listOf(14,15)) {
                val code=store.prefs.getString("index-picking",null) ?: return
                val uris=if(data.clipData!=null)(0 until data.clipData!!.itemCount).map { data.clipData!!.getItemAt(it).uri } else listOfNotNull(data.data)
                if(uris.isEmpty())return
                runCatching {
                    uris.forEach { contentResolver.takePersistableUriPermission(it,Intent.FLAG_GRANT_READ_URI_PERMISSION) }
                    val sources=CloudIndex(store).sources(code);val seen=(0 until sources.length()).map { sources.getJSONObject(it).getString("uri") }.toMutableSet()
                    uris.forEach { if(seen.add(it.toString()))sources.put(JSONObject().put("uri",it.toString()).put("tree",requestCode==15)) }
                    analyzeCloud(code,sources)
                }.onFailure(::failure);return
            }
            val uri=data.data ?: return
            if(requestCode==10) {
                runCatching { if(data.flags and Intent.FLAG_GRANT_WRITE_URI_PERMISSION!=0)contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION) else contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION) }
                    .onFailure { message("Permissão temporária: pode ser necessário selecionar o arquivo novamente após reiniciar.") }
                store.saveTree(pickingCode,uri);reloadLocal();return
            }
            if(requestCode==13) {
                runCatching {
                    require(data.flags and Intent.FLAG_GRANT_WRITE_URI_PERMISSION!=0) { "A pasta precisa permitir leitura e escrita." }
                    contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                    FileSync(store).setTree(syncPicking,uri);message("Pasta de sincronização definida. Analise antes de copiar.");syncFiles()
                }.onFailure(::failure);return
            }
            if(requestCode==12) {
                val name=store.displayName(uri)
                if(name.substringAfterLast('.').lowercase() !in setOf("zip","7z","rar")) { message("Escolha ZIP, 7z ou RAR.");return }
                val code=textureCode;val id=textureId
                runCatching { contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION) }
                show(AlertDialog.Builder(this).setTitle("Instalar pacote local?").setMessage("$name\n$code · $id\nFeche o emulador. Texturas diferentes existentes não serão substituídas.").setNegativeButton("Cancelar",null).setPositiveButton("Instalar") { _,_ -> runTexture { progress -> TextureStore(store).local(uri,code,id,progress) } })
            }
        } finally { maybeFinish() }
    }
    override fun startActivityForResult(intent:Intent,requestCode:Int) { awaitingResult=true;super.startActivityForResult(intent,requestCode) }
}
