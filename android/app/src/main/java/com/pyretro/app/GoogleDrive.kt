package com.pyretro.app

import android.content.Context
import com.google.android.gms.auth.api.identity.AuthorizationRequest
import com.google.android.gms.auth.api.identity.AuthorizationResult
import com.google.android.gms.auth.api.identity.Identity
import com.google.android.gms.common.api.Scope
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.Tasks
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLDecoder
import java.net.URLEncoder
import java.util.concurrent.TimeUnit

/** ROM no Drive da conta Google do celular, sem passar pelo notebook. Guardada em `cloud:<chave>`
 *  como `pyretro-gdrive:<id>?name=…&size=…&md5=…`: o md5 do Drive confere que o arquivo não mudou. */
data class DriveRef(val id:String,val name:String,val size:Long,val md5:String) {
    fun encoded()="${DriveSource.PREFIX}${enc(id)}?name=${enc(name)}&size=$size&md5=${enc(md5)}"
    private fun enc(value:String)=URLEncoder.encode(value,"UTF-8")
}

/** Regras sem Android: origem guardada, consulta do Drive e escolha do arquivo do jogo. */
object DriveSource {
    const val PREFIX="pyretro-gdrive:"
    const val SCOPE="https://www.googleapis.com/auth/drive"
    /** Mesmo caminho do rclone do notebook (`[rclone] drive_roms_root`). */
    val ROMS=listOf("Jogos","ROMs")
    fun parse(value:String?):DriveRef? {
        if(value==null || !value.startsWith(PREFIX))return null
        return runCatching {
            val body=value.removePrefix(PREFIX);val id=dec(body.substringBefore('?'))
            val query=body.substringAfter('?',"").split('&').filter { it.contains('=') }.associate { it.substringBefore('=') to dec(it.substringAfter('=')) }
            val name=query.getValue("name")
            require(id.matches(Regex("[A-Za-z0-9_-]{10,}")) && name.isNotBlank() && !name.contains('/') && !name.contains('\\') && name !in setOf(".",".."))
            DriveRef(id,name,query.getValue("size").toLong().also { require(it>0) },query["md5"].orEmpty())
        }.getOrNull()
    }
    /** Texto entre aspas simples na consulta do Drive: escapa \\ e '. */
    fun quoted(value:String)="'"+value.replace("\\","\\\\").replace("'","\\'")+"'"
    fun childQuery(parent:String,name:String?=null,folder:Boolean?=null)=listOfNotNull("${quoted(parent)} in parents","trashed = false",
        name?.let { "name = ${quoted(it)}" },folder?.let { if(it)"mimeType = 'application/vnd.google-apps.folder'" else "mimeType != 'application/vnd.google-apps.folder'" }).joinToString(" and ")
    /** O arquivo do jogo: nome exato (ROM pesada) ou nome sem extensão (ROM leve), só formatos que o
     *  celular abre sozinho. Mais de um candidato vira escolha do usuário, nunca adivinhação. */
    fun candidates(files:List<DriveRef>,romName:String,accepts:(String)->Boolean):List<DriveRef> {
        val usable=files.filter { it.size>0 && accepts(it.name) && it.name.substringAfterLast('.').lowercase() !in setOf("cue","m3u") }
        return usable.filter { it.name==romName }.ifEmpty { usable.filter { it.name.substringBeforeLast('.')==romName } }
    }
    private fun dec(value:String)=URLDecoder.decode(value,"UTF-8")
}

/** A conta precisa de uma confirmação na tela (primeira vez ou permissão revogada). */
class GoogleConsentNeeded(val result:AuthorizationResult):Exception("Conecte a conta Google em Opções para usar o Drive sem o notebook.")

