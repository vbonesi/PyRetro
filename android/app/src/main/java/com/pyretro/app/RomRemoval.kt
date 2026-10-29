package com.pyretro.app
import android.net.Uri
import android.provider.DocumentsContract
import java.util.UUID

/** Prévia refeita antes de agir. Local vai para nomes de lixeira recuperáveis na mesma pasta. */
class RomRemoval(private val store:LibraryStore) {
    private val saf=SafStorage(store,12L*1024*1024*1024);private val drive=GoogleDrive(store.context,store.prefs)
    private fun localFiles(code:String):Map<String,Uri> {
        val tree=store.tree(code) ?: return emptyMap();val base=saf.folder(tree,false) ?: return emptyMap();val out=linkedMapOf<String,Uri>()
        fun walk(parent:Uri,prefix:String,depth:Int) {
            require(depth<=16 && out.size<=20000)
            for((name,uri) in saf.children(tree,parent)) {
                if(name.startsWith('.'))continue
                require(BundleRules.safe(name));val path=prefix+name
                if(store.context.contentResolver.getType(uri)==DocumentsContract.Document.MIME_TYPE_DIR)walk(uri,"$path/",depth+1) else out[path]=uri
            }
        }
        walk(base,"",0);return out
    }
    private fun remoteFiles(code:String):Map<String,DriveRef> {
        val parent=drive.folderOrNull(DriveSource.ROMS+code,"root") ?: return emptyMap();val out=linkedMapOf<String,DriveRef>()
        fun walk(folder:String,prefix:String,depth:Int) {
            require(depth<=16 && out.size<=20000)
            for(row in drive.children(folder)) {
                val name=row.getString("name");if(name.startsWith('.'))continue;require(BundleRules.safe(name));val path=prefix+name
                if(row.optString("mimeType")==DocumentsContract.Document.MIME_TYPE_DIR || row.optString("mimeType")=="application/vnd.google-apps.folder")walk(row.getString("id"),"$path/",depth+1)
                else { require(path !in out);out[path]=DriveRef(row.getString("id"),path,row.optLong("size"),row.optString("md5Checksum",row.optString("sha256Checksum"))) }
            }
        }
        walk(parent,"",0);return out
    }
    private fun remoteText(ref:DriveRef):String {
        require(ref.size in 1..1024*1024);val connection=drive.media(ref.id,0)
        try { require(connection.responseCode==200);return connection.inputStream.use { input -> val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(65536)
            while(true) { val n=input.read(buffer);if(n<0)break;require(out.size()+n<=1024*1024);out.write(buffer,0,n) };String(out.toByteArray(),Charsets.UTF_8) } } finally { connection.disconnect() }
    }
    fun plan(game:Game,scope:String,running:Boolean=false):RemovalPlan {
        require(game.code in store.folders);val protected=mutableListOf<String>();val tracking=store.tracking(game)
        if(tracking.optBoolean("iniciado") && !tracking.optBoolean("finalizado"))protected.add("Jogo iniciado e não finalizado.")
        if(SpaceStore(store).pinned(game))protected.add("Jogo fixado para manter baixado.")
        if(running || DownloadQueue.get(store).contains(game.key))protected.add("Jogo em execução ou na fila de downloads.")
        val locals=localFiles(game.code);val localEntry=game.localUri?.let { selected -> locals.entries.singleOrNull { store.documentId(it.value)==store.documentId(selected) }?.key }
        val lp=localEntry?.let { BundleRules.removalPlan(it,locals.keys) { path -> String(saf.read(locals.getValue(path),1024*1024),Charsets.UTF_8) } }
        val local=lp?.remove.orEmpty().map { path -> val uri=locals.getValue(path);val hash=saf.fingerprint(uri);RemovalFile(path,uri.toString(),hash.size,hash.sha256) }
        val remoteResult=if(drive.connected)runCatching { remoteFiles(game.code) } else null
        val refs=if(scope=="local")remoteResult?.getOrNull() else remoteResult?.getOrThrow()
        val chosen=DriveSource.parse(store.prefs.getString("cloud:${game.key}",null))
        val remoteEntry=refs?.entries?.filter { it.value.id==chosen?.id }?.singleOrNull()?.key
            ?: refs?.keys?.filter { it==game.romName }?.singleOrNull()
            ?: refs?.keys?.filter { GameLogic.fileLabel(it)==game.romName }?.singleOrNull()
        if(scope!="local" && refs!=null && remoteEntry==null && refs.keys.any { GameLogic.fileLabel(it)==GameLogic.fileLabel(game.romName) })protected.add("Mais de uma região/formato no Drive. Vincule o arquivo correto na ficha.")
        val rp=remoteEntry?.let { BundleRules.removalPlan(it,refs!!.keys) { path -> remoteText(refs.getValue(path)) } }
        // Sem DAT de dependências não remover um possível pai de outros Arcade.
        if(game.code=="ARCADE" && ((locals.keys.size>1 && scope!="drive") || (refs.orEmpty().keys.size>1 && scope!="local")))protected.add("Arcade: dependências entre jogos ainda não verificadas neste aparelho. Use o notebook.")
        val remote=if(refs==null)null else rp?.remove.orEmpty().map { path -> val ref=refs.getValue(path);RemovalFile(path,ref.id,ref.size,ref.md5) }
        return RemovalRules.plan(scope,local,remote,lp?.preserve.orEmpty()+rp?.preserve.orEmpty(),protected,(lp?.complete!=false && rp?.complete!=false))
    }
    fun apply(game:Game,confirmed:RemovalPlan,running:Boolean=false):List<Pair<String,Result<Unit>>> = synchronized(SpaceStore.mutationLock) {
        val current=plan(game,confirmed.scope,running)
        val results=RemovalRules.apply(current,confirmed.token,confirmed.confirmation,local={ file ->
            val uri=Uri.parse(file.id);val old=store.displayName(uri)
            require(saf.fingerprint(uri).sha256==file.fingerprint) { "Arquivo local mudou depois da prévia." }
            val renamed=DocumentsContract.renameDocument(store.context.contentResolver,uri,".pyretro-trash-${UUID.randomUUID()}-$old") ?: error("Não foi possível mover para a lixeira local.")
            store.prefs.edit().putString("rom-trash:$renamed",old).commit()
        },remote={ file -> val latest=drive.metadata(file.id);require(latest.size==file.size && latest.md5==file.fingerprint) { "Arquivo do Drive mudou depois da prévia." };drive.trash(file.id) })
        val edit=store.prefs.edit()
        if(results.any { it.first.startsWith("Celular:") && it.second.isSuccess })edit.remove("rom:${game.key}")
        val removed=current.drive.filter { file -> results.any { it.first=="Drive: ${file.path}" && it.second.isSuccess } }.map { it.id }.toSet()
        if(removed.isNotEmpty()) {
            val rows=org.json.JSONArray(store.prefs.getString("drive-index:${game.code}","[]"));val kept=(0 until rows.length()).map { rows.getJSONObject(it) }.filter { it.optString("id") !in removed }
            edit.putString("drive-index:${game.code}",org.json.JSONArray(kept).toString())
            if(DriveSource.parse(store.prefs.getString("cloud:${game.key}",null))?.id in removed)edit.remove("cloud:${game.key}")
        };edit.apply()
        results
    }
    fun restore(uri:String) {
        val original=store.prefs.getString("rom-trash:$uri",null) ?: error("Registro de lixeira ausente.")
        val target=Uri.parse(uri);val current=store.displayName(target);require(current.startsWith(".pyretro-trash-"))
        val parentId=store.documentId(target).substringBeforeLast('/');val root=store.tree("ROOT") ?: store.folders.keys.mapNotNull { store.tree(it) }.firstOrNull { store.documentId(target).startsWith(store.documentId(it)+"/") } ?: error("Escolha a pasta Jogos novamente.")
        val parent=DocumentsContract.buildDocumentUriUsingTree(root,parentId)
        require(original !in saf.children(root,parent)) { "Já existe um arquivo com esse nome; as duas versões foram preservadas." }
        check(DocumentsContract.renameDocument(store.context.contentResolver,target,original)!=null);store.prefs.edit().remove("rom-trash:$uri").apply()
    }
}
