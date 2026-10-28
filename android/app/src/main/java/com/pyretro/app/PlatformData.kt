package com.pyretro.app

// Gerado por tools/build_platform_icons.py a partir de assets/platforms/manifest.json; não edite.
data class PlatformInfo(val id:String,val name:String,val short:String,val color:Int,val aliases:List<String>)

object PlatformData {
    val all=listOf(
    PlatformInfo("outro","Outra plataforma","?",0xFF4A5560.toInt(),listOf()),
    PlatformInfo("nes","Nintendo Entertainment System","NES",0xFFB3202B.toInt(),listOf("FC","Nintendo - Nintendo Entertainment System","Famicom","Nintendo Entertainment System")),
    PlatformInfo("snes","Super Nintendo","SNES",0xFF6B4FA0.toInt(),listOf("SFC","Nintendo - Super Nintendo Entertainment System","Super Nintendo Entertainment System","Super Famicom")),
    PlatformInfo("gb","Game Boy","GB",0xFF5C6B3A.toInt(),listOf("GB","Nintendo - Game Boy")),
    PlatformInfo("gbc","Game Boy Color","GBC",0xFF8A3FA8.toInt(),listOf("GBC","Nintendo - Game Boy Color")),
    PlatformInfo("gba","Game Boy Advance","GBA",0xFF3F4FA8.toInt(),listOf("GBA","Nintendo - Game Boy Advance")),
    PlatformInfo("n64","Nintendo 64","N64",0xFF2E7D4F.toInt(),listOf("N64","Nintendo - Nintendo 64")),
    PlatformInfo("nds","Nintendo DS","DS",0xFF4A5560.toInt(),listOf("NDS","Nintendo - Nintendo DS","Nintendo DS")),
    PlatformInfo("3ds","Nintendo 3DS","3DS",0xFFB3202B.toInt(),listOf("3DS","Nintendo - 3DS","Nintendo 3DS")),
    PlatformInfo("gamecube","GameCube","GC",0xFF5B4B9A.toInt(),listOf("NGC","Nintendo - GameCube","GameCube","Nintendo GameCube")),
    PlatformInfo("wii","Wii","Wii",0xFF37769A.toInt(),listOf("WII","Nintendo - Wii","Nintendo Wii")),
    PlatformInfo("switch","Nintendo Switch","NSW",0xFFC21F2B.toInt(),listOf("NSW","Nintendo Switch","Switch")),
    PlatformInfo("mastersystem","Master System","SMS",0xFF1F4E9C.toInt(),listOf("SMS","Sega - Master System - Mark III","Sega Master System")),
    PlatformInfo("megadrive","Mega Drive","MD",0xFF223A7A.toInt(),listOf("MD","Sega - Mega Drive - Genesis","Mega Drive","Genesis","Sega Genesis")),
    PlatformInfo("gamegear","Game Gear","GG",0xFF2B4F8F.toInt(),listOf("GG","Sega - Game Gear","Sega Game Gear")),
    PlatformInfo("pcengine","PC Engine","PCE",0xFFB8561A.toInt(),listOf("PCE","NEC - PC Engine - TurboGrafx 16","PC Engine","TurboGrafx-16")),
    PlatformInfo("pcenginecd","PC Engine CD","PCE-CD",0xFF9A4A16.toInt(),listOf("PCECD","NEC - PC Engine CD - TurboGrafx-CD","PC Engine CD","TurboGrafx-CD")),
    PlatformInfo("arcade","Arcade","ARC",0xFF8F6A00.toInt(),listOf("ARCADE","FBNeo - Arcade Games","Arcade","Fliperama")),
    PlatformInfo("ps1","PlayStation","PS1",0xFF1F4F9E.toInt(),listOf("PS","Sony - PlayStation","PlayStation","PlayStation 1","PS1","PSX")),
    PlatformInfo("ps2","PlayStation 2","PS2",0xFF243C8A.toInt(),listOf("PS2","Sony - PlayStation 2","PlayStation 2")),
    PlatformInfo("psp","PlayStation Portable","PSP",0xFF33414F.toInt(),listOf("PSP","Sony - PSP","PlayStation Portable")),
    PlatformInfo("ps3","PlayStation 3","PS3",0xFF2A3E6E.toInt(),listOf("PS3","PlayStation 3","Sony - PlayStation 3")),
    PlatformInfo("ps4","PlayStation 4","PS4",0xFF1B4F8A.toInt(),listOf("PS4","PlayStation 4","Sony - PlayStation 4")),
    PlatformInfo("ps5","PlayStation 5","PS5",0xFF2C4A7A.toInt(),listOf("PS5","PlayStation 5")),
    PlatformInfo("xbox","Xbox","XBOX",0xFF2F7D32.toInt(),listOf("Xbox")),
    PlatformInfo("xbox360","Xbox 360","360",0xFF3A7A2E.toInt(),listOf("Xbox 360","X360")),
    PlatformInfo("xboxone","Xbox One","ONE",0xFF2F7D32.toInt(),listOf("Xbox One")),
    PlatformInfo("xboxseries","Xbox Series X|S","XS",0xFF1F6F4A.toInt(),listOf("Xbox Series S","Xbox Series X","Xbox Series X|S","Xbox Series")),
    PlatformInfo("steam","Steam","STEAM",0xFF27475E.toInt(),listOf("Steam")),
    PlatformInfo("gog","GOG","GOG",0xFF6A3D8F.toInt(),listOf("GOG","GOG Galaxy")),
    PlatformInfo("epic","Epic Games Store","EPIC",0xFF3A3F45.toInt(),listOf("Epic Games Store","Epic Games","Epic")),
    PlatformInfo("amazon","Amazon Games","AMZ",0xFF9A5B00.toInt(),listOf("Amazon Games","Amazon","Prime Gaming")),
    PlatformInfo("pc","PC","PC",0xFF4A5560.toInt(),listOf("PC","Windows","Heroic","Heroic Games Launcher")),
    PlatformInfo("android","Android","AND",0xFF2F7A4F.toInt(),listOf("Android")),
    PlatformInfo("ios","iOS","iOS",0xFF4A5560.toInt(),listOf("iOS","iPhone","iPad"))
    )
}
