package com.pyretro.app

import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

/** Regras sem Android dos saves pelo Drive (contrato `docs/drive-saves.md`). */
object DriveSaveRules {
    /** Pasta de cada grupo dentro de Jogos/Saves, igual ao `mobile_sync` do notebook. */
    val GROUP_PATHS=linkedMapOf("retro-saves" to listOf("saves"),"retro-states" to listOf("states"),"retro-runtime" to listOf("runtime-logs"),
        "psp-saves" to listOf("PPSSPP","SAVEDATA"),"psp-states" to listOf("PPSSPP","PPSSPP_STATE"),"3ds-saves" to listOf("Lime3DS","sdmc"))
    val SAVES=listOf("Jogos","Saves")
    const val PENDING=".pyretro-pending"
    /** JSON compacto com escapes ASCII, como `json.dumps(..., ensure_ascii=True, separators=(',',':'))`. */
    fun json(value:String)=buildString {
        append('"')
        for(c in value) when {
            c=='"' -> append("\\\"");c=='\\' -> append("\\\\");c=='\n' -> append("\\n");c=='\r' -> append("\\r");c=='\t' -> append("\\t")
            c=='\b' -> append("\\b");c=='\u000c' -> append("\\f");c.code<0x20 || c.code>0x7e && c.code!=0x7f -> append("\\u%04x".format(c.code))
            else -> append(c)
        }
        append('"')
    }
    fun identity(account:String,folder:String,group:String,tree:String):String {
        require(group in GROUP_PATHS && listOf(account,folder,tree).all { it.isNotEmpty() }) { "Identidade de sincronização inválida." }
        val encoded="[1,${json(account)},${json(folder)},${json(group)},${json(tree)}]"
        return MessageDigest.getInstance("SHA-256").digest(encoded.toByteArray()).joinToString("") { "%02x".format(it) }
    }
    /** Envio do celular que não pode sobrescrever o Drive: `.pyretro-pending/<caminho>/<ms>-<base>.pending`,
     *  onde base é o SHA-256 da versão do Drive que o celular viu (ou `none`). O notebook aplica. */
    fun pendingName(at:Long,base:String?)="$at-${base ?: "none"}.pending"
    private val pendingPattern=Regex("([0-9]{13})-([0-9a-f]{64}|none)\\.pending")
    fun parsePending(name:String):Pair<Long,String?>? = pendingPattern.matchEntire(name)?.let { it.groupValues[1].toLong() to it.groupValues[2].takeIf { b -> b!="none" } }
}

/** Saves e estados entre o celular e `Jogos/Saves` no Drive, sem o notebook. Drive → celular grava
 *  com histórico local; celular → Drive só cria arquivo novo ou deixa uma pendência para o notebook
 *  aplicar (o Drive não tem gravação condicional; ver o contrato). */
