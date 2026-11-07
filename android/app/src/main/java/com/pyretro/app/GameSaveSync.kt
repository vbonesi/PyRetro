package com.pyretro.app

import android.provider.DocumentsContract

/**
 * Saves de um jogo do RetroArch pela nuvem sem perguntar: ao terminar o download da ROM e ao voltar do jogo.
 * Só aplica o que é seguro (enviar versão nova, baixar quando o celular não mudou nada); conflito nunca é
 * sobrescrito e fica para a tela "Saves na nuvem". Falha de rede ou pasta não configurada não atrapalha nada.
 */
object GameSaveSync {
    data class Outcome(val sent:Int,val received:Int,val conflicts:Int,val failed:Int) {
        val any get()=sent+received+conflicts+failed>0
        fun text():String=listOfNotNull(sent.takeIf { it>0 }?.let { "↑ $it save(s) enviado(s)" },received.takeIf { it>0 }?.let { "↓ $it save(s) baixado(s)" },
            conflicts.takeIf { it>0 }?.let { "⚠ $it conflito(s): abra Saves do jogo" },failed.takeIf { it>0 }?.let { "$it falha(s) ao sincronizar saves" }).joinToString(" · ")
    }
    /** `null` quando não se aplica (PSP/3DS usam o ID do título; sem conta Google; pasta RetroArch não escolhida). */
    fun run(store:LibraryStore,drive:GoogleDrive,game:Game,storage:CloudStorage=DriveCloudStorage(drive)):Outcome? {
        if(!drive.connected || game.code.isEmpty() || game.code=="PSP" || game.code=="3DS")return null
        val sync=FileSync(store)
        if(sync.tree("retro-saves")==null || sync.retroarchTree()?.let { SaveRules.retroarchFolderProblem(DocumentsContract.getTreeDocumentId(it)) }!=null)return null
        val name=game.localUri?.let { runCatching { store.displayName(it) }.getOrNull() } ?: game.romName.substringAfterLast('/').ifBlank { game.name }
        val label=SaveRules.label(name,store.extensionsFor(game.code))
        val mine:(String,String)->Boolean={ group,path -> group in setOf("retro-saves","retro-states") && SaveRules.belongs(path,game.code,label) }
        val phone=CloudPhone(store,sync,storage)
        var sent=0;var received=0;var failed=0
        for(result in phone.apply(filter=mine,safeOnly=true).values) {
            val rows=result.getOrNull();if(rows==null) { failed++;continue }
            for(row in rows) if(!row.ok)failed++ else if(row.action=="push")sent++ else if(row.action=="pull")received++
        }
        val conflicts=phone.analyze(mine).values.sumOf { it.getOrNull()?.count { item -> item.action=="conflict" } ?: 0 }
        return Outcome(sent,received,conflicts,failed)
    }
}
