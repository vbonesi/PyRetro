package com.pyretro.app

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** Mesma identidade do modo TV (tv.css): fundo #0b1220, painel #1a2b3f, destaque #81e1ca. */
private val Accent = Color(0xFF81E1CA)
private val Dark = darkColorScheme(
    primary = Accent, onPrimary = Color(0xFF102B30), background = Color(0xFF0B1220), onBackground = Color(0xFFEDF4FD),
    surface = Color(0xFF1A2B3F), onSurface = Color(0xFFEDF4FD), surfaceVariant = Color(0xFF223850), onSurfaceVariant = Color(0xFF9FB3C9),
    outline = Color(0xFF3C5166), secondaryContainer = Color(0xFF1F4A47), onSecondaryContainer = Accent,
)
private val Light = lightColorScheme(
    primary = Color(0xFF0E7C6B), onPrimary = Color.White, background = Color(0xFFF1F6FB), onBackground = Color(0xFF0B1220),
    surface = Color.White, onSurface = Color(0xFF0B1220), surfaceVariant = Color(0xFFE2EBF4), onSurfaceVariant = Color(0xFF3C5166),
    outline = Color(0xFF9FB3C9), secondaryContainer = Color(0xFFCDEFE7), onSecondaryContainer = Color(0xFF0E5A4E),
)

@Composable
fun PyRetroTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) =
    MaterialTheme(colorScheme = if (dark) Dark else Light, content = content)
