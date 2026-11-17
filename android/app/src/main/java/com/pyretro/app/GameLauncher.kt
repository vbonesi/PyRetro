package com.pyretro.app

import android.content.ClipData
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.DocumentsContract

/** Abre o jogo no emulador certo; compartilhado pela casca em Compose e pela tela antiga. */
object GameLauncher {
    /** Caminho real do arquivo (armazenamento interno ou cartão) a partir do endereço do seletor de pastas. */
    fun filePath(uri: Uri): String {
        val parts = DocumentsContract.getDocumentId(uri).split(':', limit = 2)
        require(uri.authority == "com.android.externalstorage.documents" && parts.size == 2) { "Copie a ROM para uma pasta do armazenamento interno antes de abrir no emulador." }
        return (if (parts[0] == "primary") "/storage/emulated/0/" else "/storage/${parts[0]}/") + parts[1]
    }

    fun coreId(store: LibraryStore, code: String) = CoreProfiles.id(code, store.prefs.getString("core:$code", if (code == "NDS") store.prefs.getString("nds-core", null) else null))

    private fun installed(context: Context, vararg packages: String) = packages.firstOrNull { context.packageManager.getLaunchIntentForPackage(it) != null }

    fun retroArchIntent(context: Context, store: LibraryStore, game: Game, uri: Uri): Intent {
        val pkg = installed(context, "com.retroarch", "com.retroarch.aarch64") ?: error("RetroArch não encontrado.")
        val path = filePath(uri)
        val target = context.packageManager.getApplicationInfo(pkg, 0)
        return Intent().setComponent(ComponentName(pkg, "com.retroarch.browser.retroactivity.RetroActivityFuture")).putExtra("ROM", path)
            .putExtra("LIBRETRO", "${target.dataDir}/cores/${coreId(store, game.code)}_libretro_android.so")
            .putExtra("CONFIGFILE", "/storage/emulated/0/Android/data/$pkg/files/retroarch.cfg")
    }

    /** Intent pronta para iniciar o jogo que está no celular; lança [IllegalStateException] com texto para o usuário se faltar emulador. */
    fun intentFor(context: Context, store: LibraryStore, game: Game): Intent {
        val uri = game.localUri ?: error("Este jogo não está neste celular.")
        val intent = when (game.code) {
            "3DS" -> Intent(Intent.ACTION_VIEW).setPackage(installed(context, "io.github.lime3ds.android", "io.github.azahar_emu.azahar") ?: error("Instale/configure Lime3DS ou Azahar no celular.")).setDataAndType(uri, "application/octet-stream")
            "PSP" -> Intent(Intent.ACTION_VIEW).setPackage(installed(context, "org.ppsspp.ppssppgold", "org.ppsspp.ppsspp") ?: error("PPSSPP não encontrado.")).setDataAndType(uri, "application/octet-stream")
            else -> retroArchIntent(context, store, game, uri)
        }
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION); intent.clipData = ClipData.newRawUri("ROM", uri)
        return intent
    }
}
