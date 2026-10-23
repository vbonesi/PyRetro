package com.pyretro.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper

/** O que a notificação mostra para um estado da fila (sem Android, testável). */
data class DownloadNoticeText(val title:String,val text:String,val percent:Int?,val ongoing:Boolean)
object DownloadNotice {
    fun of(rows:List<QueuedDownload>,running:Boolean):DownloadNoticeText? {
        val active=rows.firstOrNull { it.state==DownloadState.RUNNING }
        val waiting=rows.count { it.state==DownloadState.WAITING }
        if(running && active!=null) {
            val percent=active.total?.takeIf { it>0 }?.let { (active.bytes*100/it).toInt().coerceIn(0,100) }
            return DownloadNoticeText("Baixando ${active.game.name}",(percent?.let { "$it%" } ?: "em andamento")+(if(waiting>0)" · mais $waiting na fila" else ""),percent,true)
        }
        if(running)return DownloadNoticeText("Downloads do PyRetro","Preparando a fila…",null,true)
        val failed=rows.filter { it.state==DownloadState.FAILED };val paused=rows.count { it.state==DownloadState.PAUSED }
        return when {
            failed.isNotEmpty() -> DownloadNoticeText("Download falhou: ${failed.first().game.name}",failed.first().error.ifBlank { "Abra Downloads no PyRetro." },null,false)
            paused>0 -> DownloadNoticeText("Downloads pausados","$paused na fila · cópia parcial preservada",null,false)
            rows.size==1 && rows[0].state==DownloadState.DONE -> DownloadNoticeText("Download concluído","${rows[0].game.name} está pronto em Neste celular",null,false)
            rows.isNotEmpty() && rows.all { it.state==DownloadState.DONE } -> DownloadNoticeText("Downloads concluídos","${rows.size} jogos prontos em Neste celular",null,false)
            else -> null
        }
    }
}

/** Mantém a fila rodando com o app em segundo plano (serviço em primeiro plano, tipo dataSync).
 *  Não inicia downloads sozinho: só acompanha a fila que o usuário começou. */
class DownloadService:Service() {
    companion object {
        private const val CHANNEL="downloads";private const val ONGOING=1;private const val RESULT=2
        const val PAUSE="com.pyretro.app.PAUSE_DOWNLOADS"
        fun follow(context:Context) {
            val intent=Intent(context,DownloadService::class.java)
            runCatching { if(Build.VERSION.SDK_INT>=26)context.startForegroundService(intent) else context.startService(intent) }
        }
    }
    private val handler=Handler(Looper.getMainLooper())
    /** Concluídos antes deste acompanhamento: o aviso final fala só do que terminou agora. */
    private var doneBefore:Set<String>?=null
    private val queue by lazy { DownloadQueue.get(LibraryStore(applicationContext)) }
    private val manager by lazy { getSystemService(NotificationManager::class.java) }
    private fun build(notice:DownloadNoticeText):Notification {
        if(Build.VERSION.SDK_INT>=26)manager.createNotificationChannel(NotificationChannel(CHANNEL,"Downloads",NotificationManager.IMPORTANCE_LOW))
        val open=PendingIntent.getActivity(this,0,Intent(this,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),PendingIntent.FLAG_IMMUTABLE)
        val builder=(if(Build.VERSION.SDK_INT>=26)Notification.Builder(this,CHANNEL) else @Suppress("DEPRECATION") Notification.Builder(this))
            .setSmallIcon(if(notice.ongoing)android.R.drawable.stat_sys_download else android.R.drawable.stat_sys_download_done)
            .setContentTitle(notice.title).setContentText(notice.text).setContentIntent(open).setOngoing(notice.ongoing).setOnlyAlertOnce(true).setAutoCancel(!notice.ongoing)
        if(notice.ongoing) {
            builder.setProgress(100,notice.percent ?: 0,notice.percent==null)
            val pause=PendingIntent.getService(this,1,Intent(this,DownloadService::class.java).setAction(PAUSE),PendingIntent.FLAG_IMMUTABLE)
            builder.addAction(Notification.Action.Builder(null,"Pausar",pause).build())
        }
        return builder.build()
    }
    private val tick=object:Runnable { override fun run() {
        val rows=runCatching { queue.snapshot() }.getOrDefault(emptyList())
        if(queue.running) { DownloadNotice.of(rows,true)?.let { manager.notify(ONGOING,build(it)) };handler.postDelayed(this,1000);return }
        // Fila parou: troca a notificação fixa por um aviso do resultado e encerra o serviço.
        stopForeground(STOP_FOREGROUND_REMOVE)
        DownloadNotice.of(rows.filter { it.game.key !in doneBefore.orEmpty() },false)?.let { manager.notify(RESULT,build(it)) }
        doneBefore=null
        stopSelf()
    } }
    override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int {
        if(intent?.action==PAUSE)runCatching { queue.pause() }
        if(doneBefore==null)doneBefore=runCatching { queue.snapshot() }.getOrDefault(emptyList()).filter { it.state==DownloadState.DONE }.map { it.game.key }.toSet()
        val notice=DownloadNotice.of(runCatching { queue.snapshot() }.getOrDefault(emptyList()),true)!!
        if(Build.VERSION.SDK_INT>=29)startForeground(ONGOING,build(notice),ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC) else startForeground(ONGOING,build(notice))
        handler.removeCallbacks(tick);handler.post(tick)
        return START_NOT_STICKY
    }
    override fun onTimeout(startId:Int,fgsType:Int) { runCatching { queue.pause() };stopSelf() } // limite do Android 15 para dataSync
    override fun onDestroy() { handler.removeCallbacks(tick);super.onDestroy() }
    override fun onBind(intent:Intent?):IBinder?=null
}
