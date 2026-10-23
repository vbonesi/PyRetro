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
    private fun list(query:String):List<JSONObject> {
        val out=mutableListOf<JSONObject>();var page=""
        do {
            val data=json("https://www.googleapis.com/drive/v3/files?pageSize=1000&fields=nextPageToken,files(id,name,size,md5Checksum,mimeType)&q=${URLEncoder.encode(query,"UTF-8")}"+(if(page.isEmpty())"" else "&pageToken=$page"))
            val files=data.optJSONArray("files") ?: JSONArray();for(i in 0 until files.length())out.add(files.getJSONObject(i))
            page=data.optString("nextPageToken")
        } while(page.isNotEmpty())
        return out
    }
    private val folders=mutableMapOf<String,String>()
    private fun folder(path:List<String>):String {
        var parent="root"
        for((i,name) in path.withIndex()) {
            val key=path.take(i+1).joinToString("/")
            parent=folders[key] ?: list(DriveSource.childQuery(parent,name,folder=true)).singleOrNull()?.getString("id")?.also { folders[key]=it }
                ?: error("Pasta ${path.take(i+1).joinToString("/")} não encontrada (ou repetida) no Drive desta conta.")
        }
        return parent
    }
    fun account():String { val email=json("https://www.googleapis.com/drive/v3/about?fields=user(emailAddress)").getJSONObject("user").getString("emailAddress")
        prefs.edit().putBoolean("google:connected",true).putString("google:email",email).apply();return email }
    /** Arquivos da pasta do sistema no Drive (Jogos/ROMs/<código>). */
    fun romFiles(code:String):List<DriveRef> = list(DriveSource.childQuery(folder(DriveSource.ROMS+code),folder=false))
        .map { DriveRef(it.getString("id"),it.getString("name"),it.optString("size","0").toLongOrNull() ?: 0,it.optString("md5Checksum")) }
    fun metadata(id:String):DriveRef { val it=json("https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?fields=id,name,size,md5Checksum,trashed")
        require(!it.optBoolean("trashed")) { "O arquivo foi para a lixeira do Drive." }
        return DriveRef(it.getString("id"),it.getString("name"),it.optString("size","0").toLong(),it.optString("md5Checksum")) }
    /** Conteúdo a partir de `offset` (Range), para continuar uma cópia parcial. */
    fun media(id:String,offset:Long):HttpURLConnection = open("https://www.googleapis.com/drive/v3/files/${URLEncoder.encode(id,"UTF-8")}?alt=media",offset)
}
