package com.pyretro.app

import android.net.Uri
import android.provider.DocumentsContract
import org.json.JSONObject

data class FolderStatus(val code:String,val label:String,val access:FolderAccess)
data class PendingStatus(val key:String,val time:Boolean,val conflict:Boolean)

/** A central lê metadados privados e concessões; abrir a tela não consulta provedores/rede. */
class StatusStore(private val store:LibraryStore) {
    private fun identity(uri:Uri):GrantIdentity?=runCatching {
        require(uri.scheme=="content")
        val tree=DocumentsContract.isTreeUri(uri)
        GrantIdentity(requireNotNull(uri.authority),if(tree)DocumentsContract.getTreeDocumentId(uri) else DocumentsContract.getDocumentId(uri),tree)
    }.getOrNull()
    private fun grants()=store.context.contentResolver.persistedUriPermissions.mapNotNull { permission ->
        identity(permission.uri)?.let { SavedGrant(it,permission.isReadPermission,permission.isWritePermission) }
    }
    fun folders():List<FolderStatus> {
        val granted=grants();val sync=FileSync(store)
        fun access(resolve:()->Uri?):FolderAccess=runCatching {
            val uri=resolve()
            if(uri==null)FolderAccess.UNSELECTED else identity(uri)?.let { StatusRules.access(it,granted) } ?: FolderAccess.RESELECT
        }.getOrDefault(FolderAccess.RESELECT)
        return listOf(FolderStatus("ROOT","Pasta Jogos",access { store.prefs.getString("tree:ROOT",null)?.let(Uri::parse) }))+
            store.folders.map { (code,label) -> FolderStatus(code,label,access { store.tree(code) }) }+
            listOf(FolderStatus("retroarch","Pasta RetroArch",access { sync.retroarchTree() }))+
            sync.groups.map { (code,label) -> FolderStatus(code,label,access { sync.tree(code) }) }
    }
    fun connectionSummary(date:(Long)->String):String {
        if(store.base().isBlank())return "Endereço ainda não configurado. Abra Opções para salvar o endereço HTTPS."
        fun whenRecorded(key:String)=store.prefs.getLong(key,0).takeIf { it>0 }?.let(date) ?: "ainda não registrado"
        val attempt=if(!store.prefs.contains("last-attempt-ok"))"." else if(store.prefs.getBoolean("last-attempt-ok",false))" · respondeu." else " · falhou. Confira notebook, Tailscale e endereço."
        return "Último contato bem-sucedido: ${whenRecorded("last-contact")}.\nÚltima tentativa: ${whenRecorded("last-attempt")}$attempt\nÉ um registro de contato; a conexão pode mudar. Testar não sincroniza nem abre jogos."
    }
    fun pending():List<PendingStatus> {
        val snapshot=store.prefs.all
        return snapshot.filterKeys { it.startsWith("pending:") || it.startsWith("time-event:") }.map { (key,raw) ->
            val payload=runCatching { JSONObject(raw as String) }.getOrNull()
            PendingStatus(payload?.optString("key") ?: key.removePrefix("pending:"),key.startsWith("time-event:"),
                raw is String && StatusRules.conflictStillApplies(raw,snapshot["conflict:$key"] as? String))
        }
    }
}
