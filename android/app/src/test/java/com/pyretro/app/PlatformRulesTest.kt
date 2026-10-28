package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class PlatformRulesTest {
    @Test fun matchesRomCodesSourceNamesAndNicknames() {
        assertEquals("snes",PlatformRules.find("SFC","qualquer").id)
        assertEquals("ps1",PlatformRules.find(null,"Sony - PlayStation").id)
        assertEquals("xboxseries",PlatformRules.find("Xbox Series S").id)
        assertEquals("N64",PlatformRules.find("Nintendo - Nintendo 64").short)
        assertEquals("epic",PlatformRules.find(null,"Epic Games Store").id)
    }
    @Test fun unknownPlatformGetsNeutralBadgeWithInitials() {
        val info=PlatformRules.find("Atari Jaguar")
        assertEquals("outro",info.id);assertEquals("ATA",info.short);assertEquals("Atari Jaguar",info.name)
    }
    @Test fun everyBadgeFitsAndAliasesAreUnique() {
        val seen=HashMap<String,String>()
        for(p in PlatformData.all){ assertTrue(p.short.length<=6)
            for(name in listOf(p.id,p.name)+p.aliases){ val owner=seen.getOrPut(name.lowercase().filter { it.isLetterOrDigit() }) { p.id };assertEquals("$name pertence a duas plataformas",p.id,owner) } }
    }
}
