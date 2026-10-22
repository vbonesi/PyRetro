package com.pyretro.app

import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.io.IOException
import java.security.MessageDigest

/** Valida todo o prefixo na origem antes de acrescentar bytes ao checkpoint.
 *  Com [resumed], a origem já começa depois do checkpoint (HTTP Range com etag conferido
 *  pelo notebook): o prefixo local só entra no SHA-256, sem ser relido da rede. */
object ResumableCopy {
    class Paused:IOException("Download pausado. Use Downloads para continuar.")
    fun copy(input:InputStream,file:File,expected:Long?,limit:Long=12L*1024*1024*1024,
             cancelled:()->Boolean={false},progress:(Long)->Unit={},resumed:Boolean=false):String {
        var total=file.length();require(total<=limit && (expected==null || total<=expected)) { "Origem mudou. Descarte a cópia parcial para reiniciar." }
        val digest=MessageDigest.getInstance("SHA-256");val buffer=ByteArray(256*1024)
        fun checkPause() { if(cancelled())throw Paused() }
        if(total>0 && resumed)file.inputStream().use { previous ->
            while(true) { checkPause();val n=previous.read(buffer);if(n<0)break;digest.update(buffer,0,n) }
        }
        else if(total>0)file.inputStream().use { previous ->
            var left=total;val old=ByteArray(buffer.size)
            while(left>0) {
                checkPause();val n=input.read(buffer,0,minOf(buffer.size.toLong(),left).toInt())
                require(n>0) { "Origem ficou menor. Cópia parcial preservada." }
                var offset=0;while(offset<n) { val read=previous.read(old,offset,n-offset);require(read>0);offset+=read }
                require((0 until n).all { buffer[it]==old[it] }) { "Origem mudou no trecho já baixado. Descarte a cópia parcial para reiniciar." }
                digest.update(buffer,0,n);left-=n
            }
        }
        checkPause();progress(total)
        FileOutputStream(file,true).use { output ->
            try {
                while(true) {
                    checkPause();val n=input.read(buffer);if(n<0)break
                    require(total+n<=limit && (expected==null || total+n<=expected)) { "Origem excedeu o tamanho esperado." }
                    output.write(buffer,0,n);digest.update(buffer,0,n);total+=n;progress(total)
                }
            } finally { output.fd.sync() }
        }
        require(total>0 && (expected==null || total==expected)) { "Transferência incompleta. A cópia parcial foi preservada." }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}
