package com.pyretro.app

/** Escolhas explícitas; o Android não permite consultar os cores privados de outro app. */
object CoreProfiles {
    val choices=linkedMapOf(
        "FC" to listOf("nestopia" to "Nestopia", "fceumm" to "FCEUmm", "mesen" to "Mesen"),
        "SFC" to listOf("snes9x" to "Snes9x", "snes9x2010" to "Snes9x 2010"),
        "GB" to listOf("gambatte" to "Gambatte", "gearboy" to "Gearboy"),
        "GBC" to listOf("gambatte" to "Gambatte", "gearboy" to "Gearboy"),
        "GBA" to listOf("mgba" to "mGBA", "gpsp" to "gpSP"),
        "MD" to listOf("genesis_plus_gx" to "Genesis Plus GX", "picodrive" to "PicoDrive"),
        "SMS" to listOf("genesis_plus_gx" to "Genesis Plus GX", "picodrive" to "PicoDrive"),
        "GG" to listOf("genesis_plus_gx" to "Genesis Plus GX", "gearsystem" to "Gearsystem"),
        "N64" to listOf("mupen64plus_next_gles3" to "Mupen64Plus-Next GLES3", "mupen64plus_next_gles2" to "Mupen64Plus-Next GLES2", "parallel_n64" to "ParaLLEl N64"),
        "NDS" to listOf("melonds" to "melonDS", "melondsds" to "melonDS DS", "desmume" to "DeSmuME"),
        "PCE" to listOf("mednafen_pce" to "Beetle PCE", "mednafen_pce_fast" to "Beetle PCE Fast"),
        "PCECD" to listOf("mednafen_pce" to "Beetle PCE", "mednafen_pce_fast" to "Beetle PCE Fast"),
        "ARCADE" to listOf("fbneo" to "FinalBurn Neo", "mame2003_plus" to "MAME 2003 Plus"),
        "PS" to listOf("swanstation" to "SwanStation", "pcsx_rearmed" to "PCSX ReARMed")
    )
    fun id(code:String,selected:String?=null):String {
        val options=choices[code] ?: error("Escolha um emulador para $code.")
        val id=selected ?: options.first().first
        require(options.any { it.first==id }) { "Core inválido para $code. Escolha em Opções." }
        return id
    }
}