class DriveSaves(private val store:LibraryStore,private val drive:GoogleDrive,private val sync:FileSync) {
    private val prefs=store.context.getSharedPreferences("drive-saves",0)
    private fun hex(bytes:ByteArray)=bytes.joinToString("") { "%02x".format(it) }
    private fun hash(file:File)=MessageDigest.getInstance("SHA-256").let { d -> file.inputStream().use { i -> val b=ByteArray(1024*1024);while(true) { val n=i.read(b);if(n<0)break;d.update(b,0,n) } };hex(d.digest()) }
    private fun root(group:String,create:Boolean):String? {
        val saves=drive.folder(DriveSaveRules.SAVES)
        return if(create)drive.folder(DriveSaveRules.GROUP_PATHS.getValue(group),true,saves) else drive.folderOrNull(DriveSaveRules.GROUP_PATHS.getValue(group),saves)
    }
    /** Arquivos do grupo no Drive: caminho → {id,size,sha256}. Atalhos e nomes repetidos param a análise. */
    private fun remote(group:String,root:String?):Pair<Map<String,JSONObject>,Map<String,Set<String>>> {
        val files=linkedMapOf<String,JSONObject>();val pending=mutableMapOf<String,MutableSet<String>>()
        fun scan(folder:String,prefix:String,depth:Int,inPending:Boolean) {
            require(depth<=16) { "Pasta com níveis demais no Drive." }
            val rows=drive.children(folder);val names=rows.groupBy { it.getString("name") }
            names.filter { it.value.size>1 }.keys.firstOrNull()?.let { error("Nome repetido no Drive: $prefix$it. Resolva antes de sincronizar.") }
            for(row in rows) {
                val name=row.getString("name");val type=row.optString("mimeType")
                if(type=="application/vnd.google-apps.shortcut")error("Atalho no Drive em $prefix$name; saves não seguem atalhos.")
                if(type=="application/vnd.google-apps.folder") {
                    if(!inPending && prefix.isEmpty() && name==DriveSaveRules.PENDING)scan(row.getString("id"),"",depth+1,true)
                    else if(!name.startsWith(".pyretro-"))scan(row.getString("id"),"$prefix$name/",depth+1,inPending)
                    continue
                }
                if(inPending) { if(DriveSaveRules.parsePending(name)!=null && SyncRules.accepted(group,prefix.trimEnd('/')))
                    pending.getOrPut(prefix.trimEnd('/')) { mutableSetOf() }.add(row.optString("sha256Checksum")); continue }
                val path=prefix+name
                if(name.startsWith(".pyretro-") || !SyncRules.accepted(group,path))continue
                val sha=row.optString("sha256Checksum");require(sha.matches(Regex("[0-9a-f]{64}"))) { "O Drive não informou o SHA-256 de $path." }
                require(files.size<20000);files[path]=JSONObject().put("id",row.getString("id")).put("size",row.optString("size","0").toLong()).put("sha256",sha)
            }
        }
        if(root!=null)scan(root,"",0,false)
        return files to pending
    }
    private fun identity(group:String):String {
        val account=prefs.getString("account",null) ?: drive.accountId().also { prefs.edit().putString("account",it).apply() }
        return DriveSaveRules.identity(account,drive.folder(DriveSaveRules.SAVES),group,sync.tree(group).toString())
    }
    /** Mesma tabela de conflitos do notebook; envio que já está pendente aparece como "pending". */
    fun analyze(group:String,only:((String)->Boolean)?=null):SyncPlan {
        require(sync.tree(group)!=null) { "Escolha a pasta ${sync.groups[group]} no celular." }
        val id=identity(group);val baseline=JSONObject(prefs.getString("baseline:$id","{}")!!)
        val (remote,pending)=remote(group,root(group,false));val local=sync.local(group)
        val rows=(local.keys+remote.keys+baseline.keys().asSequence().toList()).distinct().filter { only==null || only(it) }.sorted().map { path ->
            val left=local[path];val right=remote[path];val previous=baseline.optString(path).takeIf { it.isNotBlank() }
            val direction=SyncRules.direction(left?.sha256,right?.getString("sha256"),previous)
            SyncRow(path,left,right,if(direction!="same" && left!=null && left.sha256 in pending[path].orEmpty())"pending" else direction)
        }
        return SyncPlan(group,"drive:"+drive.folder(DriveSaveRules.SAVES),id,rows,only!=null)
    }
    private fun download(group:String,row:SyncRow) {
        val source=row.remote ?: error("Sem versão no Drive.");val expected=source.getString("sha256")
        require(drive.file(source.getString("id")).optString("sha256Checksum")==expected) { "O save mudou no Drive depois da análise. Analise de novo." }
        val temp=File.createTempFile("drive-save-",".tmp",store.context.cacheDir)
        try {
            val connection=drive.media(source.getString("id"),0)
            try { require(connection.responseCode==200) { "Drive recusou o save (HTTP ${connection.responseCode})." };connection.inputStream.use { i -> temp.outputStream().use { o -> i.copyTo(o,1024*1024) } } } finally { connection.disconnect() }
            require(temp.length()==source.getLong("size") && hash(temp)==expected) { "Save chegou incompleto; o do celular foi preservado." }
            sync.install(group,row.path,temp,expected,row.local?.sha256)
        } finally { temp.delete() }
    }
    /** Devolve true se o arquivo ficou ativo no Drive (pode avançar a base) e false se virou pendência. */
    private fun upload(group:String,row:SyncRow,baseline:String?):Boolean {
        val source=row.local ?: error("Sem versão no celular.")
        val temp=File.createTempFile("drive-send-",".tmp",store.context.cacheDir)
        try {
            store.context.contentResolver.openInputStream(source.uri).use { i -> requireNotNull(i);temp.outputStream().use { o -> i.copyTo(o,1024*1024) } }
            require(temp.length()==source.size && hash(temp)==source.sha256) { "Save mudou durante a leitura. Feche o emulador e analise de novo." }
            val root=root(group,true)!!;val parts=row.path.split('/');val parent=drive.folder(parts.dropLast(1),true,root)
            if(row.remote==null && baseline==null && drive.children(parent).none { it.getString("name")==parts.last() }) {
                val made=drive.create(parent,parts.last(),temp)
                // Criação concorrente (outro aparelho/Insync): se agora há dois, o nosso vira pendência.
                if(drive.children(parent).count { it.getString("name")==parts.last() }==1 && made.optString("sha256Checksum")==source.sha256)return true
                drive.move(made.getString("id"),parent,drive.folder(listOf(DriveSaveRules.PENDING)+parts,true,root),DriveSaveRules.pendingName(System.currentTimeMillis(),null));return false
            }
            drive.create(drive.folder(listOf(DriveSaveRules.PENDING)+parts,true,root),DriveSaveRules.pendingName(System.currentTimeMillis(),row.remote?.getString("sha256")),temp)
            return false
        } finally { temp.delete() }
    }
    fun apply(plan:SyncPlan,progress:(String)->Unit):String {
        require(identity(plan.group)==plan.identity) { "Conta, pasta do Drive ou pasta do celular mudou. Analise de novo." }
        val baseline=JSONObject(prefs.getString("baseline:${plan.identity}","{}")!!);var done=0;var pending=0;var ignored=0;val errors=mutableListOf<String>()
        for(row in plan.rows) {
            try {
                when(row.choice) {
                    "download" -> { progress("Recebendo ${row.path}");download(plan.group,row);baseline.put(row.path,row.remote!!.getString("sha256"));done++ }
                    "upload" -> { progress("Enviando ${row.path}");if(upload(plan.group,row,baseline.optString(row.path).takeIf { it.isNotBlank() })) { baseline.put(row.path,row.local!!.sha256);done++ } else pending++ }
                    "same" -> (row.local?.sha256 ?: row.remote?.optString("sha256"))?.let { baseline.put(row.path,it) }
                    "pending" -> pending++
                    else -> ignored++
                }
                prefs.edit().putString("baseline:${plan.identity}",baseline.toString()).apply()
            } catch(error:Exception) { errors.add(row.path+": "+(error.message ?: "falha")) }
        }
        return "$done cópia(s) confirmada(s). $pending envio(s) aguardando o notebook aplicar no PC. $ignored conflito(s) adiado(s). ${errors.size} falha(s)."+
            if(errors.isEmpty())"" else "\n"+errors.take(30).joinToString("\n")
    }
}
