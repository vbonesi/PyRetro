package com.pyretro.app

import android.content.Context
import androidx.work.*
import java.util.concurrent.TimeUnit

/** Só metadados/diário: nunca baixa ROMs, inicia jogos ou sincroniza saves em segundo plano. */
class LibraryWorker(context:Context,params:WorkerParameters):Worker(context,params) {
    override fun doWork():Result {
        if(!MainActivity.automaticUpdates)return Result.retry()
        val store=LibraryStore(applicationContext)
        if(!store.prefs.getBoolean("google:connected",false))return Result.success()
        return try { store.cloudLibrary.sync();Result.success() }
        catch(error:Exception) {
            store.prefs.edit().putString("library-sync-result","Biblioteca pendente: ${error.message}").apply()
            if(error is GoogleConsentNeeded)Result.failure() else Result.retry()
        } finally { store.closeJournal() }
    }
    companion object {
        private fun constraints()=Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).setRequiresBatteryNotLow(true).build()
        fun schedule(context:Context) {
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("pyretro-library-periodic",ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequest.Builder(LibraryWorker::class.java,15,TimeUnit.MINUTES).setConstraints(constraints()).setInitialDelay(15,TimeUnit.MINUTES).build())
        }
        fun enqueue(context:Context) {
            WorkManager.getInstance(context).enqueueUniqueWork("pyretro-library-now",ExistingWorkPolicy.KEEP,
                OneTimeWorkRequest.Builder(LibraryWorker::class.java).setConstraints(constraints()).setBackoffCriteria(BackoffPolicy.EXPONENTIAL,30,TimeUnit.SECONDS).build())
        }
    }
}
