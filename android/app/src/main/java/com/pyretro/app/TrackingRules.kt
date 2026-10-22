package com.pyretro.app

import org.json.JSONObject

/** Campos de acompanhamento editados offline: progresso é booleano, nota é 0–11 ou vazia. */
object TrackingRules {
    /** Valor como o servidor compara: nota ausente/NULL vira null, número vira Double. */
    fun value(tracking:JSONObject,field:String):Any? =
        if(field=="nota")tracking.opt(field).takeUnless { it==null || it==JSONObject.NULL }?.let { (it as? Number)?.toDouble() ?: it.toString().toDoubleOrNull() }
        else tracking.optBoolean(field)
    fun same(a:Any?,b:Any?):Boolean {
        val x=a.takeUnless { it==JSONObject.NULL };val y=b.takeUnless { it==JSONObject.NULL }
        return if(x is Number && y is Number)x.toDouble()==y.toDouble() else x==y
    }
    /** Mesmo passo do modo TV: ±1 e ±0,1, uma casa decimal, entre 0 e 11. */
    fun adjust(current:Double?,delta:Double):Double=(Math.round(((current ?: 0.0)+delta)*10)/10.0).coerceIn(0.0,11.0)
    fun label(nota:Double?):String=nota?.let { "%.1f".format(java.util.Locale("pt","BR"),it) } ?: "Sem nota"
}
