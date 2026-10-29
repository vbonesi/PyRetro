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

class MainActivity:Activity(),InputManager.InputDeviceListener {
    companion object {
        /** Catálogo e progresso atualizam sozinhos quando o notebook responde; a instrumentação desliga. */
        @Volatile var automaticUpdates=true
        private val COLLECTIONS=listOf("home" to "Início","cell" to "Neste celular","catalog" to "Catálogo","favorites" to "Favoritos","ranking" to "Ranking","wishlist" to "Desejados","kept" to "Fixados","stream" to "Stream")
    }
    private lateinit var store:LibraryStore
    private lateinit var pageRoot:LinearLayout
    private lateinit var grid:GridLayout
    private lateinit var search:EditText
    private lateinit var status:TextView
    private lateinit var counter:TextView
    private lateinit var pagingBar:View
    private lateinit var drawShortcut:Button
    private lateinit var statsShortcut:Button
    private val extras by lazy { NotebookExtras(store,filesDir) }
    private val drive by lazy { GoogleDrive(this,store.prefs) }
    /** Jogo que esperava a conta Google ser conectada para baixar do Drive. */
    private var driveAfterConsent:Game?=null
    /** Desejados como cartões (chave "wish:…"); vêm do cache e se atualizam com o notebook online. */
    private var wishGames=emptyList<Game>()
    private var wishItems=emptyMap<String,WishItem>()
    private lateinit var statusButton:Button
    private lateinit var filterButton:Button
    private var filterPlatform=""
    private var filterGenre=""
    private lateinit var headingBar:View
    private lateinit var titleView:TextView
    private val collectionButtons=linkedMapOf<String,Button>()
    private lateinit var gridScroll:ScrollView
    private lateinit var controlHint:TextView
    private lateinit var previousPage:Button
    private lateinit var nextPage:Button
    private lateinit var searchToggle:Button
    private var glyphFamily="generic"
    private var renderedCollection=""
    private var lastDrawKey:String?=null
    private lateinit var controllerManager:InputManager
    private val work=Executors.newSingleThreadExecutor()
    private val images=Executors.newFixedThreadPool(2)
    private val prefetch=Executors.newSingleThreadExecutor()
    private var lastAutomaticUpdate=0L
    private var catalog=emptyList<Game>()
    private var games=emptyList<Game>()
    private var localProblems=emptyList<String>()
    private var localScanAt=0L
    private var updateLocalStatus:(()->Unit)?=null
    private var updateQueueStatus:(()->Unit)?=null
    private lateinit var queueBanner:Button
    private var seenQueueRevision=Long.MIN_VALUE
    private var seenQueueCompletion=0L
    private var restorePosition=true
    private var restoredScroll=0
    private var restoredPage:Int?=null
    private var lastSelectedKey:String?=null
    private var expandedTrackingKey:String?=null
    private val queueHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private fun queue()=DownloadQueue.get(store)
    private val queueTick=object:Runnable {
        override fun run() {
            if(isFinishing || isDestroyed)return
            runCatching {
                val helper=queue()
                if(seenQueueRevision!=helper.revision) {
                    seenQueueRevision=helper.revision
                    val rows=helper.snapshot();val active=rows.firstOrNull { it.state==DownloadState.RUNNING }
                    queueBanner.visibility=if(rows.any { it.state!=DownloadState.DONE })View.VISIBLE else View.GONE
                    queueBanner.text=if(active!=null)"↓ ${active.game.name} · ${bytesLabel(active.bytes)}" else "Downloads · ${rows.count { it.state!=DownloadState.DONE }} pendente(s) · abrir fila"
                    for(row in rows)downloadBadges[row.game.key]?.let { badge -> badge.text=coloredBadges(row.game,row.takeIf { it.state!=DownloadState.DONE });badge.visibility=if(badge.text.isEmpty())View.GONE else View.VISIBLE }
                    updateQueueStatus?.invoke();refreshStatusButton()
                }
                if(helper.completedAt>seenQueueCompletion) {
                    seenQueueCompletion=helper.completedAt;reloadLocal { message("Download concluído. Escolha Jogar quando quiser abrir o jogo.") }
                }
            }.onFailure { queueBanner.visibility=View.VISIBLE;queueBanner.text="Fila indisponível · abrir Downloads para conferir" }
            queueHandler.postDelayed(this,500)
        }
    }
    private fun bytesLabel(value:Long)=android.text.format.Formatter.formatFileSize(this,value)
    private var collection="home"
    /** Saves/estados do RetroArch no celular por sistema (nomes de arquivo), lidos junto com as pastas. */
    private var saveNames:Map<String,List<String>> = emptyMap()
    /** Selo de download de cada cartão visível, atualizado pela fila sem redesenhar a grade. */
    private val downloadBadges=mutableMapOf<String,TextView>()
    private var cardQueue:List<QueuedDownload> = emptyList()
    private var page=0
    private var pageCount=1
    private var dialog:AlertDialog?=null
    private var pickingCode="NDS"
    private var syncPicking="retroarch"
    private var pickingGame:Game?=null
    private var pickingCloud=false
    private var textureCode="PSP"
    private var textureId=""
    private var downloadAfterFolder:Game?=null
    private var activeGame:Game?=null
    private var launchedAt=0L
    private var leftForGame=false
    private var scanOnResume=false
    private var lastMotion=0L
    private var lastCollectionAt=0L
    private var lastProbeAt=0L
    private var networkCallback:ConnectivityManager.NetworkCallback?=null
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
    private fun message(value:String) {
        status.text=value
        val notice=value.startsWith("Offline") || value.startsWith("Modo offline") || value.startsWith("Online ·")
        status.visibility=if(notice && (resources.configuration.orientation==2 || !store.prefs.getBoolean("ui:show-notice",true)))View.GONE else View.VISIBLE
    }
    private fun failure(error:Throwable) { message(error.message ?: "Não foi possível concluir.") }
    private fun firstEnabledButton(view:View):Button? {
        if(view.visibility!=View.VISIBLE)return null
        if(view is Button && view.isEnabled)return view
        if(view is ViewGroup)for(index in 0 until view.childCount)firstEnabledButton(view.getChildAt(index))?.let { return it }
        return null
    }
    private fun show(builder:AlertDialog.Builder):AlertDialog {
        dialog?.dismiss();return builder.create().also { opened ->
            dialog=opened;opened.setOnDismissListener { if(dialog===opened) { dialog=null;updateLocalStatus=null;updateQueueStatus=null } }
            opened.setOnKeyListener { _,code,event ->
                when(code) {
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
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState);store=LibraryStore(this)
        collection=store.prefs.getString("ui:collection","home").takeIf { it in COLLECTIONS.map { c -> c.first } } ?: "home"
        filterPlatform=store.prefs.getString("ui:filter:$collection:platform","").orEmpty();filterGenre=store.prefs.getString("ui:filter:$collection:genre","").orEmpty()
        page=store.prefs.getInt("ui:page",0).coerceAtLeast(0);restoredScroll=store.prefs.getInt("ui:scroll",0).coerceAtLeast(0)
        restoredPage=page
        lastSelectedKey=store.prefs.getString("ui:selected",null)
        window.statusBarColor=appBackground;window.navigationBarColor=appBackground
        pageRoot=column().apply { setBackgroundColor(appBackground) }
        pageRoot.setOnApplyWindowInsetsListener { view,insets ->
            if(Build.VERSION.SDK_INT>=30) {
                val safe=insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout() or WindowInsets.Type.ime())
                view.setPadding(dp(12)+safe.left,dp(8)+safe.top,dp(12)+safe.right,dp(8)+safe.bottom)
            } else view.setPadding(dp(12)+insets.systemWindowInsetLeft,dp(8)+insets.systemWindowInsetTop,dp(12)+insets.systemWindowInsetRight,dp(8)+insets.systemWindowInsetBottom)
            insets
        }
        // Um só lugar para Situação e Opções, nas duas orientações; a barra abaixo é só de coleções.
        val heading=row();heading.addView(ImageView(this).apply { setImageResource(R.drawable.ic_pyretro);contentDescription=null;scaleType=ImageView.ScaleType.FIT_CENTER },LinearLayout.LayoutParams(dp(32),dp(32)))
        titleView=text("PyRetro",25f).apply { setTypeface(null,Typeface.BOLD) };add(heading,titleView,1f);statusButton=button("Situação") { statusCenter() };add(heading,statusButton);add(heading,button("Opções") { settings() });pageRoot.addView(heading);headingBar=heading
        val collections=row()
        for((id,label) in COLLECTIONS)add(collections,button(label) { selectCollection(id) }.also { tab -> collectionButtons[id]=tab;tab.setOnFocusChangeListener { _,focused -> tab.background=shape(collection==id,focused) } })
        horizontal(pageRoot,collections)
        drawShortcut=button("🎲 Sortear") { draw() };add(collections,drawShortcut)
        statsShortcut=button("📊 Estatísticas") { statsDialog() };add(collections,statsShortcut)
        search=EditText(this).apply { hint="Y · Pesquisar nome, plataforma ou gênero";setHintTextColor(Color.LTGRAY);setTextColor(appForeground);isSingleLine=true;minHeight=dp(48);background=shape();setPadding(dp(12),0,dp(12),0);setText(store.prefs.getString("ui:query","")!!.take(256)) }
        search.addTextChangedListener(object:TextWatcher { override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){};override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){page=0;render()};override fun afterTextChanged(s:Editable?){} })
        // Filtro por plataforma/gênero ao lado da busca; vale para a coleção aberta.
        val searchRow=row();searchRow.addView(search,LinearLayout.LayoutParams(0,dp(52),1f))
        searchToggle=button("⌕ Buscar") { store.prefs.edit().putBoolean("ui:search-open",true).apply();render();search.requestFocus();(getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager).showSoftInput(search,InputMethodManager.SHOW_IMPLICIT) };add(searchRow,searchToggle)
        filterButton=button("Filtro") { filterDialog() };add(searchRow,filterButton);pageRoot.addView(searchRow,LinearLayout.LayoutParams(-1,-2))
        status=text("Modo offline · selecione suas pastas ou carregue o catálogo do notebook.",13f);pageRoot.addView(status)
        queueBanner=button("Downloads") { downloads() }.apply { textSize=13f;maxLines=2;visibility=View.GONE };pageRoot.addView(queueBanner,LinearLayout.LayoutParams(-1,-2))
        seenQueueCompletion=runCatching { queue().completedAt }.getOrDefault(0L)
        grid=GridLayout(this).apply { alignmentMode=GridLayout.ALIGN_BOUNDS }
        gridScroll=ScrollView(this).apply { isFillViewport=true;addView(grid) };pageRoot.addView(gridScroll,LinearLayout.LayoutParams(-1,0,1f))
        val paging=row();previousPage=button("LB · Anterior") { changePage(-1) }.apply { minWidth=0 };add(paging,previousPage);counter=text("",13f);add(paging,counter,1f);nextPage=button("Próxima · RB") { changePage(1) }.apply { minWidth=0 };add(paging,nextPage);pageRoot.addView(paging);pagingBar=paging
        controlHint=text("Galileo G8: direcional/analógico · A abrir · B voltar · X favorito · Y buscar · Menu opções",11f);pageRoot.addView(controlHint)
        setContentView(pageRoot);adaptLayout();catalog=store.cached();if(catalog.isNotEmpty())message("Offline · catálogo em cache. Jogos locais disponíveis sem o notebook.");reloadLocal();probeNotebook()
        if(collection=="wishlist")loadWishlist()
        // Ligar o Tailscale (VPN) troca a rede padrão: sonda de novo sem esperar o usuário sair e voltar.
        networkCallback=object:ConnectivityManager.NetworkCallback() { override fun onAvailable(network:Network) { queueHandler.postDelayed({ if(!isFinishing && !isDestroyed)probeNotebook(force=true) },2_000) } }
        runCatching { (getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager).registerDefaultNetworkCallback(networkCallback!!) }
        controllerManager=getSystemService(INPUT_SERVICE) as InputManager;controllerManager.registerInputDeviceListener(this,null);updateControllerOrientation();updateGlyphs()
    }
    private fun updateControllerOrientation() {
        val present=InputDevice.getDeviceIds().asSequence().mapNotNull { InputDevice.getDevice(it) }.any { !it.isVirtual && (it.supportsSource(InputDevice.SOURCE_GAMEPAD) || it.supportsSource(InputDevice.SOURCE_JOYSTICK)) }
        val orientation=if(present)ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE else ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        if(requestedOrientation!=orientation)requestedOrientation=orientation
        if(::search.isInitialized)updateGlyphs()
    }
    private fun glyph(key:String)=GlyphRules.key(glyphFamily,key)
    private fun updateGlyphs() {
        val names=InputDevice.getDeviceIds().asSequence().mapNotNull { InputDevice.getDevice(it) }.filter { !it.isVirtual && it.supportsSource(InputDevice.SOURCE_GAMEPAD) }.map { it.name }.toList()
        glyphFamily=GlyphRules.family(store.prefs.getString("ui:glyphs","auto").orEmpty(),names)
        search.hint="${glyph("Y")} · Pesquisar nome, plataforma ou gênero"
        previousPage.text="${glyph("LB")} · Anterior";nextPage.text="Próxima · ${glyph("RB")}"
        controlHint.text="${glyph("A")} abrir · ${glyph("B")} voltar · ${glyph("X")} favorito · ${glyph("Y")} buscar · ${glyph("Menu")} opções"
    }
    override fun onInputDeviceAdded(deviceId:Int)=updateControllerOrientation()
    override fun onInputDeviceRemoved(deviceId:Int)=updateControllerOrientation()
    override fun onInputDeviceChanged(deviceId:Int)=updateControllerOrientation()
    override fun onDestroy() { networkCallback?.let { callback -> runCatching { (getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager).unregisterNetworkCallback(callback) } };queueHandler.removeCallbacks(queueTick);updateQueueStatus=null;updateLocalStatus=null;if(::controllerManager.isInitialized)controllerManager.unregisterInputDeviceListener(this);super.onDestroy() }
    private fun reloadLocal(after:(()->Unit)?=null) {
        work.execute {
            val problems=mutableListOf<String>()
            val roms=store.folders.keys.flatMap { code -> runCatching { store.files(code) }.getOrElse { problems.add(store.folders.getValue(code));emptyList() } }
            val all=store.bind(catalog,roms)
            val saves=runCatching { val sync=FileSync(store);if(sync.retroarchTree()==null)emptyMap() else listOf("retro-saves","retro-states").flatMap { sync.local(it).keys }.groupBy({ it.substringBefore('/') },{ it.substringAfter('/') }) }.getOrDefault(emptyMap())
            runOnUiThread { games=all;saveNames=saves;localProblems=problems;localScanAt=System.currentTimeMillis();render();updateLocalStatus?.invoke();after?.invoke() }
        }
    }
    private fun render() {
        if(!::grid.isInitialized)return
        for((id,tab) in collectionButtons)tab.background=shape(id==collection,tab.hasFocus())
        if(renderedCollection!=collection) { renderedCollection=collection;collectionButtons[collection]?.let { tab -> tab.post { (tab.parent?.parent as? HorizontalScrollView)?.smoothScrollTo((tab.left-dp(16)).coerceAtLeast(0),0) } } }
        val streaming=collection=="stream"
        val compactSearch=resources.configuration.orientation==2 && search.text.isBlank() && !store.prefs.getBoolean("ui:search-open",false)
        search.visibility=if(streaming || compactSearch)View.GONE else View.VISIBLE
        searchToggle.visibility=if(!streaming && compactSearch)View.VISIBLE else View.GONE
        filterButton.visibility=if(streaming)View.GONE else View.VISIBLE
        refreshStatusButton()
        pagingBar.visibility=if(streaming)View.GONE else View.VISIBLE
        drawShortcut.visibility=if(streaming)View.GONE else View.VISIBLE
        statsShortcut.visibility=drawShortcut.visibility
        controlHint.visibility=if(streaming || resources.configuration.orientation==2 || !store.prefs.getBoolean("ui:show-hint",true))View.GONE else View.VISIBLE
        if(streaming) { renderStream();return }
        val home=collection=="home" && search.text.isBlank()
        pagingBar.visibility=if(home)View.GONE else View.VISIBLE
        filterButton.visibility=if(home || streaming)View.GONE else View.VISIBLE
        if(home) { renderHome();return }
        val focusedKey=if(restorePosition)lastSelectedKey else (currentFocus?.tag as? Game)?.key
        val query=GameLogic.normalized(search.text.toString())
        val base=collectionGames().filter { query.isBlank() || GameLogic.normalized(it.name+it.platform+it.genre).contains(query) }
        val entries=gridEntries(base)
        val ordered=if(collection=="ranking") { val byKey=base.associateBy { it.key };GridRules.ranking(entries).mapNotNull(byKey::get) } else base
        val allowed=GridRules.filter(entries,filterPlatform,filterGenre).map { it.key }.toSet()
        val visible=ordered.filter { it.key in allowed }
        filterButton.text=listOf(filterPlatform,filterGenre).filter { it.isNotBlank() }.joinToString(" · ").ifBlank { "Filtro" }.let { if(it=="Filtro") it else "Filtro: $it" }
        filterButton.background=shape(filterPlatform.isNotBlank() || filterGenre.isNotBlank(),filterButton.hasFocus())
        val podium=if(collection=="ranking")visible.take(3) else emptyList()
        val listed=visible.drop(podium.size)
        val count=((listed.size+23)/24).coerceAtLeast(1);pageCount=count;page=page.coerceIn(0,count-1);counter.text="${page+1}/$count · ${visible.size} jogos"
        pagingBar.visibility=if(count>1)View.VISIBLE else View.GONE
        if(restorePosition && localScanAt>0 && restoredPage!=null) { page=restoredPage!!.coerceIn(0,count-1);counter.text="${page+1}/$count · ${visible.size} jogos" }
        val compact=resources.configuration.orientation==2
        grid.removeAllViews();downloadBadges.clear();cardQueue=runCatching { queue().snapshot() }.getOrDefault(emptyList());val width=resources.displayMetrics.widthPixels/resources.displayMetrics.density
        val columns=if(width>=900)4 else if(width>=600)3 else 2;grid.columnCount=columns
        if(podium.isNotEmpty() && page==0) {
            grid.addView(text("Top 3 desta seleção",18f).apply { setTypeface(null,Typeface.BOLD) },GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED,1),GridLayout.spec(0,columns)).apply { this.width=-1 })
            val wide=compact && width>=600
            val row=LinearLayout(this).apply { orientation=if(wide)LinearLayout.HORIZONTAL else LinearLayout.VERTICAL }
            val byKey=podium.associateBy { it.key }
            for(key in GridRules.podiumOrder(podium.map { it.key },wide))row.addView(gameCard(byKey.getValue(key),wide),LinearLayout.LayoutParams(if(wide)0 else -1,-2,if(!wide)0f else if(key==podium.first().key)1.2f else 1f).apply { setMargins(dp(4),dp(4),dp(4),dp(4)) })
            grid.addView(row,GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED,1),GridLayout.spec(0,columns)).apply { this.width=-1 })
            GridRules.tieNote(visible.map { g -> entries.first { it.key==g.key } })?.let { grid.addView(text(it,12f),GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED,1),GridLayout.spec(0,columns)).apply { this.width=-1 }) }
        }
        for(game in listed.drop(page*24).take(24)) {
            val params=GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED),GridLayout.spec(GridLayout.UNDEFINED,1f)).apply { this.width=0;setMargins(dp(4),dp(4),dp(4),dp(4)) };grid.addView(gameCard(game,compact),params)
        }
        if(visible.isEmpty() && base.isNotEmpty() && (filterPlatform.isNotBlank() || filterGenre.isNotBlank()))grid.addView(text("Nenhum jogo com este filtro. Toque em Filtro para limpar.",17f))
        else if(visible.isEmpty())grid.addView(text(when(collection) { "cell" -> "Escolha a pasta Jogos em Opções. Jogos do Catálogo podem ser baixados direto pela ficha do jogo.";"kept" -> "Fixe jogos nos detalhes para encontrá-los aqui e proteger as ROMs contra remoção.";"wishlist" -> if(store.online)"Nenhum jogo nos Desejados." else "Os Desejados vêm do notebook. Conecte uma vez (Tailscale ligado) e eles ficam guardados para ver offline.";"ranking" -> "Dê nota aos jogos da Biblioteca em Progresso e tempo, na ficha. O ranking mostra a maior nota primeiro.";else -> "Carregue o catálogo uma vez ou marque seus favoritos. Sem conexão, o cache continua disponível." },17f))
        if(focusedKey!=null) {
            val next=(0 until grid.childCount).map { grid.getChildAt(it) }.firstOrNull { (it.tag as? Game)?.key==focusedKey } ?: grid.getChildAt(0)
            next?.requestFocus()
        }
        if(restorePosition && localScanAt>0) { restorePosition=false;restoredPage=null;gridScroll.post { gridScroll.scrollTo(0,restoredScroll) } }
    }
    private fun gameCard(game:Game,compact:Boolean):LinearLayout {
        val card=column().apply { isFocusable=true;isClickable=true;descendantFocusability=ViewGroup.FOCUS_BLOCK_DESCENDANTS;tag=game;background=shape();setOnClickListener { details(game) };setOnFocusChangeListener { _,focused -> background=shape(focused=focused) } }
        if(compact)card.setPadding(dp(8),dp(4),dp(8),dp(4))
        val cover=ImageView(this).apply { setImageResource(com.pyretro.app.R.drawable.ic_pyretro);scaleType=ImageView.ScaleType.FIT_CENTER;contentDescription=game.name }
        card.addView(cover,LinearLayout.LayoutParams(-1,dp(if(compact)70 else 150)))
        card.addView(text((if(store.prefs.getBoolean("favorite:${game.key}",false))"★ " else "")+game.name,16f).apply { maxLines=2;ellipsize=android.text.TextUtils.TruncateAt.END;setTypeface(null,Typeface.BOLD) })
        val meta=text((if(compact)store.folders[game.code] ?: game.platform else game.platform)+" · "+where(game),12f).apply { maxLines=if(compact)1 else 2;ellipsize=android.text.TextUtils.TruncateAt.END }
        card.addView(LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL;gravity=android.view.Gravity.CENTER_VERTICAL
            addView(platformChip(game.code,game.platform),LinearLayout.LayoutParams(-2,-2).apply { setMargins(dp(4),0,0,0) });addView(meta,LinearLayout.LayoutParams(0,-2,1f)) })
        val badges=text(coloredBadges(game),12f).apply { maxLines=3;setTextColor(Color.rgb(140,220,200));visibility=if(text.isEmpty())View.GONE else View.VISIBLE }
        card.addView(badges);downloadBadges[game.key]=badges
        images.execute { val file=runCatching { store.cover(game) }.getOrNull();if(file!=null) { val bitmap=BitmapFactory.decodeFile(file.path,BitmapFactory.Options().apply { inSampleSize=2 });if(bitmap!=null)runOnUiThread { cover.setImageBitmap(bitmap) } } }
        return card
    }
    /** Selos do cartão: progresso, nota, tempo no celular, save e download em andamento. */
    /** Os mesmos selos, com a nota na cor da escala comum (dourada no 11). */
    private fun coloredBadges(game:Game,download:QueuedDownload?=null):CharSequence {
        val plain=badges(game,download);val nota=TrackingRules.value(store.tracking(game),"nota") as Double?
        val color=NotaRules.color(nota) ?: return plain
        val label=NotaRules.symbol(nota)+" "+TrackingRules.label(nota);val at=plain.indexOf(label)
        if(at<0)return plain
        return android.text.SpannableString(plain).apply { setSpan(android.text.style.ForegroundColorSpan(color),at,at+label.length,android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE) }
    }
    private fun badges(game:Game,download:QueuedDownload?=null):String {
        val tracking=store.tracking(game);val minutes=store.prefs.getLong("time:${game.key}",0)/60
        val label=game.romName.substringAfterLast('/').let { SaveRules.label(it,store.extensionsFor(game.code)) }
        val saved=game.localUri!=null && saveNames[game.code].orEmpty().any { SaveRules.belongs("${game.code}/$it",game.code,label) }
        val row=download ?: cardQueue.firstOrNull { it.game.key==game.key && it.state!=DownloadState.DONE }
        return listOfNotNull(
            when { tracking.optBoolean("platinado") -> "🏆";tracking.optBoolean("finalizado") -> "✓ Finalizado";tracking.optBoolean("iniciado") -> "▶ Jogando";else -> null },
            (TrackingRules.value(tracking,"nota") as Double?)?.let { NotaRules.symbol(it)+" "+TrackingRules.label(it) },
            minutes.takeIf { it>0 }?.let { if(it>=60)"⏱ ${it/60}h${"%02d".format(it%60)}" else "⏱ ${it}min" },
            "💾".takeIf { saved },
            row?.let { when(it.state) { DownloadState.FAILED -> "⬇ falhou";DownloadState.PAUSED -> "⬇ pausado";else -> "⬇ "+(it.total?.takeIf { t -> t>0 }?.let { t -> "${it.bytes*100/t}%" } ?: bytesLabel(it.bytes)) } }
        ).joinToString(" · ")
    }
    /** Início: fileiras horizontais com o que faz sentido abrir agora. Pesquisar mostra a grade do catálogo. */
    private fun renderHome() {
        val focusedKey=if(restorePosition)lastSelectedKey else (currentFocus?.tag as? Game)?.key
        page=0;pageCount=1;grid.removeAllViews();downloadBadges.clear();cardQueue=runCatching { queue().snapshot() }.getOrDefault(emptyList());grid.columnCount=1
        val byKey=games.associateBy { it.key }
        val entries=games.map { game -> val tracking=store.tracking(game)
            HomeEntry(game.key,game.name,game.localUri!=null,tracking.optBoolean("iniciado"),tracking.optBoolean("finalizado"),
                store.prefs.getBoolean("favorite:${game.key}",false),store.prefs.getLong("played:${game.key}",0),store.prefs.getLong("time:${game.key}",0)) }
        val compact=resources.configuration.orientation==2
        val box=column()
        for((title,keys) in HomeRules.rows(entries)) {
            box.addView(text(title,18f).apply { setTypeface(null,Typeface.BOLD);setPadding(dp(4),dp(10),dp(4),dp(2)) })
            val line=row()
            for(key in keys)byKey[key]?.let { game -> line.addView(gameCard(game,compact),LinearLayout.LayoutParams(dp(if(compact)150 else 170),-2).apply { setMargins(dp(4),dp(4),dp(4),dp(4)) }) }
            box.addView(HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled=false;addView(line) },LinearLayout.LayoutParams(-1,-2))
        }
        if(box.childCount==0)box.addView(text("Escolha a pasta Jogos em Opções ou carregue o catálogo. Jogos iniciados, abertos por aqui e favoritos aparecem em fileiras.",17f))
        grid.addView(box,GridLayout.LayoutParams().apply { width=ViewGroup.LayoutParams.MATCH_PARENT })
        val cards=generateSequence(listOf<View>(box)) { level -> level.flatMap { v -> if(v is ViewGroup)(0 until v.childCount).map(v::getChildAt) else emptyList() }.takeIf { it.isNotEmpty() } }.flatten().filter { it.tag is Game }.toList()
        counter.text="${games.size} jogos"
        if(focusedKey!=null)(cards.firstOrNull { (it.tag as Game).key==focusedKey } ?: cards.firstOrNull())?.requestFocus()
        if(restorePosition && localScanAt>0) { restorePosition=false;restoredPage=null;gridScroll.post { gridScroll.scrollTo(0,restoredScroll) } }
    }
    private fun gridEntries(list:List<Game>)=list.map { GridEntry(it.key,it.name,it.platform,it.genre,TrackingRules.value(store.tracking(it),"nota") as Double?,it.id.ifBlank { it.key }) }
    private fun collectionGames():List<Game> {
        val pinned=if(collection=="kept")SpaceStore(store).pinnedChecker() else ({ _:Game -> false })
        return (if(collection=="wishlist")wishGames else games).filter { (collection!="cell" || it.localUri!=null) && (collection!="favorites" || store.prefs.getBoolean("favorite:${it.key}",false)) && (collection!="kept" || pinned(it)) && (collection!="ranking" || TrackingRules.value(store.tracking(it),"nota")!=null) }
    }
    /** Filtro da coleção aberta: plataformas e gêneros que existem nela. */
    private fun filterDialog() {
        val entries=gridEntries(collectionGames())
        val box=column();box.addView(text("Filtrar",23f))
        fun section(title:String,options:List<String>,all:String,current:String,choose:(String)->Unit) {
            box.addView(text(title,18f).apply { setTypeface(null,Typeface.BOLD) })
            val line=row();horizontal(box,line)
            for(option in listOf("")+options)add(line,button(option.ifBlank { all }) { choose(option);page=0;dialog?.dismiss();render() }.apply { background=shape(option==current);setOnFocusChangeListener { _,focused -> background=shape(option==current,focused) } })
        }
        section("Plataforma",GridRules.platforms(entries),"Todas",filterPlatform) { filterPlatform=it }
        section("Gênero",GridRules.genres(entries),"Qualquer",filterGenre) { filterGenre=it }
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun refreshStatusButton() {
        if(!::statusButton.isInitialized)return
        val failed=runCatching { queue().snapshot().count { it.state==DownloadState.FAILED } }.getOrDefault(0)
        val conflicts=0 // conflitos de saves agora são tratados na tela da nuvem
        statusButton.text=GridRules.statusLabel(GridRules.attention(store.pending(),failed,localProblems.size,conflicts))
    }
    // --- Desejados, Estatísticas, editar e capa (precisam do notebook; leitura fica em cache) ---
    private fun needsNotebook():Boolean { if(store.online)return true;message("Esta função precisa do notebook online. Ligue o Tailscale e tente de novo.");return false }
    private fun loadWishlist() {
        fun apply(items:List<WishItem>) { wishItems=items.associateBy(ExtrasRules::wishKey)
            wishGames=items.map { Game(it.id,ExtrasRules.wishKey(it),it.name,ExtrasRules.STORES.getValue(it.source),cover=it.cover,genre=it.genre) } }
        if(wishGames.isEmpty())apply(extras.wishlist(false))
        if(!store.online)return
        work.execute { runCatching { extras.wishlist(true) }.onSuccess { items -> runOnUiThread { apply(items);if(collection=="wishlist")render() } } }
    }
    private fun wishDetails(game:Game) {
        val item=wishItems[game.key] ?: return
        val box=column()
        val cover=ImageView(this).apply { scaleType=ImageView.ScaleType.FIT_CENTER;visibility=View.GONE }
        box.addView(cover,LinearLayout.LayoutParams(-1,dp(200)))
        images.execute { val bitmap=runCatching { store.cover(game) }.getOrNull()?.let { BitmapFactory.decodeFile(it.path) };if(bitmap!=null)runOnUiThread { cover.setImageBitmap(bitmap);cover.visibility=View.VISIBLE } }
        box.addView(text(item.name,22f).apply { setTypeface(null,Typeface.BOLD) })
        box.addView(text(listOf(ExtrasRules.STORES.getValue(item.source),item.genre).filter { it.isNotBlank() }.joinToString(" · ")+" · na sua lista de desejos",14f))
        val actions=row();horizontal(box,actions)
        fun leave(bought:Boolean) {
            if(!needsNotebook())return
            show(AlertDialog.Builder(this).setMessage(if(bought)"Marcar \"${item.name}\" como comprado? Sai dos Desejados e entra na Biblioteca." else "Tirar \"${item.name}\" da lista de desejos?")
                .setPositiveButton(if(bought)"Comprado" else "Tirar") { _,_ -> work.execute { runCatching { extras.leaveWishlist(item,bought) }.onSuccess { items -> runOnUiThread {
                    wishGames=wishGames.filter { it.key!=game.key };message(if(bought)"${item.name} entrou na Biblioteca." else "${item.name} saiu dos Desejados.");render()
                    if(bought)refreshCatalog(silent=true)
                } }.onFailure { runOnUiThread { failure(it) } } } }.setNegativeButton("Voltar",null))
        }
        add(actions,button("✅ Comprado") { leave(true) });add(actions,button("🗑 Tirar da lista") { leave(false) })
        box.addView(text("Para adicionar jogos aos Desejados, use o modo TV ou a interface do notebook.",12f))
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun statsDialog() {
        val box=column();box.addView(text("📊 Estatísticas",23f))
        val body=text(if(store.online)"Consultando o notebook…" else "",15f);box.addView(body)
        val actions=row();horizontal(box,actions)
        add(actions,button("Ranking") { dialog?.dismiss();selectCollection("ranking") });add(actions,button("Desejados") { dialog?.dismiss();selectCollection("wishlist") })
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
        var wishCount=extras.wishlist(false).size
        fun fill(stats:JSONObject?,fresh:Boolean) {
            if(dialog!==opened)return
            if(stats==null) { body.text="As estatísticas vêm do notebook. Conecte uma vez e elas ficam guardadas para ver offline.";return }
            val media=if(stats.isNull("nota_media"))"—" else "%.2f".format(java.util.Locale("pt","BR"),stats.getDouble("nota_media"))
            body.text=listOf("🎮 ${stats.getInt("total")} jogos na Biblioteca","▶ ${stats.getInt("jogando")} jogando agora","✓ ${stats.getInt("zerados")} finalizados · 🏆 ${stats.getInt("platinados")} platinados",
                "★ nota média $media · ${stats.getInt("com_nota")} com nota","◷ ${ExtrasRules.hours(stats.getDouble("tempo_total_horas"))} de jogo registrado","♡ $wishCount nos Desejados",
                if(fresh)"" else "Offline · dados de ${store.prefs.getLong("stats-at",0).takeIf { it>0 }?.let(::versionDate) ?: "—"}.").filter { it.isNotBlank() }.joinToString("\n")
        }
        fill(extras.stats(false),false)
        // Online: lê também os Desejados, para a contagem não depender de ter aberto a coleção antes.
        if(store.online)work.execute { val result=runCatching { extras.stats(true) };val wishes=runCatching { extras.wishlist(true).size }.getOrNull()
            runOnUiThread { if(wishes!=null)wishCount=wishes;result.onSuccess { fill(it,true) }.onFailure { fill(extras.stats(false),false) } } }
    }
    private fun editGame(game:Game) {
        if(!needsNotebook())return
        message("Lendo os dados de ${game.name}…")
        work.execute {
            val result=runCatching { extras.record(game.id) to extras.genres() }
            runOnUiThread { result.onFailure(::failure).onSuccess { (record,genres) ->
                if(record==null) { message("Este jogo não está mais na Biblioteca do notebook.");return@onSuccess }
                val fields=listOf("genero" to "Gênero","data_final" to "Data que finalizou (aaaa-mm-dd)","tempo" to "Tempo jogado (ex.: 31:40:00)","observacoes" to "Comentário")
                val before=fields.associate { (field,_) -> field to (record.optString(field).takeUnless { record.isNull(field) } ?: "") }
                val box=column();box.addView(text("✎ ${game.name}",21f).apply { setTypeface(null,Typeface.BOLD) })
                val options=(listOf("") + genres + listOf(before.getValue("genero"))).distinct()
                box.addView(text("Gênero",15f))
                val genre=Spinner(this).apply { adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,options.map { it.ifBlank { "Sem gênero" } });setSelection(options.indexOf(before.getValue("genero")).coerceAtLeast(0)) }
                box.addView(genre)
                val inputs=fields.drop(1).associate { (field,label) -> box.addView(text(label,15f))
                    field to EditText(this).apply { setText(before.getValue(field));setTextColor(appForeground);background=shape();setPadding(dp(12),dp(8),dp(12),dp(8));if(field=="observacoes") { minLines=3 } else isSingleLine=true }.also { box.addView(it,LinearLayout.LayoutParams(-1,-2)) } }
                show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null).setPositiveButton("Salvar") { _,_ ->
                    val after=mapOf("genero" to options[genre.selectedItemPosition])+inputs.mapValues { it.value.text.toString() }
                    val changes=ExtrasRules.changes(before,after)
                    if(changes.isEmpty()) { message("Nada alterado.");return@setPositiveButton }
                    work.execute { runCatching { extras.edit(game.id,changes) }.onSuccess { runOnUiThread { message("Dados de ${game.name} salvos no notebook.");refreshCatalog(silent=true) } }.onFailure { runOnUiThread { failure(it) } } }
                })
            } }
        }
    }
    private fun coverSearch(game:Game,target:CoverTarget) {
        if(!needsNotebook())return
        val box=column();box.addView(text("🖼 Capa de ${game.name}",21f).apply { setTypeface(null,Typeface.BOLD) })
        val query=EditText(this).apply { setText(game.name);setTextColor(appForeground);isSingleLine=true;background=shape();setPadding(dp(12),dp(8),dp(12),dp(8)) }
        box.addView(query,LinearLayout.LayoutParams(-1,-2))
        val status=text("",13f);val results=GridLayout(this).apply { columnCount=3 }
        lateinit var search:()->Unit
        // Só a busca mais recente desenha: resposta ou miniatura de uma busca anterior é descartada
        // (achado do Codex na revisão da 0.9.0: buscar de novo antes da resposta misturava as capas).
        val searches=LatestRequest()
        add(box,button("Buscar no SteamGridDB") { search() });box.addView(status);box.addView(results)
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
        search={
            val term=query.text.toString().trim()
            if(term.length>=2) {
                val current=searches.start()
                status.text="Buscando… o SteamGridDB pode levar até dois minutos.";results.removeAllViews()
                work.execute { val found=runCatching { extras.searchCovers(term) };runOnUiThread { if(dialog!==opened || !searches.isCurrent(current))return@runOnUiThread
                    found.onFailure { status.text=it.message ?: "Busca falhou." }.onSuccess { list ->
                        status.text=if(list.isEmpty())"Nada encontrado. Troque o termo." else "Toque numa capa para usar."
                        for((url,name) in list.take(12)) {
                            val image=ImageView(this).apply { scaleType=ImageView.ScaleType.FIT_CENTER;contentDescription=name;isFocusable=true;isClickable=true;background=shape();setPadding(dp(4),dp(4),dp(4),dp(4))
                                setOnFocusChangeListener { _,focused -> background=shape(focused) }
                                setOnClickListener { show(AlertDialog.Builder(this@MainActivity).setMessage("Usar esta capa para ${game.name}? A capa atual no notebook é substituída.").setNegativeButton("Voltar",null).setPositiveButton("Usar") { _,_ ->
                                    message("Aplicando a capa…")
                                    work.execute { runCatching { extras.applyCover(target,url) }.onSuccess { runOnUiThread { message("Capa trocada. Atualizando o catálogo…");refreshCatalog(silent=true) } }.onFailure { runOnUiThread { failure(it) } } }
                                }) } }
                            results.addView(image,GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED),GridLayout.spec(GridLayout.UNDEFINED,1f)).apply { width=0;height=dp(170);setMargins(dp(3),dp(3),dp(3),dp(3)) })
                            images.execute { if(searches.isCurrent(current)) { val bitmap=runCatching { extras.thumbnail(url) }.getOrNull();if(bitmap!=null)runOnUiThread { if(searches.isCurrent(current))image.setImageBitmap(bitmap) } } }
                        }
                    } } }
            }
        }
        search()
    }
    private fun selectCollection(id:String) {
        if(id!=collection) {
            store.prefs.edit().putString("ui:filter:$collection:platform",filterPlatform).putString("ui:filter:$collection:genre",filterGenre).apply()
            filterPlatform=store.prefs.getString("ui:filter:$id:platform","").orEmpty();filterGenre=store.prefs.getString("ui:filter:$id:genre","").orEmpty()
        }
        if(id=="wishlist")loadWishlist()
        collection=id;page=0;restorePosition=false;restoredPage=null;render();gridScroll.scrollTo(0,0)
    }
    private fun renderStream() {
        page=0;pageCount=1;grid.removeAllViews();grid.columnCount=1
        val box=column();box.addView(text("Stream",23f))
        val clients=listOf(
            Triple("Xbox · XBXPlay","com.grill.xbxplay","Conecte ao seu Xbox pelo XBXPlay."),
            Triple("PS4 · Remote Play","com.playstation.remoteplay","Conecte ao seu PS4 pelo aplicativo oficial."),
            Triple("PC e Switch · Moonlight","com.limelight","Escolha o notebook no Moonlight. O vídeo do Switch passa pelo notebook.")
        )
        for((label,target,description) in clients) {
            box.addView(platformChip(if(target=="com.grill.xbxplay")"Xbox Series S" else if(target=="com.playstation.remoteplay")"PlayStation 4" else "PC"))
            val installed=packageManager.getLaunchIntentForPackage(target)!=null
            box.addView(button(label+(if(installed)"" else " · não encontrado")) { openPackage(target) }.apply { isEnabled=installed;alpha=if(installed)1f else .55f },LinearLayout.LayoutParams(-1,-2).apply { setMargins(dp(3),dp(3),dp(3),dp(3)) })
            box.addView(text(description,14f))
        }
        help(box,"Conexões e jogos","Login, pareamento e escolha do console/computador ficam nos clientes. Para solicitar um jogo ou transmissão ao notebook, use a ação nos detalhes do título. Abrir esta aba não liga consoles nem inicia transmissão.")
        grid.addView(box,GridLayout.LayoutParams().apply { width=ViewGroup.LayoutParams.MATCH_PARENT })
        if(restorePosition && localScanAt>0) { restorePosition=false;restoredPage=null;gridScroll.post { gridScroll.scrollTo(0,restoredScroll) } }
    }
    private fun changePage(delta:Int) {
        val next=(page+delta).coerceIn(0,pageCount-1)
        if(next!=page) { page=next;render();gridScroll.scrollTo(0,0);grid.getChildAt(0)?.requestFocus() }
        else {
            val top=(gridScroll.scrollY+delta*gridScroll.height*4/5).coerceIn(0,(grid.height-gridScroll.height).coerceAtLeast(0))
            gridScroll.scrollTo(0,top)
            (0 until grid.childCount).map { grid.getChildAt(it) }.firstOrNull { it.top>=top && it.top<top+gridScroll.height }?.requestFocus()
        }
    }
    private fun controllerSearch() {
        val box=column();box.addView(text("Pesquisar · ${glyph("X")} apaga · ${glyph("Menu")} confirma",18f))
        val input=EditText(this).apply { setSingleLine();setText(search.text.toString());setTextColor(appForeground) };box.addView(input)
        val keyboard=GridLayout(this).apply { columnCount=6 }
        fun append(value:String) { input.append(value) }
        for(letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")keyboard.addView(button(letter.toString()) { append(letter.toString()) },GridLayout.LayoutParams().apply { width=dp(48);height=dp(48) })
        box.addView(ScrollView(this).apply { addView(keyboard) },LinearLayout.LayoutParams(-1,dp(190)))
        add(box,button("Espaço") { append(" ") });add(box,button("Apagar") { if(input.length()>0)input.text.delete(input.length()-1,input.length()) })
        val opened=show(AlertDialog.Builder(this).setView(box).setPositiveButton("Pesquisar") { _,_ -> search.setText(input.text.toString()) }.setNegativeButton("Voltar",null))
        opened.setOnKeyListener { _,code,event ->
            if(code !in setOf(KeyEvent.KEYCODE_BUTTON_A,KeyEvent.KEYCODE_BUTTON_B,KeyEvent.KEYCODE_BUTTON_X,KeyEvent.KEYCODE_BUTTON_START))false
            else {
                if(event.action==KeyEvent.ACTION_DOWN && event.repeatCount==0)when(code) {
                    KeyEvent.KEYCODE_BUTTON_A -> opened.currentFocus?.performClick()
                    KeyEvent.KEYCODE_BUTTON_B -> opened.dismiss()
                    KeyEvent.KEYCODE_BUTTON_X -> if(input.length()>0)input.text.delete(input.length()-1,input.length())
                    KeyEvent.KEYCODE_BUTTON_START -> { search.setText(input.text.toString());opened.dismiss() }
                };true
            }
        };keyboard.getChildAt(0)?.requestFocus()
    }
    private fun adaptLayout() {
        val landscape=resources.configuration.orientation==2
        titleView.textSize=if(landscape)18f else 25f
        controlHint.visibility=if(landscape || !store.prefs.getBoolean("ui:show-hint",true))View.GONE else View.VISIBLE
        status.maxLines=if(landscape)1 else 2;message(status.text.toString());search.layoutParams.height=dp(if(landscape)48 else 52)
    }
    private fun draw() {
        val query=GameLogic.normalized(search.text.toString())
        val current=collectionGames().filter { (filterPlatform.isBlank() || it.platform==filterPlatform) && (filterGenre.isBlank() || it.genre==filterGenre) && (query.isBlank() || GameLogic.normalized(it.name+it.platform+it.genre).contains(query)) }
        // Coleção vazia (Fixados/Favoritos sem jogos) não pode parecer botão morto: sorteia dos jogos do celular ou do catálogo.
        val local=games.filter { it.localUri!=null }
        val (pool,title)=when {
            current.isNotEmpty() -> current to "Sortear desta coleção"
            local.isNotEmpty() -> local to "Coleção vazia · sorteando entre os jogos neste celular"
            games.isNotEmpty() -> games to "Coleção vazia · sorteando no catálogo em cache"
            else -> { message("Nenhum jogo para sortear. Escolha as pastas ou carregue o catálogo.");Toast.makeText(this,"Nenhum jogo para sortear.",Toast.LENGTH_LONG).show();return }
        }
        val platforms=listOf("Todos os sistemas")+pool.map { it.platform }.distinct().sorted()
        val genres=listOf("Qualquer gênero")+pool.map { it.genre }.filter { it.isNotBlank() }.distinct().sorted()
        val system=Spinner(this);system.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,platforms)
        val genre=Spinner(this);genre.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,genres)
        system.setSelection(platforms.indexOf(store.prefs.getString("ui:draw-platform","")).coerceAtLeast(0))
        genre.setSelection(genres.indexOf(store.prefs.getString("ui:draw-genre","")).coerceAtLeast(0))
        val box=column();box.addView(text(title,if(pool===current)22f else 18f));box.addView(system);box.addView(genre)
        box.addView(text("${pool.size} jogo(s) disponíveis. O resultado abre a ficha; jogar/baixar exige sua escolha.",13f))
        add(box,button("Sortear e sugerir como jogar") {
            store.prefs.edit().putString("ui:draw-platform",system.selectedItem.toString()).putString("ui:draw-genre",genre.selectedItem.toString()).apply()
            val selected=pool.filter { (system.selectedItemPosition==0 || it.platform==system.selectedItem) && (genre.selectedItemPosition==0 || it.genre==genre.selectedItem) }.randomOrNull()
            if(selected==null)Toast.makeText(this,"Nenhum jogo com esses filtros.",Toast.LENGTH_SHORT).show() else { lastDrawKey=selected.key;details(selected) }
        });show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
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
    private fun changeCollection(step:Int) { val now=SystemClock.elapsedRealtime();if(dialog==null && now-lastCollectionAt>=180) { lastCollectionAt=now;val ids=COLLECTIONS.map { it.first };selectCollection(ids[(ids.indexOf(collection)+step+ids.size)%ids.size]);grid.getChildAt(0)?.let { (firstEnabledButton(it) ?: it).requestFocus() } } }
    private fun toggleFavorite(game:Game) { store.prefs.edit().putBoolean("favorite:${game.key}",!store.prefs.getBoolean("favorite:${game.key}",false)).apply();render() }
    private fun linked(game:Game)=store.prefs.contains("cloud:${game.key}")
    private fun queued(game:Game)=runCatching { queue().contains(game.key) }.getOrDefault(false)
    /** Onde o jogo está e o que dá para fazer com ele, em poucas palavras (cartão e ficha). */
    private fun where(game:Game)=when {
        game.key.startsWith("wish:") -> "♡ Desejado"
        game.localUri!=null -> "▶ Neste celular"
        game.code in store.folders && (linked(game) || game.downloadable) -> "⬇ Baixar"
        GameLogic.remotePackage(game.platform)!=null || GameLogic.streamedThroughNotebook(game.platform) -> "📡 Stream"
        game.pcLocal -> "🖥 No notebook"
        else -> "Catálogo"
    }
    private fun primary(box:LinearLayout,label:String,action:()->Unit)=button(label,action).apply { textSize=18f;setTypeface(null,Typeface.BOLD);minHeight=dp(56) }.also { add(box,it) }
    private fun details(game:Game) {
        if(game.key.startsWith("wish:")) { wishDetails(game);return }
        lastSelectedKey=game.key
        val box=column()
        // Capa grande no topo (some se o jogo não tiver capa no cache).
        val cover=ImageView(this).apply { scaleType=ImageView.ScaleType.FIT_CENTER;contentDescription=game.name;visibility=View.GONE }
        box.addView(cover,LinearLayout.LayoutParams(-1,dp(if(resources.configuration.orientation==2)140 else 230)))
        images.execute { val file=runCatching { store.cover(game) }.getOrNull();val bitmap=file?.let { BitmapFactory.decodeFile(it.path) };if(bitmap!=null)runOnUiThread { cover.setImageBitmap(bitmap);cover.visibility=View.VISIBLE } }
        box.addView(platformChip(game.code,game.platform),LinearLayout.LayoutParams(-2,-2).apply { setMargins(dp(4),0,0,dp(2)) })
        box.addView(text(game.name,22f).apply { setTypeface(null,Typeface.BOLD) })
        val rom=game.code in store.folders;val stream=GameLogic.remotePackage(game.platform);val viaNotebook=GameLogic.streamedThroughNotebook(game.platform)
        val waiting=rom && game.localUri==null && queued(game)
        val state=when {
            game.localUri!=null -> "Neste celular"
            waiting -> "Na fila de downloads"
            rom && (linked(game) || game.downloadable) -> "Pronto para baixar"+(if(!store.online && drive.connected)" do Drive (conta Google)" else if(game.pcLocal)" do notebook" else if(game.drive)" do Drive" else " do arquivo vinculado")
            stream!=null || viaNotebook -> "Console · transmita do aparelho"
            game.pcLocal -> "Instalado no notebook"
            else -> "Só no catálogo"
        }
        val played=store.prefs.getLong("time:${game.key}",0)/60
        box.addView(text(listOfNotNull(game.platform,state,played.takeIf { it>0 }?.let { if(it>=60)"⏱ ${it/60}h${"%02d".format(it%60)} no celular" else "⏱ $it min no celular" }).joinToString(" · "),14f))
        (TrackingRules.value(store.tracking(game),"nota") as Double?)?.let { nota -> box.addView(text(NotaRules.symbol(nota)+" "+TrackingRules.label(nota)+(if(NotaRules.special(nota))" · jogo muito especial" else ""),16f).apply { NotaRules.color(nota)?.let(::setTextColor) }) }
        // A ação principal é a próxima coisa que faz sentido para o jogo; o resto fica em Mais opções.
        when {
            game.localUri!=null -> primary(box,"▶ Jogar neste celular") { dialog?.dismiss();launchLocal(game) }
            waiting -> primary(box,"⬇ Na fila · ver downloads") { downloads() }
            rom && (linked(game) || game.downloadable) -> primary(box,"⬇ Baixar para este celular") { quickDownload(game) }
            stream!=null -> primary(box,if(stream=="com.grill.xbxplay")"📡 Transmitir do Xbox · XBXPlay" else "📡 Transmitir do PlayStation · Remote Play") { dialog?.dismiss();openPackage(stream) }
            viaNotebook -> primary(box,"📡 Transmitir do Switch pelo notebook") { dialog?.dismiss();notebook(game) }
            game.code.isEmpty() && !game.key.startsWith("local:") -> primary(box,"🖥 Jogar no notebook · Moonlight") { dialog?.dismiss();notebook(game) }
            rom -> primary(box,"Procurar a ROM no Drive") { driveSearch(game) }
        }
        if(stream!=null)box.addView(text("Abrir o jogo direto não é possível: escolha-o no console depois de conectar.",13f))
        if(lastDrawKey==game.key)add(box,button("🎲 Sortear novamente") { draw() })
        if(viaNotebook)box.addView(text("Abra o jogo no Switch. O notebook liga o SysDVR e o Moonlight mostra a tela.",13f))
        if(rom && game.localUri==null && !waiting && !linked(game) && !game.downloadable)box.addView(text("O notebook não tem esta ROM. Escolha o arquivo no Drive uma vez; depois o download é direto.",13f))
        val quick=row();horizontal(box,quick)
        add(quick,button(if(store.prefs.getBoolean("favorite:${game.key}",false))"★ Favorito" else "☆ Favoritar") { toggleFavorite(game);details(game) })
        if(rom)add(quick,button(if(SpaceStore(store).pinned(game))"📌 Fixado" else "📌 Fixar") {
            runCatching { SpaceStore(store).setPinned(game,!SpaceStore(store).pinned(game));render();details(game) }.onFailure(::failure)
        })
        if(rom)add(quick,button("💾 Saves") { gameSaves(game) })
        if(game.id.isBlank() && game.key.startsWith("local:") && game.localUri!=null)add(quick,button("📚 Adicionar à Biblioteca") { addToLibrary(game) })
        val progress=expandable(box,"Progresso e tempo",expandedTrackingKey==game.key) { expandedTrackingKey=if(it)game.key else null }
        val tracking=store.tracking(game)
        for((field,label) in listOf("iniciado" to "Iniciado","finalizado" to "Finalizado","platinado" to "Platinado"))add(progress,button((if(tracking.optBoolean(field))"✓ " else "○ ")+label) {
            store.setProgress(game,field,!tracking.optBoolean(field))
            if(GameLogic.offerRemoval(tracking.optBoolean("finalizado"),store.tracking(game).optBoolean("finalizado"),game.localUri!=null) && !SpaceStore(store).pinned(game))offerRomRemoval(game) else details(game)
        })
        if(game.id.isNotBlank()) { // nota só vale para jogo da Biblioteca; ROM solta não cria cadastro
            val nota=TrackingRules.value(tracking,"nota") as Double?
            progress.addView(text("Nota (0–11): ${if(NotaRules.special(nota))"✦ " else ""}${TrackingRules.label(nota)}",16f).apply { setTypeface(null,Typeface.BOLD);NotaRules.color(nota)?.let { setTextColor(it) } })
            val rating=row();horizontal(progress,rating)
            for((label,delta) in listOf("−1" to -1.0,"−0,1" to -0.1,"+0,1" to 0.1,"+1" to 1.0))add(rating,button(label) { store.setNota(game,TrackingRules.adjust(nota,delta));details(game) })
            if(nota!=null)add(rating,button("Limpar") { store.setNota(game,null);details(game) })
        }
        val minutes=store.prefs.getLong("time:${game.key}",0)/60
        progress.addView(text("$minutes min neste celular. Vai para o notebook sozinho quando ele estiver online.",12f))
        val more=expandable(box,"Mais opções")
        if(rom && game.pcLocal && game.code !in setOf("NDS","3DS"))add(more,button("🖥 Jogar no notebook · Moonlight") { dialog?.dismiss();notebook(game) })
        if(game.code=="PS")add(more,button("Abrir DuckStation · escolher jogo") { dialog?.dismiss();openPackage("com.github.stenzek.duckstation") })
        if(rom) {
            add(more,button("Usar outra ROM deste celular") { dialog?.dismiss();pickRom(game,false) })
            add(more,button("Escolher o arquivo no Drive") { driveSearch(game) })
        }
        if(game.code in setOf("PS","PSP","3DS"))add(more,button("Texturas HD deste sistema") { textures(game) })
        if(game.id.isNotBlank())add(more,button("✎ Editar dados (gênero, comentário…)") { editGame(game) })
        ExtrasRules.coverTarget(game.id,game.cover)?.let { target -> add(more,button("🖼 Trocar capa") { coverSearch(game,target) }) }
        if(game.localUri!=null)add(more,button("Remover ROM deste celular") { offerRomRemoval(game) })
        help(more,"Voltar ao PyRetro","Use Recentes → PyRetro para retornar; coleção, busca e posição ficam guardadas. Para encerrar o jogo, use o menu do emulador.")
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    /** Baixar em um toque: arquivo vinculado, ou o que o notebook tem (acervo ou Drive pelo rclone). */
    private fun quickDownload(game:Game) {
        if(store.tree(game.code)==null) {
            downloadAfterFolder=game;dialog?.dismiss();message("Escolha a pasta Jogos do celular; cada sistema fica em Jogos/<sistema>.");pickFolder("ROOT");return
        }
        val current=store.prefs.getString("cloud:${game.key}",null)
        if(current!=null && RomSource.parse(current)==null) { enqueueAndStart(game);return }
        // Notebook fora do ar e conta Google conectada: vai direto ao Drive.
        if(!store.online && drive.connected) { driveDirect(game);return }
        if(!game.downloadable) { if(current!=null)enqueueAndStart(game) else if(drive.connected)driveDirect(game) else driveSearch(game);return }
        message("Consultando o notebook…")
        work.execute { val result=runCatching { RomSource.playable(store.romOptions(game)) { store.accepts(game.code,it) } };runOnUiThread {
            if(isFinishing || isDestroyed)return@runOnUiThread
            result.onSuccess { options -> when(options.size) {
                0 -> offerBundle(game)
                1 -> linkNotebook(game,options[0])
                else -> show(AlertDialog.Builder(this).setTitle("Qual arquivo baixar?").setItems(options.map { "${it.file} · ${bytesLabel(it.size)}" }.toTypedArray()) { _,which -> linkNotebook(game,options[which]) }.setNegativeButton("Voltar",null))
            } }.onFailure { error ->
                if(current!=null)enqueueAndStart(game)
                else if(drive.connected)driveDirect(game)
                else show(AlertDialog.Builder(this).setTitle("Notebook indisponível").setMessage("${error.message ?: "Sem resposta."}\n\nSem o notebook, escolha o arquivo no Drive: ele fica vinculado ao jogo e o download começa em seguida.").setNegativeButton("Voltar",null).setPositiveButton("Procurar no Drive") { _,_ -> driveSearch(game) })
            }
        } }
    }
    /** Sem arquivo único: se o notebook tem um CUE/M3U que o sistema abre, oferece o conjunto inteiro. */
    private fun offerBundle(game:Game) {
        work.execute {
            val result=runCatching {
                val entries=store.romOptions(game).filter { BundleRules.isDescriptor(it.file) && store.accepts(game.code,it.file.substringAfterLast('/')) }
                    .sortedBy { if(it.file.endsWith(".m3u",true))0 else 1 } // M3U (todos os discos) antes do CUE de um disco só
                entries.map { option -> val (id,members)=BundleStore(store,SafStorage(store)).manifest(game.code,option.file);Triple(option.file,id,members) }
            }
            runOnUiThread { if(isFinishing || isDestroyed)return@runOnUiThread
                val bundles=result.getOrElse { emptyList() }
                if(bundles.isEmpty()) { show(AlertDialog.Builder(this).setTitle("Formato que o celular não abre").setMessage("O notebook tem ${game.name}, mas nem num arquivo único que o celular abra nem num CUE/M3U completo (${result.exceptionOrNull()?.message ?: "PS1 precisa de CHD, PBP ou CUE com todas as faixas"}). Converta no PC ou escolha outro arquivo no Drive.").setNegativeButton("Voltar",null).setPositiveButton("Procurar no Drive") { _,_ -> driveSearch(game) });return@runOnUiThread }
                show(AlertDialog.Builder(this).setTitle("Baixar o conjunto de discos").setItems(bundles.map { (entry,_,members) -> "${entry.substringAfterLast('/')} · ${members.size} arquivos · ${bytesLabel(members.sumOf { it.size })}" }.toTypedArray()) { _,which ->
                    val (entry,id,members)=bundles[which]
                    store.prefs.edit().putString("cloud:${game.key}",BundleRef(game.code,entry,id,members.sumOf { it.size }).encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
                    enqueueAndStart(game)
                }.setNegativeButton("Voltar",null))
            }
        }
    }
    // --- Conta Google: Drive direto do celular ---
    private fun connectGoogle(after:Game?=null) {
        driveAfterConsent=after;message("Abrindo a conta Google…")
        drive.authorize().addOnSuccessListener { result ->
            if(result.hasResolution()) runCatching { startIntentSenderForResult(result.pendingIntent!!.intentSender,20,null,0,0,0) }.onFailure(::failure)
            else googleConnected()
        }.addOnFailureListener { error -> failure(IllegalStateException("O Google recusou a conexão: ${error.message}. Confira se esta conta está entre os usuários de teste do projeto PyRetro no Google Cloud.",error)) }
    }
    private fun googleConnected() {
        work.execute { val result=runCatching { drive.account() };runOnUiThread {
            result.onSuccess { email -> message("Conta Google conectada: $email.");driveAfterConsent?.let { game -> driveAfterConsent=null;driveDirect(game) } }.onFailure(::failure)
        } }
    }
    /** Procura a ROM em Jogos/ROMs/<sistema> do Drive da conta e baixa por ela. */
    private fun driveDirect(game:Game) {
        message("Procurando ${game.name} no seu Drive…")
        work.execute {
            val result=runCatching { DriveSource.candidates(drive.romFiles(game.code),game.romName.ifBlank { game.name }) { store.accepts(game.code,it) } }
            runOnUiThread { if(isFinishing || isDestroyed)return@runOnUiThread
                result.onSuccess { found -> when(found.size) {
                    0 -> show(AlertDialog.Builder(this).setTitle("Não achei no Drive").setMessage("Não há em Jogos/ROMs/${game.code} um arquivo de ${game.name} que o celular abra sozinho (PS1 precisa de CHD ou PBP). Escolha o arquivo manualmente.").setNegativeButton("Voltar",null).setPositiveButton("Procurar no Drive") { _,_ -> driveSearch(game) })
                    1 -> linkDrive(game,found[0])
                    else -> show(AlertDialog.Builder(this).setTitle("Qual arquivo baixar?").setItems(found.map { "${it.name} · ${bytesLabel(it.size)}" }.toTypedArray()) { _,which -> linkDrive(game,found[which]) }.setNegativeButton("Voltar",null))
                } }.onFailure { error -> if(error is GoogleConsentNeeded)connectGoogle(game) else failure(error) }
            }
        }
    }
    private fun notificationsAllowed()=Build.VERSION.SDK_INT<33 || checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)==android.content.pm.PackageManager.PERMISSION_GRANTED
    /** Android 13+: a notificação do download em segundo plano precisa de permissão. Pede no máximo
     *  duas vezes (depois disso o próprio Android não mostra mais); Opções tem o atalho permanente. */
    private fun askNotifications() {
        val asked=store.prefs.getInt("asked-notifications-count",0)
        if(!notificationsAllowed() && asked<2) { store.prefs.edit().putInt("asked-notifications-count",asked+1).apply();requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS),30) }
    }
    private fun linkDrive(game:Game,ref:DriveRef) {
        store.prefs.edit().putString("cloud:${game.key}",ref.encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
        enqueueAndStart(game)
    }
    private fun linkNotebook(game:Game,option:RomOption) {
        store.prefs.edit().putString("cloud:${game.key}",RomRef(game.code,option.file,option.etag,option.size).encoded()).remove("cloud-auto:${game.code}:${game.key}").apply()
        enqueueAndStart(game)
    }
    private fun enqueueAndStart(game:Game) {
        runCatching {
            val helper=queue();val source=store.prefs.getString("cloud:${game.key}",null)
            val existing=helper.snapshot().firstOrNull { it.game.key==game.key && it.state!=DownloadState.DONE }
            when {
                existing==null -> helper.enqueue(game)
                existing.state==DownloadState.RUNNING -> Unit
                existing.source==source -> if(existing.state!=DownloadState.WAITING)helper.retry(game.key)
                else -> { helper.remove(game.key);helper.enqueue(game) }
            }
            if(!helper.running)helper.start()
            askNotifications()
        }.onSuccess { dialog?.dismiss();message("⬇ ${game.name}: baixando. O andamento aparece no topo; o jogo fica pronto em Neste celular.") }
            .onFailure { error -> show(AlertDialog.Builder(this).setTitle("Downloads").setMessage(error.message ?: "Não foi possível iniciar o download.").setNegativeButton("Voltar",null).setPositiveButton("Abrir fila") { _,_ -> downloads() }) }
    }
    private fun driveSearch(game:Game) {
        val formats=store.extensionsFor(game.code).filter { it !in setOf("cue","m3u") }.sorted().joinToString(", ")
        show(AlertDialog.Builder(this).setTitle("Escolher no Drive").setMessage("No seletor, abra o Google Drive e escolha:\nJogos/ROMs/${game.code}/${game.romName.ifBlank { game.name }}\n\nFormatos: $formats. O arquivo fica vinculado a ${game.name} e o download começa em seguida.")
            .setNegativeButton("Voltar",null).setPositiveButton("Abrir seletor") { _,_ -> pickRom(game,true) })
    }
    /** Mostra o que sai e o que fica (usado por outro descritor) antes de remover um conjunto. */
    private fun offerBundleRemoval(game:Game) {
        val tree=store.tree(game.code) ?: return;val entry=game.localUri ?: return
        message("Conferindo os arquivos de ${game.name}…")
        work.execute {
            val result=runCatching { BundleStore(store,SafStorage(store,12L*1024*1024*1024)).removalPlan(tree,entry) }
            runOnUiThread { if(isFinishing || isDestroyed)return@runOnUiThread
                result.onFailure(::failure).onSuccess { (_,plan) ->
                    if(!plan.complete || plan.remove.isEmpty()) { show(AlertDialog.Builder(this).setTitle("Remoção não é segura").setMessage("Algum CUE/M3U da pasta Jogos/${game.code} não pôde ser lido (ou nada é só deste jogo), então não dá para garantir que as faixas não são usadas por outro jogo. Nada foi removido.").setPositiveButton("Voltar") { _,_ -> details(game) });return@onSuccess }
                    val text="Sai do celular (${plan.remove.size}):\n"+plan.remove.joinToString("\n") { "• $it" }+
                        (if(plan.preserve.isEmpty())"" else "\n\nFica, porque outro jogo usa (${plan.preserve.size}):\n"+plan.preserve.joinToString("\n") { "• $it" })+
                        "\n\nProgresso, saves, states, BIOS, texturas e a origem no PC/Drive são preservados."
                    show(AlertDialog.Builder(this).setTitle("Remover ${game.name} do celular?").setMessage(text).setNegativeButton("Manter") { _,_ -> details(game) }.setPositiveButton("Remover") { _,_ ->
                        work.execute { val done=runCatching { BundleStore(store,SafStorage(store,12L*1024*1024*1024)).remove(tree,entry,plan) }
                            runOnUiThread { done.onSuccess { n -> store.prefs.edit().remove("rom:${game.key}").apply();message("${game.name}: $n arquivo(s) removido(s) do celular.");reloadLocal() }.onFailure(::failure) } }
                    })
                }
            }
        }
    }
    private fun offerRomRemoval(game:Game) {
        if(SpaceStore(store).pinned(game)) {
            show(AlertDialog.Builder(this).setTitle("Jogo fixado").setMessage("${game.name} está fixado para manter baixado. Desfixe nos detalhes antes de remover a ROM.").setPositiveButton("Voltar") { _,_ -> details(game) });return
        }
        // Conjunto de discos: remove o principal e as faixas/discos que só ele usa (prévia no celular).
        if(game.localUri?.let { store.displayName(it) }?.let(BundleRules::isDescriptor)==true) { offerBundleRemoval(game);return }
        show(AlertDialog.Builder(this).setTitle("Remover ROM do celular?").setMessage("${game.name}\n\nExcluir apenas a ROM local para liberar espaço? Progresso, saves, states, BIOS, texturas e a origem no PC/Drive serão preservados. Você pode baixar o jogo novamente depois.").setNegativeButton("Manter ROM") { _,_ -> details(game) }.setPositiveButton("Excluir ROM local") { _,_ ->
            message("Removendo somente a ROM local…")
            work.execute { runCatching { store.removeLocal(game);PlaylistStore(store).afterChange(game.code) }.onSuccess { playlist -> runOnUiThread { message("ROM removida do celular. Histórico e saves preservados. $playlist");reloadLocal() } }.onFailure { runOnUiThread { failure(it) } } }
        })
    }
    private fun folderState(code:String)=when(StatusStore(store).folders().firstOrNull { it.code==code }?.access) {
        FolderAccess.READ_WRITE -> "✓";FolderAccess.READ_ONLY -> "somente leitura";FolderAccess.RESELECT -> "permissão expirada";else -> "escolher"
    }
    /** Estrutura fechada: Jogos/<sistema>, RetroArch/saves|states por sistema, emuladores e cores padrão. */
    private fun settings() {
        val box=column();box.addView(text("Opções",23f))
        box.addView(text("Configurar este celular",18f).apply { setTypeface(null,Typeface.BOLD) })
        add(box,button("📁 Pasta Jogos · ${folderState("ROOT")}") { dialog?.dismiss();pickFolder("ROOT") })
        add(box,button("📁 Pasta RetroArch (saves) · ${folderState("retroarch")}") { pickSyncFolder("retroarch") })
        val server=EditText(this).apply { setSingleLine();setText(store.base());hint="https://endereço-do-pyretro";setTextColor(appForeground);setHintTextColor(Color.LTGRAY) };box.addView(server)
        add(box,button("Salvar endereço e atualizar catálogo") { runCatching { store.setBase(server.text.toString()) }.onFailure { failure(it);return@button };refreshCatalog() })
        box.addView(text("Conta Google",18f).apply { setTypeface(null,Typeface.BOLD) })
        if(drive.connected) {
            box.addView(text("Conectada: ${drive.email.ifBlank { "conta Google" }}. ROMs do Drive (Jogos/ROMs) baixam direto, sem o notebook.",13f))
            add(box,button("Desconectar conta Google") { drive.disconnect();message("Conta Google desconectada deste app. Para revogar o acesso, use myaccount.google.com → Segurança.");dialog?.dismiss() })
        } else {
            box.addView(text("Conecte para baixar ROMs do seu Drive (Jogos/ROMs) mesmo com o notebook desligado.",13f))
            add(box,button("Conectar conta Google") { dialog?.dismiss();connectGoogle() })
        }
        box.addView(text("ROMs ficam em Jogos/<sistema>; saves e estados, por sistema na pasta RetroArch. Emuladores e cores são os padrões do PyRetro. O catálogo e o progresso atualizam sozinhos quando o notebook responde.",12f))
        if(!notificationsAllowed()) add(box,button("🔔 Permitir notificações de download") {
            runCatching { startActivity(Intent(android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE,packageName)) }.onFailure(::failure) })
        box.addView(text("Uso",18f).apply { setTypeface(null,Typeface.BOLD) })
        val pref=store.prefs.getString("ui:glyphs","auto").orEmpty()
        add(box,button("Botões: ${GlyphRules.label(pref,glyphFamily)}") {
            val next=GlyphRules.choices[(GlyphRules.choices.indexOf(pref)+1).mod(GlyphRules.choices.size)]
            store.prefs.edit().putString("ui:glyphs",next).apply();updateGlyphs();settings()
        })
        add(box,button("Downloads") { downloads() })
        add(box,button("Espaço e jogos fixados") { spaceManager() })
        add(box,button("Saves e estados · todos os jogos") { syncFiles() })
        add(box,button("🗂 Organizar ROMs novas (notebook)") { organizeRoms() })
        val advanced=expandable(box,"Avançado")
        add(advanced,button("Índice manual do Drive") { cloudMenu() })
        add(advanced,button("Playlists do RetroArch") { playlists() })
        add(advanced,button("Texturas HD") { textures() })
        add(advanced,button("Apps instalados · emuladores e streaming") { connectionApps() })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun refreshCatalog(silent:Boolean=false) {
        if(!silent) { dialog?.dismiss();message("Consultando notebook…") }
        work.execute { runCatching { store.refresh() }.onSuccess { fresh -> runOnUiThread {
            catalog=fresh;message(if(silent)"Online · catálogo atualizado agora." else "Catálogo atualizado. As capas são guardadas conforme você navega.");reloadLocal { prefetchCovers() }
        } }.onFailure { store.online=false;runOnUiThread { if(!silent)failure(it) } } }
    }
    private fun syncTracking(silent:Boolean=false) {
        if(!silent) { dialog?.dismiss();message("Enviando progresso e tempo…") }
        work.execute { runCatching { store.synchronize() }.onSuccess { result -> val fresh=store.cached();runOnUiThread {
            catalog=fresh;message(if(silent)"Online · catálogo atualizado. $result" else result);reloadLocal { prefetchCovers() }
        } }.onFailure { runOnUiThread { if(!silent)failure(it) } } }
    }
    /** Notebook respondeu: atualiza o que é só leitura ou já protegido por conflito no servidor.
     *  Saves continuam explícitos (precisam dos emuladores fechados e de decisão em conflitos). */
    private fun automaticUpdate(force:Boolean=false) {
        // No máximo a cada 15 min: pendências em conflito continuam pendentes e não podem virar um laço.
        val now=SystemClock.elapsedRealtime()
        if(!automaticUpdates || (!force && lastAutomaticUpdate>0 && now-lastAutomaticUpdate<15*60*1000L))return
        lastAutomaticUpdate=now
        val stale=System.currentTimeMillis()-store.prefs.getLong("updated",0)>6*60*60*1000L
        if(store.pending()>0)syncTracking(silent=true) else if(stale || catalog.isEmpty())refreshCatalog(silent=true)
    }
    /** Capas dos jogos do celular, favoritos e fixados ficam no cache para o modo offline. */
    private fun prefetchCovers() {
        if(!store.online)return
        val pinned=SpaceStore(store).pinnedChecker()
        val wanted=games.filter { it.localUri!=null || store.prefs.getBoolean("favorite:${it.key}",false) || pinned(it) }.take(300)
        prefetch.execute { for(game in wanted) { if(!store.online)break;runCatching { store.cover(game) } } }
    }
    /** Saves e estados pela nuvem (core/cloud_saves no notebook): compara, mostra e só então sincroniza. */
    private fun cloudSaves(title:String="☁ Saves na nuvem",filter:((String,String)->Boolean)?=null) {
        val box=column();box.addView(text(title,23f));val info=text("Comparando com o Drive…",15f);box.addView(info)
        val area=column();box.addView(area)
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Fechar",null))
        var busy=false
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
            val phone=runCatching { CloudPhone(store,FileSync(store),DriveCloudStorage(drive)) }
            val analysis=phone.mapCatching { it.analyze(filter) }
            runOnUiThread {
                if(dialog!==opened)return@runOnUiThread
                val result=analysis.getOrElse { info.text="Não foi possível comparar: ${it.message}";return@runOnUiThread }
                if(result.isEmpty()) { info.text="Escolha as pastas de saves em Situação (pasta RetroArch, PPSSPP, 3DS).";return@runOnUiThread }
                val counts=result.values.mapNotNull { it.getOrNull() }.flatten().groupingBy { it.action }.eachCount()
                val failed=result.filterValues { it.isFailure }
                info.text=if(counts.isEmpty() && failed.isEmpty())"Tudo em dia com a nuvem." else
                    "Enviar: ${counts["push"] ?: 0} · Baixar: ${counts["pull"] ?: 0} · Conflitos: ${counts["conflict"] ?: 0}"+if(failed.isEmpty())"" else "\nErro em: ${failed.map { it.key+" ("+it.value.exceptionOrNull()?.message+")" }.joinToString()}"
                val pending=counts.filterKeys { it=="push" || it=="pull" }.values.sum()
                if(pending>0)add(area,button("Sincronizar agora ($pending)") {
                    perform { CloudFeedback.batch { phone.getOrThrow().apply(filter=filter) } }
                })
                for((group,items) in result)for(item in items.getOrNull().orEmpty().filter { it.action=="conflict" }) {
                    add(area,text("⚠ Conflito: ${item.path}",15f))
                    val line=row();horizontal(area,line)
                    add(line,button("Manter o do celular") { perform { CloudFeedback.resolve("Mantido o do celular: ${item.path}") { phone.getOrThrow().resolve(group,item.path,"local") } } })
                    add(line,button("Usar o da nuvem") { perform { CloudFeedback.resolve("Usado o da nuvem: ${item.path}") { phone.getOrThrow().resolve(group,item.path,"remote",item.heads.keys.first()) } } })
                }
            }
        }
    }
    private fun statusCenter() {
        val box=column();val prefs=store.prefs;val pending=StatusStore(store).pending()
        fun date(key:String)=prefs.getLong(key,0).takeIf { it>0 }?.let(::versionDate) ?: "ainda não"
        fun line(title:String,value:String):TextView { box.addView(text(title,18f).apply { setTypeface(null,Typeface.BOLD) });return text(value,14f).also(box::addView) }
        box.addView(text("Situação",23f))
        fun localSummary()=(if(localScanAt==0L)"Lendo as pastas…" else "${games.count { it.localUri!=null }} jogo(s) prontos para jogar · ${catalog.size} no catálogo (${date("updated")}).")+
            if(localProblems.isEmpty())"" else "\nNão foi possível ler: ${localProblems.joinToString()}."
        val local=line("🎮 Neste celular",localSummary())
        if(folderState("ROOT")!="✓" && prefs.getString("tree:ROOT",null)==null)add(box,button("Escolher a pasta Jogos") { dialog?.dismiss();pickFolder("ROOT") })
        else if(localProblems.isNotEmpty())add(box,button("Corrigir pastas") { folderStatuses() })
        fun notebookSummary()=when { store.base().isBlank() -> "Endereço não configurado.";store.online -> "Online. Catálogo e progresso atualizam sozinhos.";else -> "Offline. Jogos do celular e catálogo em cache continuam funcionando." }
        val notebook=line("🖥 Notebook",notebookSummary())
        val test=button("Testar conexão") {}
        if(store.base().isBlank())add(box,button("Configurar endereço") { settings() }) else add(box,test)
        val tracking=pending.size
        line("⏳ Progresso e tempo",if(tracking==0)"Tudo enviado. Última sincronização: ${date("tracking-sync-at")}." else "$tracking alteração(ões) esperando o notebook.${if(pending.any { it.conflict })" Algumas precisam de conferência." else ""}")
        if(tracking>0)add(box,button("Enviar agora") { syncTracking() })
        if(pending.any { it.conflict })add(box,button("Conferir pendências") { pendingChanges() })
        val rows=runCatching { queue().snapshot() }.getOrDefault(emptyList()).filter { it.state!=DownloadState.DONE }
        if(rows.isNotEmpty()) {
            line("⬇ Downloads","${rows.size} na fila · ${rows.count { it.state==DownloadState.FAILED }} com falha · ${rows.count { it.state==DownloadState.PAUSED }} pausado(s).")
            add(box,button("Abrir downloads") { downloads() })
        }
        val sync=FileSync(store);val cloudAt=store.context.getSharedPreferences("cloud-sync",0).getLong("at",0)
        line("💾 Saves",if(sync.retroarchTree()==null)"Pasta RetroArch ainda não escolhida." else
            "Pastas prontas. Última sincronização pela nuvem: ${if(cloudAt>0)versionDate(cloudAt) else "ainda não"}. Use 💾 Saves na ficha de cada jogo.")
        if(sync.retroarchTree()==null)add(box,button("Escolher pasta RetroArch") { pickSyncFolder("retroarch") })
        // Escolha antiga (antes da 0.6.1) em RetroArch/saves: os saves do RetroArch não aparecem.
        else sync.retroarchTree()?.let { SaveRules.retroarchFolderProblem(DocumentsContract.getTreeDocumentId(it)) }?.let { problem ->
            box.addView(text("⚠ $problem",14f).apply { setTextColor(Color.rgb(255,207,112)) })
            add(box,button("Escolher a pasta RetroArch de novo") { pickSyncFolder("retroarch") })
        }
        line("☁ Saves na nuvem (novo)","Sincroniza saves e estados direto pelo Drive (pasta Jogos/PyRetro-Nuvem), sem o notebook ligado. Conflito nunca sobrescreve: você escolhe.")
        add(box,button("Comparar e sincronizar") { dialog?.dismiss();cloudSaves() })
        val technical=expandable(box,"Detalhes técnicos")
        val contact=text(StatusStore(store).connectionSummary(::versionDate),13f);technical.addView(contact)
        val partials=text("Consultando cópias parciais…",13f);technical.addView(partials)
        technical.addView(text("${prefs.all.keys.count { it.startsWith("cloud:") }} jogo(s) com origem de download vinculada.",13f))
        add(technical,button("Pastas e permissões") { folderStatuses() })
        add(technical,button("Apps instalados") { connectionApps() })
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Fechar",null))
        updateLocalStatus={ if(dialog===opened)local.text=localSummary() }
        test.setOnClickListener {
            test.isEnabled=false;notebook.text="Testando conexão…"
            work.execute { val result=runCatching { store.checkConnection() };runOnUiThread {
                if(dialog===opened && !isFinishing && !isDestroyed) {
                    contact.text=StatusStore(store).connectionSummary(::versionDate);test.isEnabled=true
                    notebook.text=if(result.isSuccess)"Online. PyRetro respondeu em ${versionDate(System.currentTimeMillis())}." else "Sem resposta. Confira o Tailscale e o notebook; o modo offline continua."
                    if(result.isSuccess) { store.online=true;notebookOnline(force=true) }
                }
            } }
        }
        images.execute { val result=runCatching { DownloadStore(store).jobs() };runOnUiThread {
            if(dialog===opened && !isFinishing && !isDestroyed)partials.text=result.fold(
                { jobs -> "${jobs.size} cópia(s) parcial(is) · ${bytesLabel(jobs.sumOf { it.getLong("bytes") })} no armazenamento privado." },
                { "Não foi possível ler as cópias parciais. Abra Downloads para conferir." })
        } }
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
            "Xbox · XBXPlay" to listOf("com.grill.xbxplay"),"PS4 · Remote Play" to listOf("com.playstation.remoteplay"),"PC · Moonlight" to listOf("com.limelight"))
        val box=column();box.addView(text("Emuladores e conexões",22f))
        box.addView(text("Aplicativo encontrado significa apenas que pode ser aberto. Login, pareamento, VPN, cores e funcionamento em jogo precisam ser conferidos no próprio aplicativo.",14f))
        for((label,packages) in apps) {
            val installed=packages.firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null }
            add(box,button("$label · ${if(installed==null)"não encontrado" else "abrir"}") {
                if(installed!=null)openPackage(installed)
            }.apply { isEnabled=installed!=null;alpha=if(installed!=null)1f else 0.55f })
        }
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar") { _,_ -> statusCenter() })
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
                    }.setPositiveButton("Adicionar à fila") { _,_ -> quickDownload(game) });Unit
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
        work.execute {
            val label=SaveRules.label(game.localUri?.let { runCatching { store.displayName(it) }.getOrNull() } ?: game.romName.substringAfterLast('/').ifBlank { game.name },store.extensionsFor(game.code))
            // RetroArch: só os arquivos deste jogo. PSP/3DS: o grupo do emulador inteiro (o ID do título não é lido aqui).
            val mine:(String,String)->Boolean=if(retro) { g,path -> g in setOf("retro-saves","retro-states") && SaveRules.belongs(path,game.code,label) }
                else { g,_ -> g.startsWith(if(game.code=="PSP")"psp-" else "3ds-") }
            runOnUiThread { cloudSaves("💾 ${game.name}",mine) }
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
    /** ROM que só existe no celular ganha cadastro na Biblioteca do notebook; favorito, tempo e
     *  fixação passam para a chave do cadastro. */
    private fun addToLibrary(game:Game) {
        if(!needsNotebook())return
        val name=GameLogic.fileLabel(game.romName.substringAfterLast('/').ifBlank { game.name })
        dialog?.dismiss();message("Cadastrando ${game.name} na Biblioteca…")
        work.execute {
            val result=runCatching { val response=extras.addRom(name,game.code);response to store.refresh() }
            runOnUiThread { result.onSuccess { (response,fresh) ->
                val id=response.getString("id");val registered=fresh.firstOrNull { it.id==id }
                if(registered!=null && registered.key!=game.key)runCatching { store.migrateKeys(mapOf(game.key to registered.key)) }
                registered?.let { store.prefs.edit().putString("rom:${it.key}",game.localUri.toString()).apply() }
                catalog=fresh;dialog?.dismiss()
                message(if(response.optBoolean("created"))"${game.name} entrou na Biblioteca." else "${game.name} já estava na Biblioteca; agora está ligado a este arquivo.")
                reloadLocal()
            }.onFailure(::failure) }
        }
    }
    private fun syncFiles() {
        val sync=FileSync(store);val box=column();box.addView(text("Saves e estados",22f))
        box.addView(text("Sincroniza direto pelo Drive (pasta Jogos/PyRetro-Nuvem), sem o notebook ligado. Feche os emuladores. Conflito nunca sobrescreve: você escolhe; versões substituídas ficam no histórico.",13f))
        box.addView(text("Estados exigem core/versão compatíveis. 3DS inclui apenas saves/extdata da SDMC, sem jogos instalados.",13f))
        add(box,button("☁ Comparar e sincronizar tudo") { dialog?.dismiss();cloudSaves() })
        add(box,button("Escolher pasta RetroArch") { pickSyncFolder("retroarch") })
        for((group,label) in sync.groups.filterKeys { it in CloudPhone.prefixes })add(box,button("Pasta de $label") { pickSyncFolder(group) })
        for((group,label) in sync.groups.filterKeys { it in CloudPhone.prefixes })add(box,button("Versões deste celular · $label") { localVersions(group) })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun coreId(code:String)=CoreProfiles.id(code,store.prefs.getString("core:$code",if(code=="NDS")store.prefs.getString("nds-core",null) else null))
    private fun pickFolder(code:String) { pickingCode=code;startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),10) }
    private fun pickRom(game:Game,cloud:Boolean) { pickingGame=game;pickingCloud=cloud;startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),11) }
    @Deprecated("Compatibilidade com Activity sem dependências extras")
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(requestCode,resultCode,data)
        if(requestCode==20) { // consentimento da conta Google
            if(resultCode!=RESULT_OK) { driveAfterConsent=null;message("Conta Google não conectada.");return }
            runCatching { drive.resultFromIntent(data) }.onSuccess { googleConnected() }.onFailure(::failure);return
        }
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
            show(AlertDialog.Builder(this).setTitle("Instalar pacote local?").setMessage("$name\n$code · $id\nFeche o emulador. Texturas diferentes existentes não serão substituídas.").setNegativeButton("Cancelar",null).setPositiveButton("Instalar") { _,_ -> runTexture { progress -> TextureStore(store).local(uri,code,id,progress) } });return
        }
        runCatching {
            if(requestCode==10 && data.flags and Intent.FLAG_GRANT_WRITE_URI_PERMISSION != 0)
                contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            else contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }.onFailure { message("Permissão temporária: pode ser necessário selecionar o arquivo novamente após reiniciar.") }
        if(requestCode==10) { store.saveTree(pickingCode,uri);val pending=downloadAfterFolder;downloadAfterFolder=null;reloadLocal { if(pending!=null)quickDownload(pending) } }
        if(requestCode==11) {
            val game=pickingGame ?: return;val name=store.displayName(uri)
            if(!pickingCloud && uri.authority!="com.android.externalstorage.documents") { message("Escolha uma ROM no armazenamento local. Para o Drive, use Escolher o arquivo no Drive.");return }
            if(!store.accepts(game.code,name)) { message("Esse formato não corresponde a ${game.code}.");return }
            if(pickingCloud) {
                if(name.substringAfterLast('.').lowercase() in setOf("cue","m3u")) { message("CUE/M3U dependem de outros arquivos. Escolha CHD ou PBP.");return }
                // Escolher no Drive já é a decisão: vincula ao jogo e começa o download.
                store.prefs.edit().putString("cloud:${game.key}",uri.toString()).remove("cloud-auto:${game.code}:${game.key}").apply()
                quickDownload(game);return
            }
            show(AlertDialog.Builder(this).setTitle("Usar esta ROM").setMessage("Usar $name para ${game.name}?").setNegativeButton("Cancelar",null).setPositiveButton("Usar") { _,_ ->
                store.prefs.edit().putString("rom:${game.key}",uri.toString()).apply();game.localUri=uri
                reloadLocal { details(game) }
            })
        }
    }
    override fun onConfigurationChanged(newConfig:android.content.res.Configuration) { super.onConfigurationChanged(newConfig);adaptLayout();render() }
    private fun openPackage(name:String) {
        val intent=packageManager.getLaunchIntentForPackage(name)
        if(intent==null) { message("Aplicativo não instalado: $name");return }
        startActivity(intent)
    }
    private fun launchLocal(game:Game) {
        val uri=game.localUri ?: return
        try {
            val intent=when(game.code) {
                "3DS" -> {
                    val target=listOf("io.github.lime3ds.android","io.github.azahar_emu.azahar").firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null } ?: error("Instale/configure Lime3DS ou Azahar no celular.")
                    Intent(Intent.ACTION_VIEW).setPackage(target).setDataAndType(uri,"application/octet-stream")
                }
                "PSP" -> {
                    val target=listOf("org.ppsspp.ppssppgold","org.ppsspp.ppsspp").firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null } ?: error("PPSSPP não encontrado.")
                    Intent(Intent.ACTION_VIEW).setPackage(target).setDataAndType(uri,"application/octet-stream")
                }
                else -> {
                    val pkg=listOf("com.retroarch","com.retroarch.aarch64").firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null } ?: error("RetroArch não encontrado.")
                    val id=DocumentsContract.getDocumentId(uri);val parts=id.split(':',limit=2)
                    require(uri.authority=="com.android.externalstorage.documents" && parts.size==2) { "Copie a ROM para uma pasta do armazenamento interno antes de abrir no RetroArch." }
                    val path=(if(parts[0]=="primary")"/storage/emulated/0/" else "/storage/${parts[0]}/")+parts[1]
                    val core=coreId(game.code)
                    val target=packageManager.getApplicationInfo(pkg,0)
                    Intent().setComponent(ComponentName(pkg,"com.retroarch.browser.retroactivity.RetroActivityFuture")).putExtra("ROM",path).putExtra("LIBRETRO","${target.dataDir}/cores/${core}_libretro_android.so").putExtra("CONFIGFILE","/storage/emulated/0/Android/data/$pkg/files/retroarch.cfg")
                }
            }
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);intent.clipData=ClipData.newRawUri("ROM",uri)
            activeGame=game;launchedAt=SystemClock.elapsedRealtime();leftForGame=false;startActivity(intent)
            store.prefs.edit().putLong("played:${game.key}",System.currentTimeMillis()).apply() // fileira Recentes do Início
        } catch(error:Exception) { activeGame=null;failure(error) }
    }
    private fun notebook(game:Game) {
        show(AlertDialog.Builder(this).setTitle("Jogar no notebook").setMessage("Iniciar o jogo no notebook e abrir o Moonlight? Você escolhe o computador no Moonlight. Essa opção precisa de conexão; os jogos locais continuam offline.").setNegativeButton("Só Moonlight") { _,_ -> openPackage("com.limelight") }.setPositiveButton("Iniciar no PC") { _,_ ->
            message("Conferindo jogo no notebook…");work.execute { runCatching {
                if(game.code.isNotEmpty()) {
                    val options=JSONObject(store.request("/api/play/options?code=${Uri.encode(game.code)}&name=${Uri.encode(game.romName)}")).getJSONArray("options")
                    val valid=(0 until options.length()).map { options.getJSONObject(it) }.filter { it.isNull("error") }
                    require(valid.size==1) { "Escolha o disco/formato na interface do notebook." }
                    store.request("/api/play/start",JSONObject().put("code",game.code).put("name",valid[0].getString("name")))
                } else {
                    require(game.id.isNotBlank());val options=JSONObject(store.request("/api/pc/options?id="+Uri.encode(game.id)))
                    val remote=options.optJSONObject("remote")
                    if(remote!=null)store.request("/api/tv/apps/launch",JSONObject().put("id",remote.getJSONObject("app").getString("id")))
                    else { require(options.optBoolean("available")) { "Jogo não instalado no notebook. Abra a loja pelo Moonlight para instalar." };store.request("/api/pc/launch",JSONObject().put("id",game.id)) }
                }
            }.onSuccess { runOnUiThread { message("Pedido enviado ao notebook.");openPackage("com.limelight") } }.onFailure { runOnUiThread { failure(it) } } }
        })
    }
    /** Confere o notebook em segundo plano (só /api/csrf, no máximo 1×/min) para que o
     *  estado online, o aviso do topo e o download de capas reflitam a conexão real, em vez de
     *  ficar "Offline" até o usuário atualizar o catálogo à mão. Não baixa catálogo nem sincroniza. */
    private fun probeNotebook(force:Boolean=false) {
        val now=SystemClock.elapsedRealtime()
        // Offline, a próxima tentativa não espera 1 min: o Tailscale pode ter acabado de ligar.
        val wait=if(force || !store.online)5_000 else 60_000
        if(probing || store.base().isBlank() || (lastProbeAt>0 && now-lastProbeAt<wait))return
        probing=true;lastProbeAt=now
        Thread {
            val ok=store.probe()
            runOnUiThread {
                probing=false
                if(isFinishing || isDestroyed)return@runOnUiThread
                if(ok)notebookOnline()
                else if(status.text.startsWith("Online ·"))message("Offline · notebook não respondeu. Catálogo em cache e jogos locais continuam disponíveis.")
            }
        }.apply { isDaemon=true }.start()
    }
    /** O notebook respondeu (sondagem ou "Testar conexão"): o aviso do topo deixa de dizer Offline. */
    private fun notebookOnline(force:Boolean=false) {
        val updated=store.prefs.getLong("updated",0).takeIf { it>0 }?.let(::versionDate)
        val text=status.text.toString()
        if(text.startsWith("Offline") || text.startsWith("Modo offline") || text.startsWith("Online ·"))
            message(if(catalog.isEmpty())"Online · notebook conectado. Buscando o catálogo…" else "Online · notebook conectado. Catálogo de ${updated ?: "data desconhecida"}.")
        if(collection=="wishlist")loadWishlist()
        if(collection!="stream")render() // capas que faltavam no cache agora podem ser baixadas
        automaticUpdate(force)
    }
    override fun onPause() {
        // Downloads continuam com o app em segundo plano: o serviço mostra o progresso e o Pausar.
        queueHandler.removeCallbacks(queueTick);if(runCatching { queue().running }.getOrDefault(false))DownloadService.follow(this)
        if(::gridScroll.isInitialized) {
            restoredScroll=gridScroll.scrollY;restoredPage=page;restorePosition=true
            val selected=(currentFocus?.tag as? Game)?.key ?: lastSelectedKey
            store.prefs.edit().putString("ui:collection",collection).putInt("ui:page",page).putInt("ui:scroll",restoredScroll)
                .putString("ui:query",search.text.toString().take(256)).putString("ui:selected",selected)
                .putString("ui:filter:$collection:platform",filterPlatform).putString("ui:filter:$collection:genre",filterGenre).apply()
        }
        super.onPause();scanOnResume=true;if(activeGame!=null)leftForGame=true
    }
    override fun onResume() {
        super.onResume();queueHandler.removeCallbacks(queueTick);queueHandler.post(queueTick);if(scanOnResume) { scanOnResume=false;reloadLocal();probeNotebook() };val game=activeGame ?: return
        if(!leftForGame)return
        activeGame=null;leftForGame=false
        val elapsed=(SystemClock.elapsedRealtime()-launchedAt)/60000
        if(elapsed<1)return
        val minutes=EditText(this).apply { inputType=android.text.InputType.TYPE_CLASS_NUMBER;setText(elapsed.coerceAtMost(1440).toString()) }
        fun save():Boolean {
            val value=minutes.text.toString().toIntOrNull()
            if(value!=null && value in 1..1440) { store.addTime(game,value);message("Tempo salvo. Vai para o notebook sozinho quando ele responder.");if(store.online)automaticUpdate(force=true);return true }
            message("Use entre 1 e 1440 minutos.");return false
        }
        // Voltar de um jogo é o momento natural de levar o save para o notebook.
        show(AlertDialog.Builder(this).setTitle("Registrar tempo de ${game.name}?").setMessage("Confirme os minutos que jogou. O tempo em outros apps pode estar incluído.").setView(minutes).setNegativeButton("Descartar",null)
            .setNeutralButton("Salvar e ver saves") { _,_ -> if(save())gameSaves(game) }.setPositiveButton("Salvar") { _,_ -> save() })
    }
    override fun onKeyDown(keyCode:Int,event:KeyEvent):Boolean {
        if(event.repeatCount>0 && keyCode in setOf(KeyEvent.KEYCODE_BUTTON_A,KeyEvent.KEYCODE_BUTTON_X,KeyEvent.KEYCODE_BUTTON_START))return true
        when(keyCode) {
            KeyEvent.KEYCODE_BUTTON_A -> { currentFocus?.performClick();return true }
            KeyEvent.KEYCODE_BUTTON_B -> { if(dialog!=null)dialog?.dismiss() else if(collection=="stream")selectCollection("home") else if(search.text.isNotEmpty())search.text.clear() else { collection="home";page=0;render() };return true }
            KeyEvent.KEYCODE_BUTTON_X -> { (currentFocus?.tag as? Game)?.let(::toggleFavorite);return true }
            KeyEvent.KEYCODE_BUTTON_Y -> { if(event.repeatCount==0 && collection!="stream")controllerSearch();return true }
            KeyEvent.KEYCODE_BUTTON_L1 -> { changePage(-1);return true }
            KeyEvent.KEYCODE_BUTTON_R1 -> { changePage(1);return true }
            KeyEvent.KEYCODE_BUTTON_L2,KeyEvent.KEYCODE_BUTTON_R2 -> { if(event.repeatCount==0)changeCollection(if(keyCode==KeyEvent.KEYCODE_BUTTON_R2)1 else -1);return true }
            KeyEvent.KEYCODE_BUTTON_START -> { settings();return true }
        }
        return super.onKeyDown(keyCode,event)
    }
    override fun onGenericMotionEvent(event:MotionEvent):Boolean {
        return navigateMotion(event,currentFocus) || super.onGenericMotionEvent(event)
    }
    private fun navigateMotion(event:MotionEvent,focused:View?):Boolean {
        if(event.isFromSource(InputDevice.SOURCE_JOYSTICK) && event.action==MotionEvent.ACTION_MOVE) {
            val lt=maxOf(event.getAxisValue(MotionEvent.AXIS_LTRIGGER),event.getAxisValue(MotionEvent.AXIS_BRAKE))>.55
            val rt=maxOf(event.getAxisValue(MotionEvent.AXIS_RTRIGGER),event.getAxisValue(MotionEvent.AXIS_GAS))>.55
            if(lt && !leftTrigger)changeCollection(-1)
            if(rt && !rightTrigger)changeCollection(1)
            leftTrigger=lt;rightTrigger=rt
            val now=SystemClock.elapsedRealtime();if(now-lastMotion<180)return true
            val x=event.getAxisValue(MotionEvent.AXIS_X)+event.getAxisValue(MotionEvent.AXIS_HAT_X)
            val y=event.getAxisValue(MotionEvent.AXIS_Y)+event.getAxisValue(MotionEvent.AXIS_HAT_Y)
            if(focused is ListView && (x>.55 || x<-.55 || y>.55 || y<-.55)) {
                val code=when { y>.55 -> KeyEvent.KEYCODE_DPAD_DOWN;y<-.55 -> KeyEvent.KEYCODE_DPAD_UP;x>.55 -> KeyEvent.KEYCODE_DPAD_RIGHT;else -> KeyEvent.KEYCODE_DPAD_LEFT }
                lastMotion=now;focused.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN,code));focused.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_UP,code));return true
            }
            val next=when { x>.55 -> focused?.focusSearch(View.FOCUS_RIGHT);x<-.55 -> focused?.focusSearch(View.FOCUS_LEFT);y>.55 -> focused?.focusSearch(View.FOCUS_DOWN);y<-.55 -> focused?.focusSearch(View.FOCUS_UP);else -> return false }
            lastMotion=now;next?.requestFocus() ?: pageRoot.requestFocus(View.FOCUS_DOWN);return true
        }
        return false
    }
}