class GoogleDrive(private val context:Context,private val prefs:android.content.SharedPreferences) {
    val connected get()=prefs.getBoolean("google:connected",false)
    val email get()=prefs.getString("google:email","").orEmpty()
    private fun request()=AuthorizationRequest.builder().setRequestedScopes(listOf(Scope(DriveSource.SCOPE))).build()
    /** Pedido interativo (tela): o resultado pode trazer um PendingIntent de consentimento. */
    fun authorize():Task<AuthorizationResult> = Identity.getAuthorizationClient(context).authorize(request())
    fun resultFromIntent(data:android.content.Intent?):AuthorizationResult = Identity.getAuthorizationClient(context).getAuthorizationResultFromIntent(data)
    fun disconnect() { prefs.edit().remove("google:connected").remove("google:email").apply();folders.clear() }
    /** Token de acesso em segundo plano; o Play Services renova sozinho enquanto a permissão valer. */
    private fun token():String {
        val result=Tasks.await(authorize(),30,TimeUnit.SECONDS)
        if(result.hasResolution())throw GoogleConsentNeeded(result)
        return requireNotNull(result.accessToken) { "O Google não devolveu acesso ao Drive." }
    }
    private fun open(url:String,range:Long=0):HttpURLConnection {
        val connection=URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout=15000;connection.readTimeout=120000;connection.instanceFollowRedirects=true
        connection.setRequestProperty("Authorization","Bearer ${token()}")
        if(range>0)connection.setRequestProperty("Range","bytes=$range-")
        return connection
    }
    private fun json(url:String):JSONObject {
        val connection=open(url)
        try {
            val status=connection.responseCode
            val text=(if(status in 200..299)connection.inputStream else connection.errorStream)?.bufferedReader()?.use { it.readText() }.orEmpty()
            require(status in 200..299) { runCatching { JSONObject(text).getJSONObject("error").getString("message") }.getOrDefault("Drive recusou (HTTP $status).") }
            return JSONObject(text)
        } finally { connection.disconnect() }
    }
    private fun list(query:String,fields:String="id,name,size,md5Checksum,mimeType"):List<JSONObject> {
        val out=mutableListOf<JSONObject>();var page=""
        do {
            val data=json("https://www.googleapis.com/drive/v3/files?pageSize=1000&fields=nextPageToken,files($fields)&q=${URLEncoder.encode(query,"UTF-8")}"+(if(page.isEmpty())"" else "&pageToken=$page"))
            val files=data.optJSONArray("files") ?: JSONArray();for(i in 0 until files.length())out.add(files.getJSONObject(i))
            page=data.optString("nextPageToken")
        } while(page.isNotEmpty())
        return out
    }
    private val folders=java.util.concurrent.ConcurrentHashMap<String,String>()
    /** Pasta por caminho a partir da raiz do Drive. Nome repetido nunca é resolvido pelo primeiro. */
    @Synchronized fun folder(path:List<String>,create:Boolean=false,from:String="root"):String {
        var parent=from
        for((i,name) in path.withIndex()) {
            val key=from+":"+path.take(i+1).joinToString("/")
            val found=folders[key] ?: list(DriveSource.childQuery(parent,name,folder=true)).let { rows ->
                require(rows.size<=1) { "Pasta ${path.take(i+1).joinToString("/")} repetida no Drive; resolva antes de sincronizar." }
                rows.singleOrNull()?.getString("id")
            } ?: if(create)createFolder(parent,name) else null
            parent=(found ?: error("Pasta ${path.take(i+1).joinToString("/")} não encontrada no Drive desta conta.")).also { folders[key]=it }
        }
        return parent
    }
    @Synchronized fun folderOrNull(path:List<String>,from:String):String? {
        var parent=from
        for((i,name) in path.withIndex()) {
            val key=from+":"+path.take(i+1).joinToString("/")
            val found=folders[key] ?: list(DriveSource.childQuery(parent,name,folder=true)).let { rows ->
                require(rows.size<=1) { "Pasta repetida no Drive; resolva antes de sincronizar." };rows.singleOrNull()?.getString("id")
            } ?: return null
            folders[key]=found;parent=found
        }
        return parent
    }
    /** Filhos de uma pasta com o SHA-256 que o Drive calcula sobre os bytes. */
    fun children(parent:String):List<JSONObject> = list("${DriveSource.quoted(parent)} in parents and trashed = false","id,name,size,mimeType,sha256Checksum,md5Checksum")
    private fun send(method:String,url:String,body:ByteArray?,type:String="application/json; charset=UTF-8"):HttpURLConnection {
        val connection=open(url);connection.requestMethod=method
        if(body!=null) { connection.doOutput=true;connection.setRequestProperty("Content-Type",type);connection.setFixedLengthStreamingMode(body.size);connection.outputStream.use { it.write(body) } }
        return connection
    }
    private fun created(connection:HttpURLConnection):JSONObject = try {
        val status=connection.responseCode;val text=(if(status in 200..299)connection.inputStream else connection.errorStream)?.bufferedReader()?.use { it.readText() }.orEmpty()
        require(status in 200..299) { runCatching { JSONObject(text).getJSONObject("error").getString("message") }.getOrDefault("Drive recusou (HTTP $status).") }
        JSONObject(text)
    } finally { connection.disconnect() }
    private fun createFolder(parent:String,name:String):String = created(send("POST","https://www.googleapis.com/drive/v3/files?fields=id",
        JSONObject().put("name",name).put("mimeType","application/vnd.google-apps.folder").put("parents",JSONArray().put(parent)).toString().toByteArray())).getString("id")
    /** Envia um arquivo novo (upload retomável numa sessão só); nunca substitui um existente. */
    fun create(parent:String,name:String,file:java.io.File):JSONObject {
        val start=send("POST","https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,name,size,sha256Checksum",
            JSONObject().put("name",name).put("parents",JSONArray().put(parent)).toString().toByteArray())
        val location=try { require(start.responseCode==200) { "Drive recusou o envio (HTTP ${start.responseCode})." };requireNotNull(start.getHeaderField("Location")) } finally { start.disconnect() }
        val upload=URL(location).openConnection() as HttpURLConnection
        upload.requestMethod="PUT";upload.doOutput=true;upload.connectTimeout=15000;upload.readTimeout=120000;upload.setFixedLengthStreamingMode(file.length())
        upload.setRequestProperty("Authorization","Bearer ${token()}");upload.outputStream.use { out -> file.inputStream().use { it.copyTo(out,1024*1024) } }
        return created(upload)
    }
    /** Move para outra pasta com outro nome (usado para tirar do caminho um envio que duplicou). */
    fun move(id:String,from:String,to:String,name:String) { created(send("PATCH","https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?addParents=$to&removeParents=$from&fields=id",
        JSONObject().put("name",name).toString().toByteArray())) }
    /** Envia bytes como arquivo novo (mesmo envio retomável de [create]). */
    fun createBytes(parent:String,name:String,data:ByteArray):JSONObject {
        val temporary=java.io.File.createTempFile("cloud-",".tmp",context.cacheDir)
        try { temporary.writeBytes(data);return create(parent,name,temporary) } finally { temporary.delete() }
    }
    /** Troca o conteúdo de um arquivo que já existe (o id e o histórico de versões do Drive continuam). */
    fun replaceBytes(id:String,data:ByteArray) { created(send("PATCH","https://www.googleapis.com/upload/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?uploadType=media&fields=id",data,"application/octet-stream")) }
    /** Manda para a lixeira do Drive (recuperável por 30 dias). */
    fun trash(id:String) { created(send("PATCH","https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?fields=id",JSONObject().put("trashed",true).toString().toByteArray())) }
    fun accountId():String=json("https://www.googleapis.com/drive/v3/about?fields=user(permissionId)").getJSONObject("user").getString("permissionId")
    fun account():String { val email=json("https://www.googleapis.com/drive/v3/about?fields=user(emailAddress)").getJSONObject("user").getString("emailAddress")
        prefs.edit().putBoolean("google:connected",true).putString("google:email",email).apply();return email }
    /** Arquivos da pasta do sistema no Drive (Jogos/ROMs/<código>). */
    fun romFiles(code:String):List<DriveRef> {
        val folder=folderOrNull(DriveSource.ROMS+code,"root") ?: return emptyList()
        return list(DriveSource.childQuery(folder,folder=false)).map { DriveRef(it.getString("id"),it.getString("name"),it.optString("size","0").toLongOrNull() ?: 0,it.optString("md5Checksum")) }
    }
    fun file(id:String):JSONObject=json("https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?fields=id,name,size,trashed,sha256Checksum")
    fun metadata(id:String):DriveRef { val it=json("https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?fields=id,name,size,md5Checksum,trashed")
        require(!it.optBoolean("trashed")) { "O arquivo foi para a lixeira do Drive." }
        return DriveRef(it.getString("id"),it.getString("name"),it.optString("size","0").toLong(),it.optString("md5Checksum")) }
    /** Conteúdo a partir de `offset` (Range), para continuar uma cópia parcial. */
    fun media(id:String,offset:Long):HttpURLConnection = open("https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?alt=media",offset)
}
