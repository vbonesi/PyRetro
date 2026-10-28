package com.pyretro.app

/**
 * Cor da nota, igual à da web e do modo TV (`logic.js`, mesmas amostras nos testes): vermelho em
 * 0–1, laranja em 4, amarelo em 6,5, já verde em 7 e verde pleno em 10. Só a nota 11 exata é
 * dourada (jogo muito especial); não existe 10,x, e um valor gravado entre 10 e 11 usa o verde de 10.
 */
object NotaRules {
    private val stops=listOf(1.0 to intArrayOf(237,106,106),4.0 to intArrayOf(233,155,86),6.5 to intArrayOf(212,188,99),7.0 to intArrayOf(149,200,120),10.0 to intArrayOf(102,210,155))
    private val gold=intArrayOf(241,199,91)
    fun special(nota:Double?)=nota==11.0
    /** RGB como [r,g,b], ou null sem nota. Arredondamento por canal igual ao do JavaScript. */
    fun rgb(nota:Double?):IntArray? {
        if(nota==null || nota.isNaN())return null
        if(special(nota))return gold
        if(nota<=stops.first().first)return stops.first().second
        for(i in 1 until stops.size) {
            val (x1,c1)=stops[i]
            if(nota<=x1 || i==stops.lastIndex) {
                val (x0,c0)=stops[i-1];val t=((nota-x0)/(x1-x0)).coerceIn(0.0,1.0)
                return IntArray(3) { Math.round(c0[it]+(c1[it]-c0[it])*t).toInt() }
            }
        }
        return null
    }
    fun color(nota:Double?):Int? = rgb(nota)?.let { android.graphics.Color.rgb(it[0],it[1],it[2]) }
    fun symbol(nota:Double?)=if(special(nota))"✦" else "★"
    /** Passo do editor: entre 10 e 11 não há degrau (10 sobe para 11 e 11 desce para 10). */
    fun adjust(current:Double?,delta:Double):Double {
        val value=(Math.round(((current ?: 0.0)+delta)*10)/10.0).coerceIn(0.0,11.0)
        return if(value>10.0 && value<11.0)(if(delta>0)11.0 else 10.0) else value
    }
}
