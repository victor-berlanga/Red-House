package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import java.io.File
import kotlin.test.*

/** Controlled network delay; tests storage responsiveness, not physical device latency. */
class QueueCostTest {
    private class Memory : SecureStore {
        var value: String? = null
        override fun read() = value
        override fun write(value: String?) { this.value = value }
    }

    @Test fun enqueueDuringSynchronizationKeepsBothCommands(): Unit = runBlocking {
        val samples=mutableListOf<Double>()
        repeat(6) { iteration ->
            val entered=CompletableDeferred<Unit>()
            val responseHeaders=headersOf(HttpHeaders.ContentType,"application/json")
            fun envelope(data:JsonObject)=buildJsonObject {put("meta",obj("service" to "test-double"));put("data",data)}.toString()
            HttpClient(MockEngine { request ->
                if(request.url.encodedPath.endsWith("login")) respond(envelope(buildJsonObject {
                    put("access_token","synthetic-access");put("refresh_token","synthetic-refresh")
                    put("user",obj("id" to "one","tenant_id" to "tenant","role" to "TRANSPORT"))
                }),headers=responseHeaders)
                else {
                    entered.complete(Unit)
                    delay(250)
                    respond(envelope(buildJsonObject {
                        put("command_id",request.url.encodedPath.substringAfterLast('/'))
                        put("status","RECORDED");put("cursor",1);put("shipment_version",1)
                    }),headers=responseHeaders)
                }
            }).use { http ->
                val session=Session(Api(http,mapOf("identidad" to "https://example.com","transporte" to "https://example.com")),Memory())
                session.login("one","synthetic","")
                val queue=ObservationQueue(Memory(),session)
                val first=queue.enqueue(newId(),newId(),1,"Observación inicial")
                val sending=launch {queue.synchronize()}
                entered.await()
                val started=System.nanoTime()
                val second=queue.enqueue(newId(),newId(),1,"Observación concurrente")
                val elapsed=(System.nanoTime()-started)/1_000_000.0
                sending.join()
                val entries=queue.entries().associateBy {it.getValue("command").jsonObject.text("id")}
                assertEquals(setOf(first,second),entries.keys)
                assertEquals("RECORDED",entries.getValue(first).text("state"))
                assertEquals("PENDING",entries.getValue(second).text("state"))
                if(iteration>0)samples.add(elapsed)
            }
        }
        val baseline=System.getenv("OPT_QUEUE_BASELINE")=="1"
        if(!baseline)assertTrue(samples.sorted()[2]<100,"Enqueue still waits for the 250 ms HTTP response: $samples")
        System.getenv("OPTIMIZATION_MOBILE_EVIDENCE")?.let { path ->
            File(path,"queue-enqueue-"+(if(baseline)"before" else "after")+".json").writeText(buildJsonObject {
                put("environment","JVM MockEngine, in-memory SecureStore, 250 ms response delay; no physical device")
                put("warmup",1);put("repetitions",5);put("median_ms",samples.sorted()[2])
                put("milliseconds",JsonArray(samples.map(::JsonPrimitive)))
                put("commands_preserved",true)
            }.toString())
        }
    }
}
