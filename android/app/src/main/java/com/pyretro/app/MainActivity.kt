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
    private lateinit var store:LibraryStore
    private lateinit var pageRoot:LinearLayout
    private lateinit var grid:GridLayout
    private lateinit var search:EditText
    private lateinit var status:TextView
    private lateinit var counter:TextView
    private lateinit var quickBar:View
    private lateinit var headingBar:View
    private lateinit var compactOptions:Button
    private lateinit var gridScroll:ScrollView
    private lateinit var controlHint:TextView
    private lateinit var controllerManager:InputManager
    private val work=Executors.newSingleThreadExecutor()
    private val images=Executors.newFixedThreadPool(2)
    private var catalog=emptyList<Game>()
    private var games=emptyList<Game>()
    private var localProblems=emptyList<String>()
    private var localScanAt=0L
    private var updateLocalStatus:(()->Unit)?=null
    private var collection="cell"
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
    private var leftTrigger=false
    private var rightTrigger=false
    private val appBackground=Color.rgb(11,18,32)
    private val appForeground=Color.rgb(237,244,253)
    private val accent=Color.rgb(129,225,202)
    private fun dp(value:Int)=(value*resources.displayMetrics.density).toInt()
    private fun shape(selected:Boolean=false)=GradientDrawable().apply { cornerRadius=dp(12).toFloat();setColor(if(selected)Color.rgb(35,94,87) else Color.rgb(26,43,63));setStroke(dp(if(selected)3 else 1),if(selected)accent else Color.rgb(60,81,102)) }
    private fun text(value:String,size:Float=16f)=TextView(this).apply { text=value;textSize=size;setTextColor(appForeground);setPadding(dp(4),dp(4),dp(4),dp(4)) }
    private fun button(value:String,action:()->Unit)=Button(this).apply { text=value;isAllCaps=false;minHeight=dp(48);setTextColor(appForeground);background=shape();setPadding(dp(12),dp(6),dp(12),dp(6));setOnClickListener { action() };setOnFocusChangeListener { _,focused -> background=shape(focused) } }
    private fun row()=LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL }
    private fun column()=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setPadding(dp(12),dp(8),dp(12),dp(8)) }
    private fun add(parent:LinearLayout,view:View,weight:Float=0f) { parent.addView(view,LinearLayout.LayoutParams(if(weight>0)0 else ViewGroup.LayoutParams.WRAP_CONTENT,ViewGroup.LayoutParams.WRAP_CONTENT,weight).apply { setMargins(dp(3),dp(3),dp(3),dp(3)) }) }
    private fun horizontal(parent:LinearLayout,content:LinearLayout) { parent.addView(HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled=false;addView(content) },LinearLayout.LayoutParams(-1,-2)) }
    private fun message(value:String) { status.text=value }
    private fun failure(error:Throwable) { message(error.message ?: "Não foi possível concluir.") }
    private fun firstEnabledButton(view:View):Button? {
        if(view.visibility!=View.VISIBLE)return null
        if(view is Button && view.isEnabled)return view
        if(view is ViewGroup)for(index in 0 until view.childCount)firstEnabledButton(view.getChildAt(index))?.let { return it }
        return null
    }
    private fun show(builder:AlertDialog.Builder):AlertDialog {
        dialog?.dismiss();return builder.create().also { opened ->
            dialog=opened;opened.setOnDismissListener { if(dialog===opened) { dialog=null;updateLocalStatus=null } }
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
        window.statusBarColor=appBackground;window.navigationBarColor=appBackground
        pageRoot=column().apply { setBackgroundColor(appBackground) }
        pageRoot.setOnApplyWindowInsetsListener { view,insets ->
            if(Build.VERSION.SDK_INT>=30) {
                val safe=insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout() or WindowInsets.Type.ime())
                view.setPadding(dp(12)+safe.left,dp(8)+safe.top,dp(12)+safe.right,dp(8)+safe.bottom)
            } else view.setPadding(dp(12)+insets.systemWindowInsetLeft,dp(8)+insets.systemWindowInsetTop,dp(12)+insets.systemWindowInsetRight,dp(8)+insets.systemWindowInsetBottom)
            insets
        }
        val heading=row();add(heading,text("✦ PyRetro",25f).apply { setTypeface(null,Typeface.BOLD) },1f);add(heading,button("Situação") { statusCenter() });add(heading,button("Opções") { settings() });pageRoot.addView(heading);headingBar=heading
        val quick=row();add(quick,button("Xbox · XBXPlay") { openPackage("com.grill.xbxplay") });add(quick,button("PS4 · Remote Play") { openPackage("com.playstation.remoteplay") });add(quick,button("PC · Moonlight") { openPackage("com.limelight") });horizontal(pageRoot,quick);quickBar=pageRoot.getChildAt(pageRoot.childCount-1)
        val collections=row();for((id,label) in listOf("cell" to "Neste celular","catalog" to "Catálogo em cache","favorites" to "Favoritos"))add(collections,button(label) { collection=id;page=0;render() });horizontal(pageRoot,collections)
        add(collections,button("Sortear") { draw() });add(collections,button("Texturas") { textures() })
        compactOptions=button("Opções") { settings() };add(collections,compactOptions)
        add(collections,button("Situação") { statusCenter() })
        search=EditText(this).apply { hint="Y · Pesquisar nome, plataforma ou gênero";setHintTextColor(Color.LTGRAY);setTextColor(appForeground);isSingleLine=true;minHeight=dp(48);background=shape();setPadding(dp(12),0,dp(12),0) }
        search.addTextChangedListener(object:TextWatcher { override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){};override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){page=0;render()};override fun afterTextChanged(s:Editable?){} })
        pageRoot.addView(search,LinearLayout.LayoutParams(-1,dp(52)))
        status=text("Modo offline · selecione suas pastas ou carregue o catálogo do notebook.",13f);pageRoot.addView(status)
        grid=GridLayout(this).apply { alignmentMode=GridLayout.ALIGN_BOUNDS }
        gridScroll=ScrollView(this).apply { isFillViewport=true;addView(grid) };pageRoot.addView(gridScroll,LinearLayout.LayoutParams(-1,0,1f))
        val paging=row();add(paging,button("LB · Anterior") { changePage(-1) });counter=text("",13f);add(paging,counter,1f);add(paging,button("Próxima · RB") { changePage(1) });pageRoot.addView(paging)
        controlHint=text("Galileo G8: direcional/analógico · A abrir · B voltar · X favorito · Y buscar · Menu opções",11f);pageRoot.addView(controlHint)
        setContentView(pageRoot);adaptLayout();catalog=store.cached();if(catalog.isNotEmpty())message("Offline · catálogo em cache. Jogos locais disponíveis sem o notebook.");reloadLocal()
        controllerManager=getSystemService(INPUT_SERVICE) as InputManager;controllerManager.registerInputDeviceListener(this,null);updateControllerOrientation()
    }
    private fun updateControllerOrientation() {
        val present=InputDevice.getDeviceIds().asSequence().mapNotNull { InputDevice.getDevice(it) }.any { !it.isVirtual && (it.supportsSource(InputDevice.SOURCE_GAMEPAD) || it.supportsSource(InputDevice.SOURCE_JOYSTICK)) }
        val orientation=if(present)ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE else ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        if(requestedOrientation!=orientation)requestedOrientation=orientation
    }
    override fun onInputDeviceAdded(deviceId:Int)=updateControllerOrientation()
    override fun onInputDeviceRemoved(deviceId:Int)=updateControllerOrientation()
    override fun onInputDeviceChanged(deviceId:Int)=updateControllerOrientation()
    override fun onDestroy() { updateLocalStatus=null;if(::controllerManager.isInitialized)controllerManager.unregisterInputDeviceListener(this);super.onDestroy() }
    private fun reloadLocal(after:(()->Unit)?=null) {
        work.execute {
            val problems=mutableListOf<String>()
            val roms=store.folders.keys.flatMap { code -> runCatching { store.files(code) }.getOrElse { problems.add(store.folders.getValue(code));emptyList() } }
            val all=store.bind(catalog,roms)
            runOnUiThread { games=all;localProblems=problems;localScanAt=System.currentTimeMillis();render();updateLocalStatus?.invoke();after?.invoke() }
        }
    }
    private fun render() {
        if(!::grid.isInitialized)return
        val focusedKey=(currentFocus?.tag as? Game)?.key
        val query=GameLogic.normalized(search.text.toString())
        val visible=games.filter { game -> (collection!="cell" || game.localUri!=null) && (collection!="favorites" || store.prefs.getBoolean("favorite:${game.key}",false)) && (query.isBlank() || GameLogic.normalized(game.name+game.platform+game.genre).contains(query)) }
        val count=((visible.size+23)/24).coerceAtLeast(1);pageCount=count;page=page.coerceIn(0,count-1);counter.text="${page+1}/$count · ${visible.size} jogos"
        val compact=resources.configuration.orientation==2
        grid.removeAllViews();val width=resources.displayMetrics.widthPixels/resources.displayMetrics.density
        val columns=if(width>=900)4 else if(width>=600)3 else 2;grid.columnCount=columns
        for(game in visible.drop(page*24).take(24)) {
            val card=column().apply { isFocusable=true;isClickable=true;descendantFocusability=ViewGroup.FOCUS_BLOCK_DESCENDANTS;tag=game;background=shape();setOnClickListener { details(game) };setOnFocusChangeListener { _,focused -> background=shape(focused) } }
            if(compact)card.setPadding(dp(8),dp(4),dp(8),dp(4))
            val cover=ImageView(this).apply { setImageResource(com.pyretro.app.R.drawable.ic_pyretro);scaleType=ImageView.ScaleType.FIT_CENTER;contentDescription=game.name }
            card.addView(cover,LinearLayout.LayoutParams(-1,dp(if(compact)70 else 150)))
            card.addView(text((if(store.prefs.getBoolean("favorite:${game.key}",false))"★ " else "")+game.name,16f).apply { maxLines=if(compact)1 else 2;ellipsize=android.text.TextUtils.TruncateAt.END;setTypeface(null,Typeface.BOLD) })
            card.addView(text((if(compact)store.folders[game.code] ?: game.platform else game.platform)+" · "+(if(game.localUri!=null)"Neste celular" else if(store.prefs.contains("cloud:${game.key}"))"Na nuvem" else if(game.pcLocal)"No notebook" else "Catálogo"),12f).apply { maxLines=if(compact)1 else 2;ellipsize=android.text.TextUtils.TruncateAt.END })
            val params=GridLayout.LayoutParams(GridLayout.spec(GridLayout.UNDEFINED),GridLayout.spec(GridLayout.UNDEFINED,1f)).apply { this.width=0;setMargins(dp(4),dp(4),dp(4),dp(4)) };grid.addView(card,params)
            images.execute { val file=runCatching { store.cover(game) }.getOrNull();if(file!=null) { val bitmap=BitmapFactory.decodeFile(file.path,BitmapFactory.Options().apply { inSampleSize=2 });if(bitmap!=null)runOnUiThread { cover.setImageBitmap(bitmap) } } }
        }
        if(visible.isEmpty())grid.addView(text(if(collection=="cell")"Selecione as pastas em Opções. Jogos locais funcionam sem Tailscale ou notebook." else "Carregue o catálogo uma vez ou marque seus favoritos. Sem conexão, o cache continua disponível.",17f))
        if(focusedKey!=null) {
            val next=(0 until grid.childCount).map { grid.getChildAt(it) }.firstOrNull { (it.tag as? Game)?.key==focusedKey } ?: grid.getChildAt(0)
            next?.requestFocus()
        }
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
        val box=column();box.addView(text("Pesquisar · X apaga · Menu confirma",18f))
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
        headingBar.visibility=if(landscape)View.GONE else View.VISIBLE;compactOptions.visibility=if(landscape)View.VISIBLE else View.GONE
        quickBar.visibility=if(landscape)View.GONE else View.VISIBLE;controlHint.visibility=if(landscape)View.GONE else View.VISIBLE
        status.maxLines=if(landscape)1 else 4;search.layoutParams.height=dp(if(landscape)48 else 52)
    }
    private fun draw() {
        val pool=games.filter { (collection!="cell" || it.localUri!=null) && (collection!="favorites" || store.prefs.getBoolean("favorite:${it.key}",false)) }
        if(pool.isEmpty()) { message("Nenhum jogo nesta coleção para sortear.");return }
        val platforms=listOf("Todos os sistemas")+pool.map { it.platform }.distinct().sorted()
        val genres=listOf("Qualquer gênero")+pool.map { it.genre }.filter { it.isNotBlank() }.distinct().sorted()
        val system=Spinner(this);system.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,platforms)
        val genre=Spinner(this);genre.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,genres)
        val box=column();box.addView(text("Sortear desta coleção",22f));box.addView(system);box.addView(genre)
        add(box,button("Sortear e sugerir como jogar") {
            val selected=pool.filter { (system.selectedItemPosition==0 || it.platform==system.selectedItem) && (genre.selectedItemPosition==0 || it.genre==genre.selectedItem) }.randomOrNull()
            if(selected==null)message("Nenhum jogo com esses filtros.") else details(selected)
        });show(AlertDialog.Builder(this).setView(box).setNegativeButton("Voltar",null))
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
    private fun changeCollection(step:Int) { val now=SystemClock.elapsedRealtime();if(dialog==null && now-lastCollectionAt>=180) { lastCollectionAt=now;val ids=listOf("cell","catalog","favorites");collection=ids[(ids.indexOf(collection)+step+3)%3];page=0;render();grid.getChildAt(0)?.requestFocus() } }
    private fun toggleFavorite(game:Game) { store.prefs.edit().putBoolean("favorite:${game.key}",!store.prefs.getBoolean("favorite:${game.key}",false)).apply();render() }
    private fun details(game:Game) {
        val box=column();box.addView(text(game.name,22f).apply { setTypeface(null,Typeface.BOLD) });box.addView(text(game.platform+" · "+(if(game.localUri!=null)"Disponível neste celular" else "Escolha onde jogar"),14f))
        if(game.localUri!=null)add(box,button("Jogar neste celular") { dialog?.dismiss();launchLocal(game) })
        if(game.code in CoreProfiles.choices)add(box,button("Escolher core do RetroArch") { chooseCore(game.code) })
        if(game.code=="PS")add(box,button("Abrir DuckStation · escolher jogo") { dialog?.dismiss();openPackage("com.github.stenzek.duckstation") })
        GameLogic.remotePackage(game.platform)?.let { target -> add(box,button(if(target=="com.grill.xbxplay")"Abrir XBXPlay" else "Abrir Remote Play oficial") { dialog?.dismiss();openPackage(target) }) }
        if(game.code in store.folders) {
            add(box,button("Selecionar ROM no celular") { dialog?.dismiss();pickRom(game,false) })
            if(store.prefs.contains("cloud:${game.key}"))add(box,button("Baixar ROM vinculada e jogar") { dialog?.dismiss();download(game) })
            add(box,button("Vincular ROM no Drive") { dialog?.dismiss();pickRom(game,true) })
        }
        if(game.code in setOf("PS","PSP","3DS"))add(box,button("Texturas deste sistema") { textures(game) })
        if(!game.key.startsWith("local:") && game.code !in setOf("NDS","3DS"))add(box,button(if(game.platform in setOf("Nintendo Switch","Switch"))"Switch Lite pelo notebook · Moonlight" else "Abrir Moonlight / notebook") { dialog?.dismiss();notebook(game) })
        add(box,button(if(store.prefs.getBoolean("favorite:${game.key}",false))"★ Remover favorito" else "☆ Favoritar") { toggleFavorite(game);details(game) })
        val tracking=store.tracking(game)
        for((field,label) in listOf("iniciado" to "Iniciado","finalizado" to "Finalizado","platinado" to "Platinado"))add(box,button((if(tracking.optBoolean(field))"✓ " else "○ ")+label) {
            store.setProgress(game,field,!tracking.optBoolean(field))
            if(GameLogic.offerRemoval(tracking.optBoolean("finalizado"),store.tracking(game).optBoolean("finalizado"),game.localUri!=null))offerRomRemoval(game) else details(game)
        })
        if(game.localUri!=null)add(box,button("Remover ROM deste celular") { offerRomRemoval(game) })
        val minutes=store.prefs.getLong("time:${game.key}",0)/60
        box.addView(text("$minutes min registrados neste celular. Alterações ficam aqui até você sincronizar com o notebook.",12f))
        val scroll=ScrollView(this).apply { addView(box) }
        show(AlertDialog.Builder(this).setView(scroll).setNegativeButton("Voltar",null))
    }
    private fun offerRomRemoval(game:Game) {
        show(AlertDialog.Builder(this).setTitle("Remover ROM do celular?").setMessage("${game.name}\n\nExcluir apenas a ROM local para liberar espaço? Progresso, saves, states, BIOS, texturas e a origem no PC/Drive serão preservados. Você pode baixar o jogo novamente depois.").setNegativeButton("Manter ROM") { _,_ -> details(game) }.setPositiveButton("Excluir ROM local") { _,_ ->
            message("Removendo somente a ROM local…")
            work.execute { runCatching { store.removeLocal(game);PlaylistStore(store).afterChange(game.code) }.onSuccess { playlist -> runOnUiThread { message("ROM removida do celular. Histórico e saves preservados. $playlist");reloadLocal() } }.onFailure { runOnUiThread { failure(it) } } }
        })
    }
    private fun settings() {
        val box=column();box.addView(text("Seu PyRetro",23f));box.addView(text("O banco fica no PC. Pastas locais, cache, progresso e tempo funcionam offline. Tailscale é usado para consultar/sincronizar o notebook.",14f))
        add(box,button("Situação e conexões") { statusCenter() })
        add(box,button("Xbox · XBXPlay") { openPackage("com.grill.xbxplay") });add(box,button("PS4 · Remote Play oficial") { openPackage("com.playstation.remoteplay") });add(box,button("PC · Moonlight") { openPackage("com.limelight") })
        add(box,button("3DS · abrir Lime3DS / Azahar") { val target=listOf("io.github.lime3ds.android","io.github.azahar_emu.azahar").firstOrNull { packageManager.getLaunchIntentForPackage(it)!=null };if(target!=null)openPackage(target) else message("Emulador 3DS não encontrado.") })
        val server=EditText(this).apply { setSingleLine();setText(store.base());hint="https://endereço-do-pyretro";setTextColor(appForeground);setHintTextColor(Color.LTGRAY) };box.addView(server)
        add(box,button("Salvar endereço") { runCatching { store.setBase(server.text.toString());message("Endereço salvo. O modo offline continua disponível.") }.onFailure(::failure) })
        add(box,button("Carregar catálogo do notebook") { runCatching { store.setBase(server.text.toString()) }.onFailure { failure(it);return@button };refreshCatalog() })
        add(box,button("Sincronizar progresso e tempo (${store.pending()})") { syncTracking() })
        add(box,button("Saves, estados e runtime") { syncFiles() })
        add(box,button("Playlists do RetroArch") { playlists() })
        add(box,button("Catálogo da nuvem / Drive") { cloudMenu() })
        add(box,button("Downloads · continuar / pausar") { downloads() })
        add(box,button("Pasta Jogos · reconhecer todos os sistemas") { dialog?.dismiss();pickFolder("ROOT") })
        for((code,label) in store.folders)add(box,button("Pasta · $label") { dialog?.dismiss();pickFolder(code) })
        box.addView(text("Drive: use o seletor Android para vincular arquivos. ROMs baixadas ficam na pasta escolhida e funcionam offline. PS1 sob demanda aceita CHD/PBP, que contêm o jogo num arquivo.",13f))
        add(box,button("Cores do RetroArch por sistema") { chooseCore() })
        box.addView(text("Galileo G8: A escolhe, B volta, X favorita, Y busca, LB/RB mudam de página; LT/RT trocam a coleção. Os mesmos botões também respondem ao touch.",13f))
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun refreshCatalog() {
        dialog?.dismiss();message("Consultando notebook…")
        work.execute { runCatching { store.refresh() }.onSuccess { fresh -> runOnUiThread {
            catalog=fresh;message("Catálogo atualizado. As capas são guardadas conforme você navega.");reloadLocal()
        } }.onFailure { store.online=false;runOnUiThread { failure(it) } } }
    }
    private fun syncTracking() {
        dialog?.dismiss();message("Sincronizando alterações escolhidas…")
        work.execute { runCatching { store.synchronize() }.onSuccess { result -> val fresh=store.cached();runOnUiThread {
            catalog=fresh;message(result);reloadLocal()
        } }.onFailure { runOnUiThread { failure(it) } } }
    }
    private fun statusCenter() {
        val box=column();val helper=StatusStore(store);val pending=helper.pending();val prefs=store.prefs
        fun section(title:String,value:String):TextView { box.addView(text(title,19f).apply { setTypeface(null,Typeface.BOLD) });return text(value,14f).also(box::addView) }
        fun date(key:String)=prefs.getLong(key,0).takeIf { it>0 }?.let(::versionDate) ?: "ainda não registrado"
        box.addView(text("Situação e conexões",23f))
        fun localSummary()="${games.count { it.localUri!=null }} jogo(s) na última leitura local · ${catalog.size} entrada(s) no catálogo em cache.\nCatálogo atualizado: ${date("updated")}. Favoritos, progresso e tempo ficam neste app. Capas consultadas dependem do cache do Android."
        fun readSummary()=if(localScanAt==0L)"Leitura local ainda em andamento." else "Leitura local em ${versionDate(localScanAt)}."+
            if(localProblems.isEmpty())"" else " Lista parcial: falha ao ler ${localProblems.joinToString()}. Confira as pastas e permissões."
        val availability=section("Disponível offline",localSummary())
        val localRead=text(readSummary(),13f);box.addView(localRead)
        add(box,button("Ver jogos neste celular") { dialog?.dismiss();collection="cell";page=0;render() })
        add(box,button("Reler pastas locais") { dialog?.dismiss();reloadLocal { statusCenter() } })
        val connectionRecord=section("Notebook / Tailscale",helper.connectionSummary(::versionDate))
        val connection=text("",14f);box.addView(connection)
        val test=button("Testar conexão com notebook") {};box.addView(test)
        add(box,button("Configurar endereço / abrir Opções") { settings() })
        add(box,button("Atualizar catálogo do notebook") { refreshCatalog() })
        add(box,button("Emuladores, clientes e Tailscale") { connectionApps() })
        section("Progresso e tempo","${pending.count { !it.time }} alteração(ões) de progresso · ${pending.count { it.time }} sessão(ões) de tempo pendente(s).\n${pending.count { it.conflict }} pendência(s) exigiram conferência na última sincronização.\nÚltima sincronização concluída: ${date("tracking-sync-at")}.")
        prefs.getString("tracking-sync-result",null)?.let { box.addView(text(it,13f)) }
        add(box,button("Conferir alterações pendentes") { pendingChanges() })
        add(box,button("Sincronizar progresso e tempo") { syncTracking() })
        val sync=FileSync(store)
        section("Saves, estados e runtime","Analisar compara arquivos; aplicar copia somente as escolhas confirmadas. Os registros abaixo descrevem a última operação, não verificam mudanças posteriores.")
        for((group,label) in sync.groups) {
            val observation=sync.observation(group)
            box.addView(text(label+" · "+if(observation==null)"sem análise para estas pastas/endereço." else
                "${if(observation.optBoolean("applied"))"Aplicação" else "Análise"} em ${versionDate(observation.getLong("at"))}: ${observation.getInt("conflicts")} conflito(s), ${observation.getInt("failures")} falha(s).",13f))
        }
        add(box,button("Analisar / resolver sincronização de arquivos") { syncFiles() })
        section("Pastas e permissões","Confira as concessões persistentes de leitura e escrita. Uma concessão salva não comprova que a pasta ainda existe. Pastas padrão de saves ainda ausentes só são criadas ao aplicar uma cópia. Escolha Jogos ou pastas individuais.")
        add(box,button("Conferir / escolher pastas") { folderStatuses() })
        section("Nuvem / Drive","${prefs.all.keys.count { it.startsWith("cloud:") }} vínculo(s) de ROM salvo(s). O índice guarda nomes; baixar depende da internet e da permissão do provedor. Abrir esta central não acessa o Drive.")
        add(box,button("Conferir índice e origens da nuvem") { cloudMenu() })
        section("Downloads","Cópias parciais ficam no app até continuar ou descartar explicitamente.")
        val partials=text("Consultando checkpoints locais…",14f);box.addView(partials)
        add(box,button("Continuar / pausar downloads") { downloads() })
        add(box,button("Playlists do RetroArch") { playlists() })
        val opened=show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Fechar",null))
        updateLocalStatus={ if(dialog===opened) { availability.text=localSummary();localRead.text=readSummary() } }
        test.isEnabled=store.base().isNotBlank()
        test.setOnClickListener {
            test.isEnabled=false;connection.text="Testando conexão…"
            work.execute { val result=runCatching { store.checkConnection() };runOnUiThread {
                if(dialog===opened && !isFinishing && !isDestroyed) {
                    connectionRecord.text=helper.connectionSummary(::versionDate)
                    test.isEnabled=true;connection.text=if(result.isSuccess)"PyRetro respondeu em ${versionDate(System.currentTimeMillis())}." else "Não foi possível confirmar o PyRetro. Confira endereço, notebook e Tailscale. Seus dados offline continuam disponíveis."
                }
            } }
        }
        images.execute { val result=runCatching { DownloadStore(store).jobs() };runOnUiThread {
            if(dialog===opened && !isFinishing && !isDestroyed)partials.text=result.fold(
                { jobs -> "${jobs.size} cópia(s) parcial(is) · ${android.text.format.Formatter.formatFileSize(this,jobs.sumOf { it.getLong("bytes") })} no armazenamento privado." },
                { "Não foi possível ler os checkpoints. Abra Downloads para conferir; nenhum parcial foi descartado." })
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
        paged("Pastas e permissões",StatusStore(store).folders().map { folder ->
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
    private fun remoteVersions(group:String) {
        dialog?.dismiss();message("Consultando versões no notebook…")
        work.execute { runCatching { JSONObject(store.request("/api/mobile/sync/history?group="+Uri.encode(group))) }.onSuccess { result -> runOnUiThread {
            val versions=result.getJSONArray("versions")
            paged("Versões no notebook",(0 until versions.length()).map { versions.getJSONObject(it) }.map { version ->
                "${versionDate(version.getLong("created"))} · ${version.getString("path")} · ${version.getLong("size")} B" to {
                    show(AlertDialog.Builder(this).setTitle("Restaurar no notebook?").setMessage("${version.getString("path")}\nFeche o emulador no notebook. O arquivo atual será preservado. Esta ação restaura no PC; para receber no celular, analise o grupo depois.").setNegativeButton("Cancelar",null).setPositiveButton("Restaurar") { _,_ ->
                        val request=JSONObject().put("group",group).put("rootTag",result.getString("rootTag")).put("path",version.getString("path")).put("version",version.getString("version")).put("sha256",version.getString("sha256")).put("expected",version.getString("current"))
                        work.execute { runCatching { store.request("/api/mobile/sync/restore",request) }.onSuccess { runOnUiThread { message("Versão restaurada no notebook. Analise o grupo antes de sincronizar.") } }.onFailure { runOnUiThread { failure(it) } } }
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
            show(AlertDialog.Builder(this).setView(box).setNegativeButton("Voltar",null));Unit
        } }+listOf("Último resultado" to { show(AlertDialog.Builder(this).setTitle("Playlists").setMessage(store.prefs.getString("playlist-last","Nenhuma atualização aplicada.")).setPositiveButton("Fechar",null));Unit }))
    }
    private fun analyzePlaylist(code:String,label:String) {
        dialog?.dismiss();message("Analisando playlist de $label…")
        work.execute { runCatching { PlaylistStore(store).plan(code) }.onSuccess { plan -> runOnUiThread {
            val box=column();box.addView(text(plan.name,20f))
            box.addView(text("${plan.added} entrada(s) nova(s), ${plan.removed} ausente(s) da pasta local a retirar. Campos das entradas mantidas e itens de outras pastas serão preservados. O arquivo atual fica no histórico. Feche o RetroArch antes de aplicar.",14f))
            val auto=CheckBox(this).apply { text="Atualizar também após baixar/remover uma ROM pelo PyRetro";isChecked=store.prefs.getBoolean("playlist-auto:$code",false);minHeight=dp(48);setTextColor(appForeground) };box.addView(auto)
            show(AlertDialog.Builder(this).setView(box).setNegativeButton("Cancelar",null).setPositiveButton("Aplicar") { _,_ ->
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
    private fun downloads() {
        val box=column();box.addView(text("Downloads",22f))
        box.addView(text("Cópias parciais ficam no armazenamento privado do app. Continuar confere o trecho já baixado; o provedor pode reler esse trecho. Nada é publicado antes de concluir. Sem serviço de download em segundo plano.",14f))
        add(box,button("Pausar download em andamento") { DownloadStore.pause();message("Pausa solicitada; a cópia parcial será preservada.") })
        add(box,button("Ver cópias parciais") {
            dialog?.dismiss()
            work.execute { runCatching { DownloadStore(store).jobs() }.onSuccess { jobs -> runOnUiThread {
                paged("Cópias parciais",jobs.map { job -> "${job.optString("title")} · ${job.getLong("bytes")/1024/1024} MB" to {
                    val game=games.find { it.key==job.getString("key") } ?: Game("",job.getString("key"),job.getString("title"),store.folders[job.getString("code")] ?: "",job.getString("code"))
                    show(AlertDialog.Builder(this).setTitle(game.name).setMessage("Continuar a cópia ou descartar somente o checkpoint deste download? O jogo existente e a origem não serão apagados.").setNegativeButton("Voltar",null).setNeutralButton("Descartar parcial") { _,_ ->
                        work.execute { runCatching { DownloadStore(store).discard(game.key) }.onSuccess { runOnUiThread { message("Cópia parcial descartada.") } }.onFailure { runOnUiThread { failure(it) } } }
                    }.setPositiveButton("Continuar e jogar") { _,_ -> download(game) });Unit
                } })
            } }.onFailure { runOnUiThread { failure(it) } } }
        })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun pickSyncFolder(group:String) {
        syncPicking=group;dialog?.dismiss()
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            .putExtra(DocumentsContract.EXTRA_INITIAL_URI,DocumentsContract.buildDocumentUri("com.android.externalstorage.documents","primary:RetroArch")),13)
    }
    private fun syncFiles() {
        val sync=FileSync(store);val box=column();box.addView(text("Saves, estados e runtime",22f))
        box.addView(text("Feche os emuladores nas duas pontas. Analise antes de copiar. Arquivos diferentes na primeira sincronização ou alterados nos dois lados exigem sua escolha. Nenhum save é apagado automaticamente.",14f))
        box.addView(text("Estados exigem core/versão compatíveis. Runtime é sincronizado como arquivo: os tempos acumulados não são somados. 3DS inclui apenas saves/extdata da SDMC, sem jogos instalados, NAND ou firmware.",13f))
        add(box,button("Escolher pasta RetroArch") { pickSyncFolder("retroarch") })
        for((group,label) in sync.groups)add(box,button(label) {
            val item=column();item.addView(text(label,22f));item.addView(text(if(sync.tree(group)==null)"Escolha a pasta local para continuar." else "Pasta local definida. Notebook via HTTPS/Tailscale; jogar continua disponível offline.",14f))
            add(item,button("Escolher pasta deste grupo") { pickSyncFolder(group) })
            add(item,button("Versões deste celular") { localVersions(group) })
            add(item,button("Versões do notebook") { remoteVersions(group) })
            add(item,button("Analisar sem copiar") {
                dialog?.dismiss();message("Comparando arquivos de $label…")
                work.execute { runCatching { sync.analyze(group) }.onSuccess { plan -> runOnUiThread { reviewSync(plan) } }.onFailure { runOnUiThread { failure(it) } } }
            });show(AlertDialog.Builder(this).setView(item).setNegativeButton("Voltar",null))
        })
        add(box,button("Último resultado") { show(AlertDialog.Builder(this).setTitle("Sincronização de arquivos").setMessage(sync.lastResult()).setPositiveButton("Voltar") { _,_ -> syncFiles() }) })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun reviewSync(plan:SyncPlan) {
        val box=column();box.addView(text(FileSync(store).groups[plan.group] ?: plan.group,22f))
        val actions=plan.rows.count { it.choice in setOf("upload","download") };val conflicts=plan.rows.count { it.kind=="conflict" && it.choice=="conflict" }
        box.addView(text("$actions transferência(s) escolhida(s) · $conflicts conflito(s) adiado(s) · ${plan.rows.count { it.kind=="same" }} arquivo(s) iguais. Versões anteriores são preservadas. Feche os emuladores antes de aplicar.",14f))
        for(row in plan.rows.filter { it.kind!="same" }) {
            val direction=when(row.choice) { "upload" -> "Celular → notebook";"download" -> "Notebook → celular";else -> "Conferir conflito" }
            if(row.kind=="conflict")add(box,button("$direction · ${row.path}") {
                val options=mutableListOf("Adiar" to "conflict")
                if(row.local!=null)options.add("Usar versão do celular (${row.local.size} B)" to "upload")
                if(row.remote!=null)options.add("Usar versão do notebook (${row.remote.getLong("size")} B)" to "download")
                show(AlertDialog.Builder(this).setTitle(row.path).setItems(options.map { it.first }.toTypedArray()) { _,which -> row.choice=options[which].second;reviewSync(plan) }.setNegativeButton("Voltar") { _,_ -> reviewSync(plan) })
            }) else box.addView(text("$direction · ${row.path}",13f))
        }
        add(box,button("Aplicar escolhas e registrar comparação") {
            show(AlertDialog.Builder(this).setTitle("Aplicar sincronização?").setMessage("$actions transferência(s). Feche os emuladores no celular e no notebook. Cada arquivo será conferido novamente; conflitos adiados ficam preservados. Versões diferentes substituídas ficam no histórico da pasta.").setNegativeButton("Voltar") { _,_ -> reviewSync(plan) }.setPositiveButton("Aplicar") { _,_ ->
                message("Sincronizando arquivos…")
                work.execute { runCatching { FileSync(store).apply(plan) { status -> runOnUiThread { message(status) } } }.onSuccess { result -> runOnUiThread { message(result.lineSequence().first());show(AlertDialog.Builder(this).setTitle("Resultado").setMessage(result).setPositiveButton("Fechar",null)) } }.onFailure { runOnUiThread { failure(it) } } }
            })
        })
        show(AlertDialog.Builder(this).setView(ScrollView(this).apply { addView(box) }).setNegativeButton("Voltar",null))
    }
    private fun coreId(code:String)=CoreProfiles.id(code,store.prefs.getString("core:$code",if(code=="NDS")store.prefs.getString("nds-core",null) else null))
    private fun chooseCore(code:String?=null) {
        if(code==null) {
            val codes=CoreProfiles.choices.keys.toList()
            show(AlertDialog.Builder(this).setTitle("Sistema do RetroArch").setItems(codes.map { store.folders[it] ?: it }.toTypedArray()) { _,which -> chooseCore(codes[which]) }.setNegativeButton("Voltar",null));return
        }
        val choices=CoreProfiles.choices.getValue(code)
        show(AlertDialog.Builder(this).setTitle("${store.folders[code]} · core já instalado").setSingleChoiceItems(choices.map { it.second }.toTypedArray(),choices.indexOfFirst { it.first==coreId(code) }) { opened,which ->
            store.prefs.edit().putString("core:$code",choices[which].first).apply();opened.dismiss();message("${choices[which].second} escolhido para ${store.folders[code]}. Precisa estar instalado no RetroArch.")
        }.setNegativeButton("Voltar",null))
    }
    private fun pickFolder(code:String) { pickingCode=code;startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),10) }
    private fun pickRom(game:Game,cloud:Boolean) { pickingGame=game;pickingCloud=cloud;startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),11) }
    @Deprecated("Compatibilidade com Activity sem dependências extras")
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(requestCode,resultCode,data);if(resultCode!=RESULT_OK || data==null)return
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
        if(requestCode==10) { store.saveTree(pickingCode,uri);val pending=downloadAfterFolder;downloadAfterFolder=null;reloadLocal { if(pending!=null)download(pending) } }
        if(requestCode==11) {
            val game=pickingGame ?: return;val name=store.displayName(uri)
            if(!pickingCloud && uri.authority!="com.android.externalstorage.documents") { message("Escolha uma ROM no armazenamento local. Para o Drive, use Vincular ROM no Drive e depois baixe.");return }
            if(!store.accepts(game.code,name)) { message("Esse formato não corresponde a ${game.code}.");return }
            show(AlertDialog.Builder(this).setTitle("Vincular arquivo").setMessage("Usar $name para ${game.name}?").setNegativeButton("Cancelar",null).setPositiveButton("Vincular") { _,_ ->
                val edit=store.prefs.edit().putString((if(pickingCloud)"cloud:" else "rom:")+game.key,uri.toString())
                if(pickingCloud)edit.remove("cloud-auto:${game.code}:${game.key}")
                edit.apply()
                if(pickingCloud)message("ROM vinculada. Use Baixar ROM vinculada e jogar quando quiser.") else game.localUri=uri
                reloadLocal { details(game) }
            })
        }
    }
    override fun onConfigurationChanged(newConfig:android.content.res.Configuration) { super.onConfigurationChanged(newConfig);adaptLayout();render() }
    private fun download(game:Game) {
        if(store.tree(game.code)==null) { downloadAfterFolder=game;pickFolder(game.code);return }
        message("Baixando ${game.name} pelo provedor de arquivos…");var update=0L
        work.execute { runCatching { store.download(game) { bytes -> val now=SystemClock.elapsedRealtime();if(now-update>500) { update=now;runOnUiThread { message("Baixando ${game.name}: ${bytes/1024/1024} MB") } } } }.onSuccess { uri -> game.localUri=uri;val playlist=PlaylistStore(store).afterChange(game.code);runOnUiThread { message("Download concluído. Disponível offline. $playlist");reloadLocal { launchLocal(game) } } }.onFailure { runOnUiThread { failure(it) } } }
    }
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
    override fun onPause() { super.onPause();scanOnResume=true;if(activeGame!=null)leftForGame=true }
    override fun onResume() {
        super.onResume();if(scanOnResume) { scanOnResume=false;reloadLocal() };val game=activeGame ?: return
        if(!leftForGame)return
        activeGame=null;leftForGame=false
        val elapsed=(SystemClock.elapsedRealtime()-launchedAt)/60000
        if(elapsed<1)return
        val minutes=EditText(this).apply { inputType=android.text.InputType.TYPE_CLASS_NUMBER;setText(elapsed.coerceAtMost(1440).toString()) }
        show(AlertDialog.Builder(this).setTitle("Registrar tempo de ${game.name}?").setMessage("Confirme os minutos que jogou. O tempo em outros apps pode estar incluído.").setView(minutes).setNegativeButton("Descartar",null).setPositiveButton("Salvar no celular") { _,_ ->
            val value=minutes.text.toString().toIntOrNull()
            if(value!=null && value in 1..1440) { store.addTime(game,value);message("Tempo salvo offline. Sincronize quando quiser.") } else message("Use entre 1 e 1440 minutos.")
        })
    }
    override fun onKeyDown(keyCode:Int,event:KeyEvent):Boolean {
        if(event.repeatCount>0 && keyCode in setOf(KeyEvent.KEYCODE_BUTTON_A,KeyEvent.KEYCODE_BUTTON_X,KeyEvent.KEYCODE_BUTTON_START))return true
        when(keyCode) {
            KeyEvent.KEYCODE_BUTTON_A -> { currentFocus?.performClick();return true }
            KeyEvent.KEYCODE_BUTTON_B -> { if(dialog!=null)dialog?.dismiss() else if(search.text.isNotEmpty())search.text.clear() else { collection="cell";page=0;render() };return true }
            KeyEvent.KEYCODE_BUTTON_X -> { (currentFocus?.tag as? Game)?.let(::toggleFavorite);return true }
            KeyEvent.KEYCODE_BUTTON_Y -> { if(event.repeatCount==0)controllerSearch();return true }
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
