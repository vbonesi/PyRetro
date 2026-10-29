package com.pyretro.app

/**
 * [CloudStorage] sobre o Drive da conta conectada, dentro de uma pasta raiz (ex.: ["Jogos","PyRetro-Nuvem"]),
 * a mesma que o notebook usa pelo rclone (`drive:Jogos/PyRetro-Nuvem`). Nunca apaga de vez: `trash` usa a lixeira.
 */
class DriveCloudStorage(private val drive:GoogleDrive,private val root:List<String> = listOf("Jogos","PyRetro-Nuvem"),private val maxBytes:Int=512*1024*1024):CloudStorage {
    private val folderMime="application/vnd.google-apps.folder"

    private fun folderOf(dirs:List<String>,create:Boolean):String? =
        if(create)drive.folder(root+dirs,true) else drive.folderOrNull(root+dirs,"root")

    private fun split(path:String):Pair<List<String>,String> { val parts=CloudStorage.clean(path).split('/');return parts.dropLast(1) to parts.last() }

    private fun find(path:String):org.json.JSONObject? {
        val (dirs,name)=split(path);val folder=folderOf(dirs,false) ?: return null
        val matches=drive.children(folder).filter { it.getString("name")==name && it.optString("mimeType")!=folderMime }
        require(matches.size<=1) { "$path está duplicado no Drive; resolva antes de sincronizar." }
        return matches.singleOrNull()
    }

    override fun list(prefix:String):List<CloudEntry> {
        val dirs=if(prefix.isEmpty())emptyList() else CloudStorage.clean(prefix.trimEnd('/')).split('/')
        val start=folderOf(dirs,false) ?: return emptyList();val out=mutableListOf<CloudEntry>()
        fun walk(folder:String,base:String,depth:Int) {
            require(depth<=16) { "pastas fundas demais na nuvem" }
            for(row in drive.children(folder)) {
                val name=row.getString("name");val path=if(base.isEmpty())name else "$base/$name"
                if(row.optString("mimeType")==folderMime)walk(row.getString("id"),path,depth+1)
                else out.add(CloudEntry(path,row.optString("size","0").toLongOrNull() ?: 0))
            }
        }
        walk(start,prefix.trimEnd('/'),0);return out
    }

    override fun exists(path:String)=find(path)!=null

    override fun get(path:String):ByteArray {
        val id=find(path)?.getString("id") ?: throw CloudNotFound(path)
        val connection=drive.media(id,0)
        try {
            require(connection.responseCode in 200..299) { "Drive recusou a leitura de $path (HTTP ${connection.responseCode})." }
            return connection.inputStream.use { input ->
                val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(65536)
                while(true) { val n=input.read(buffer);if(n<0)break;require(out.size().toLong()+n<=maxBytes) { "Arquivo excede o limite de leitura." };out.write(buffer,0,n) };out.toByteArray()
            }
        } finally { connection.disconnect() }
    }

    override fun put(path:String,data:ByteArray,overwrite:Boolean) {
        val (dirs,name)=split(path);val existing=find(path)
        if(existing!=null) {
            if(!overwrite)throw CloudExists(path)
            drive.replaceBytes(existing.getString("id"),data);return
        }
        drive.createBytes(folderOf(dirs,true)!!,name,data)
    }

    override fun trash(path:String) { find(path)?.let { drive.trash(it.getString("id")) } }
}
