package com.pyretro.app
import android.app.Activity
import android.app.Instrumentation
import android.graphics.*
import android.graphics.drawable.AdaptiveIconDrawable
import android.os.Bundle
import java.io.File
import java.util.UUID

/** Renderiza os recursos instalados. Não captura desktop, notificações ou dados do usuário. */
class IconSmoke(private val runner:Instrumentation) {
    fun run() {
        val result=Bundle();var ok=false
        try {
            val context=runner.targetContext;val output=File(context.cacheDir,"icon-smoke-"+UUID.randomUUID()).apply { mkdirs() }
            val installed=context.applicationInfo.loadIcon(context.packageManager);check(installed is AdaptiveIconDrawable)
            fun save(name:String,bitmap:Bitmap) { File(output,"$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG,100,it) };bitmap.recycle() }
            val actual=Bitmap.createBitmap(256,256,Bitmap.Config.ARGB_8888);installed.setBounds(0,0,256,256);installed.draw(Canvas(actual));save("installed-mask",actual)
            for(mask in listOf("circle","squircle","rounded"))for(theme in listOf("color","light","dark")) {
                val bitmap=Bitmap.createBitmap(256,256,Bitmap.Config.ARGB_8888);val canvas=Canvas(bitmap);val path=Path()
                if(mask=="circle")path.addCircle(128f,128f,128f,Path.Direction.CW) else path.addRoundRect(RectF(0f,0f,256f,256f),if(mask=="squircle")80f else 40f,if(mask=="squircle")80f else 40f,Path.Direction.CW)
                canvas.clipPath(path);canvas.drawColor(if(theme=="light")Color.rgb(219,234,226) else Color.rgb(11,18,32))
                val foreground=context.getDrawable(if(theme=="color")R.drawable.ic_launcher_foreground else R.drawable.ic_launcher_monochrome)!!
                if(theme!="color")foreground.setTint(if(theme=="light")Color.rgb(28,73,56) else Color.rgb(170,225,194))
                foreground.setBounds(-64,-64,320,320);foreground.draw(canvas)
                val center=bitmap.getPixel(128,128);check(center!=Color.TRANSPARENT);save("$mask-$theme",bitmap)
            }
            if(android.os.Build.VERSION.SDK_INT>=33)check(installed.monochrome!=null) { "Recurso monocromático ausente no ícone instalado." }
            result.putString("stream","PASS: ícone instalado e recursos de cor/monocromático; nove máscaras/temas para inspeção em ${output.absolutePath}. O launcher real ainda exige conferência visual.\n");ok=true
        } catch(error:Throwable) { result.putString("stream","FAIL: ${error.stackTraceToString()}\n") }
        runner.finish(if(ok)Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
