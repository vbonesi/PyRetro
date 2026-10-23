package com.pyretro.app

/** A origem tentada precisa sobreviver ao erro, quando não há rootTag de resposta. */
data class SaveReviewText(val drive:Boolean,val notice:String,val warning:String?) {
    val equal get()=if(drive)"Iguais no celular e no Drive." else "Iguais no celular e no notebook."
    companion object {
        fun forComparison(rootTags:List<String>?,attemptedDrive:Boolean,configured:Boolean):SaveReviewText {
            val drive=attemptedDrive || rootTags?.any { it.startsWith("drive:") }==true
            return when {
                rootTags!=null -> SaveReviewText(drive,if(drive)"conferidos com o Drive." else "conferidos.",null)
                drive -> SaveReviewText(true,"comparação com o Drive indisponível, só os do celular.","Não foi possível comparar com o Drive. Confira a internet e a conta Google. Os arquivos acima continuam valendo no celular.")
                !configured -> SaveReviewText(false,"notebook não configurado.","Configure o notebook para comparar.")
                else -> SaveReviewText(false,"notebook offline, só os do celular.","Notebook offline: comparação indisponível. Os arquivos acima continuam valendo no celular.")
            }
        }
    }
}
