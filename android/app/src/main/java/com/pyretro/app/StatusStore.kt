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
        fun access(uri:Uri?):FolderAccess {
            if(uri==null)return FolderAccess.UNSELECTED
            return identity(uri)?.let { StatusRules.access(it,granted) } ?: FolderAccess.RESELECT
        }
        return listOf(FolderStatus("ROOT","Pasta Jogos",access(store.prefs.getString("tree:ROOT",null)?.let(Uri::parse))))+
            store.folders.map { (code,label) -> FolderStatus(code,label,access(store.tree(code))) }+
            listOf(FolderStatus("retroarch","Pasta RetroArch",access(sync.retroarchTree())))+
            sync.groups.map { (code,label) -> FolderStatus(code,label,access(sync.tree(code))) }
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
