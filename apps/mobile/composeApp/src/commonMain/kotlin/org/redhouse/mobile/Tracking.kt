package org.redhouse.mobile

import io.ktor.client.*
import io.ktor.client.plugins.websocket.*
import io.ktor.client.request.*
import io.ktor.websocket.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.*
import kotlinx.datetime.Instant

/** Sources are explicit. External hardware must normalize through the existing bridge. */
enum class PositionSource { ANDROID, IOS, SIMULATOR, GPS_BRIDGE }
data class TrackingState(val connected:Boolean=false,val cursor:Long?=null,val position:JsonObject?=null,
                         val status:String="Desconectado",val acknowledged:String?=null)
class Tracking(private val client:HttpClient,private val session:Session,private val base:String,private val journal:LocalJournal?=null) {
    private val mutable=MutableStateFlow(TrackingState())
    val state:StateFlow<TrackingState> = mutable.asStateFlow()
    private var socket:DefaultClientWebSocketSession?=null
    private val publishing=Mutex()
    private var acknowledgment:CompletableDeferred<Unit>?=null
    private var pendingId:String?=null
    init {requireHttps(base)}
    /** Explicit local discard never asserts remote persistence or changes custody. */
    suspend fun discardPending(shipment:String)=publishing.withLock {
        require(shipment.matches(Regex("[0-9a-f-]{36}")))
        journal?.remove("position:$shipment")
        mutable.value=mutable.value.copy(status="Lectura local descartada; recepción remota no confirmada")
    }
    private fun applyPosition(event:JsonObject) {
        val point=event["position"] as? JsonObject?:return
        val old=mutable.value.position
        val captured=Instant.parse(point.text("captured_at"))
        val previous=old?.let {Instant.parse(it.text("captured_at"))}
        if(previous==null || captured>=previous) mutable.value=mutable.value.copy(position=point)
    }
    /** The UI owns this job. Background, task exit and logout cancel it and close its socket. */
    suspend fun follow(shipment:String) {
        require(shipment.matches(Regex("[0-9a-f-]{36}")))
        var attempt=0
        while(currentCoroutineContext().isActive && attempt<8) {
            try {
                // Recheck session and rotate access before each new handshake.
                session.request("identidad","/api/v1/auth/me")
                client.webSocket(base.replaceFirst("https://","wss://").trimEnd('/')+"/ws/v1/tracking/json",request={
                    header("Sec-WebSocket-Protocol","redhouse.tracking.v1.json")
                }) {
                    send(obj("type" to "authenticate","credential_kind" to "user","credential" to session.accessToken()).toString())
                    val frame=withTimeout(8000) {incoming.receive()} as? Frame.Text?:throw ApiFailure(502,"socket")
                    val authenticated=codec.parseToJsonElement(frame.readText()).jsonObject
                    if(authenticated.text("type")!="authenticated") throw ApiFailure(403,authenticated.text("code"))
                    socket=this
                    send(buildJsonObject {put("type","subscribe");put("shipment_id",shipment);mutable.value.cursor?.let {put("cursor",it)}}.toString())
                    coroutineScope {
                        val heartbeat=launch {while(isActive) {delay(15000);send(obj("type" to "heartbeat").toString())}}
                        try {for(message in incoming) {
                            if(message !is Frame.Text) throw ApiFailure(502,"binary")
                            val raw=message.readText();require(raw.length<=65536)
                            val event=codec.parseToJsonElement(raw).jsonObject
                            when(event.text("type")) {
                                "subscribed" -> {applyPosition(event);mutable.value=mutable.value.copy(connected=true,cursor=event["cursor"]?.jsonPrimitive?.longOrNull,status=event.text("state"));attempt=0}
                                "position.updated" -> {
                                    val cursor=event["cursor"]?.jsonPrimitive?.longOrNull?:throw ApiFailure(502,"cursor")
                                    if(cursor>(mutable.value.cursor?:-1)) {applyPosition(event);mutable.value=mutable.value.copy(cursor=cursor,status="Observación recibida")}
                                }
                                "position.ack" -> if(event.text("event_id")==pendingId && event.text("state")=="PERSISTED_SQL") {
                                    journal?.remove("position:$shipment");mutable.value=mutable.value.copy(acknowledged=pendingId)
                                    acknowledgment?.complete(Unit)
                                }
                                "resync.required" -> {mutable.value=mutable.value.copy(cursor=null,status="Cursor vencido; recuperando instantánea");throw ApiFailure(409,"cursor")}
                                "error" -> throw ApiFailure(if(event.text("code") in setOf("redis_unavailable","database_unavailable")) 503 else 403,event.text("code"))
                                "tracking.status" -> mutable.value=mutable.value.copy(status=event.text("state"))
                            }
                        }} finally {heartbeat.cancel()}
                    }
                }
            } catch(e:CancellationException) {throw e}
            catch(e:ApiFailure) {if(e.status in setOf(401,403)) {mutable.value=mutable.value.copy(position=null,status=e.message.orEmpty());return}}
            catch(_:Exception) { /* State below retains the last observation and marks disconnection. */ }
            finally {socket=null;mutable.value=mutable.value.copy(connected=false);acknowledgment?.completeExceptionally(ApiFailure(503,"socket_closed"))}
            mutable.value=mutable.value.copy(status="Desconectado; última observación, no ubicación actual")
            delay((1000L shl attempt.coerceAtMost(5))+kotlin.random.Random.nextLong(500));attempt++
        }
    }
    suspend fun publish(position:JsonObject)=publishing.withLock {
        require(position.text("source") in PositionSource.entries.map {it.name})
        val shipment=position.text("shipment_id")
        val old=journal?.value("position:$shipment") as? JsonObject
        val point=old?:position.also {journal?.put("position:$shipment",it)}
        val connection=socket?:throw ApiFailure(503,"socket")
        if(!mutable.value.connected) throw ApiFailure(503,"socket")
        pendingId=point.text("event_id");acknowledgment=CompletableDeferred()
        connection.send(buildJsonObject {put("type","position.publish");put("position",point)}.toString())
        try {withTimeout(10000) {acknowledgment!!.await()}} finally {acknowledgment=null;pendingId=null}
    }
}
