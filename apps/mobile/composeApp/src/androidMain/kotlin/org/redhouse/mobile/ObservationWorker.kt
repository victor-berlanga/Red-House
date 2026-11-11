package org.redhouse.mobile

import android.content.Context
import androidx.work.*
import java.util.concurrent.TimeUnit

class ObservationWorker(context:Context,parameters:WorkerParameters):CoroutineWorker(context,parameters) {
    override suspend fun doWork():Result {
        val gateway=GatewayConfiguration.stored(AndroidSecureStore(applicationContext,"gateway"))?:return Result.success()
        val client=platformClient()
        return try {
            val session=Session(Api(client,gatewayBases(gateway)),AndroidSecureStore(applicationContext))
            if(session.user==null)return Result.success()
            session.restore()
            val queue=ObservationQueue(AndroidSecureStore(applicationContext,"observations"),session)
            queue.synchronize()
            if(queue.entries().any {it.text("state") in setOf("PENDING","UNCERTAIN","SENDING")} && runAttemptCount<4) Result.retry() else Result.success()
        } catch(e:ApiFailure) {if(e.status in setOf(401,403))Result.failure() else if(runAttemptCount<4)Result.retry() else Result.failure()}
        catch(_:Exception){if(runAttemptCount<4)Result.retry() else Result.failure()}
        finally{client.close()}
    }
    companion object {
        fun schedule(context:Context) {
            val request=OneTimeWorkRequestBuilder<ObservationWorker>().setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL,30,TimeUnit.SECONDS).build()
            WorkManager.getInstance(context).enqueueUniqueWork("redhouse-observations",ExistingWorkPolicy.KEEP,request)
        }
        fun cancel(context:Context){WorkManager.getInstance(context).cancelUniqueWork("redhouse-observations")}
    }
}
