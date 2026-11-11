package org.redhouse.mobile

import kotlinx.coroutines.*

/** iOS gives a bounded background opportunity; the durable queue remains the authority on pending work. */
object BackgroundSync {
    private val scope=CoroutineScope(SupervisorJob()+Dispatchers.Default)
    private var job:Job?=null
    fun start(store:SecureStore,queue:SecureStore,config:SecureStore,done:(Boolean)->Unit){
        job?.cancel()
        job=scope.launch{
            val client=platformClient()
            try{
                val origin=GatewayConfiguration.stored(config)?:throw ApiFailure(401,"locked_or_logged_out")
                val session=Session(Api(client,gatewayBases(origin)),store);session.restore()
                val pending=ObservationQueue(queue,session);pending.synchronize()
                done(pending.entries().none{it.text("state") in setOf("PENDING","UNCERTAIN","SENDING")})
            }catch(e:CancellationException){throw e}catch(_:Exception){done(false)}finally{client.close()}
        }
    }
    fun cancel(){job?.cancel();job=null}
}
