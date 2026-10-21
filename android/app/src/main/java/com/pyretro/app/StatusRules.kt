package com.pyretro.app

/** IDs SAF são opacos: nunca deduzir parentesco por prefixo do nome/URI. */
data class GrantIdentity(val authority:String,val id:String,val tree:Boolean)
data class SavedGrant(val identity:GrantIdentity,val read:Boolean,val write:Boolean)
enum class FolderAccess { UNSELECTED, RESELECT, READ_ONLY, READ_WRITE }

object StatusRules {
    fun access(target:GrantIdentity?,grants:List<SavedGrant>):FolderAccess {
        if(target==null)return FolderAccess.UNSELECTED
        val matching=grants.filter { it.identity==target }
        if(matching.none { it.read })return FolderAccess.RESELECT
        return if(matching.any { it.write })FolderAccess.READ_WRITE else FolderAccess.READ_ONLY
    }
    fun currentObservation(savedServer:String,savedTree:String,server:String,tree:String)=
        server.isNotBlank() && savedServer==server && savedTree==tree
    fun conflictStillApplies(payload:String,observedPayload:String?)=payload==observedPayload
}
