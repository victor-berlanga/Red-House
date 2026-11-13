package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.*
import io.ktor.client.request.HttpRequestData
import io.ktor.http.*
import io.ktor.http.content.TextContent
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import kotlin.test.*

/** Controlled HTTP/storage doubles: exercises races without claiming native process tests. */
class QueueConcurrencyTest {
    private class Memory : SecureStore {
        @Volatile var value: String? = null
        var failCompletion=false
        override fun read() = value
        override fun write(value: String?) {
            if(failCompletion && value?.contains("\"state\":\"RECORDED\"")==true) {
                failCompletion=false
                throw java.io.IOException("Controlled atomic storage failure")
            }
            this.value=value
        }
    }
    private fun credentials(user:String)=buildJsonObject {
        put("access_token","synthetic-access-$user");put("refresh_token","synthetic-refresh-$user")
        put("user",obj("id" to user,"tenant_id" to "tenant","role" to "TRANSPORT"))
    }.toString()
    private fun recorded(id:String)=buildJsonObject {
        put("command_id",id);put("status","RECORDED");put("cursor",1);put("shipment_version",1)
    }
    private class Lab(handler:suspend (HttpRequestData)->Pair<HttpStatusCode,JsonObject>) : AutoCloseable {
        val store=Memory()
        val sessionStore=Memory()
        val client=HttpClient(MockEngine { request ->
            val (status,data)=handler(request)
            respond(buildJsonObject {
                put("meta",obj("service" to "test-double"))
                put(if(status.isSuccess())"data" else "error",data)
            }.toString(),status,headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val api=Api(client,mapOf("transporte" to "https://example.com"))
        override fun close()=client.close()
    }

    @Test fun concurrentSendersKeepOneCommandAndDurableIdentity(): Unit = runBlocking {
        val entered=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
        var gets=0;var posts=0;var sent:JsonObject?=null
        Lab { request ->
            if(request.method==HttpMethod.Get) {
                gets++;entered.complete(Unit);release.await()
                HttpStatusCode.NotFound to obj("code" to "not_found")
            } else {
                posts++;sent=codec.parseToJsonElement((request.body as TextContent).text).jsonObject
                assertEquals(sent!!.text("id"),request.headers["Idempotency-Key"])
                HttpStatusCode.OK to recorded(sent!!.text("id"))
            }
        }.use { lab ->
            lab.sessionStore.write(credentials("one"))
            val session=Session(lab.api,lab.sessionStore)
            val queue=ObservationQueue(lab.store,session)
            val id=queue.enqueue(newId(),newId(),1,"Observación de concurrencia")
            val original=queue.entries().single().getValue("command")
            val first=launch {queue.synchronize()}
            entered.await()
            assertEquals("SENDING",queue.entries().single().text("state"))
            assertEquals(original,queue.entries().single().getValue("command"))
            val second=launch {ObservationQueue(lab.store,Session(lab.api,lab.sessionStore)).synchronize()}
            release.complete(Unit);joinAll(first,second)
            assertEquals(1,gets);assertEquals(1,posts);assertEquals<JsonElement?>(original,sent)
            assertEquals(id,queue.entries().single().getValue("command").jsonObject.text("id"))
            assertEquals("RECORDED",queue.entries().single().text("state"))
        }
    }

    @Test fun cancellationAfterCommitRecoversWithoutAnotherPost(): Unit = runBlocking {
        val committed=CompletableDeferred<Unit>()
        var saved:JsonObject?=null;var posts=0
        Lab { request ->
            if(request.method==HttpMethod.Get) {
                saved?.let {HttpStatusCode.OK to recorded(it.text("id"))}
                    ?: (HttpStatusCode.NotFound to obj("code" to "not_found"))
            } else {
                posts++;saved=codec.parseToJsonElement((request.body as TextContent).text).jsonObject
                committed.complete(Unit)
                awaitCancellation()
            }
        }.use { lab ->
            lab.sessionStore.write(credentials("one"))
            val queue=ObservationQueue(lab.store,Session(lab.api,lab.sessionStore))
            queue.enqueue(newId(),newId(),1,"Respuesta perdida tras persistir")
            val original=queue.entries().single().getValue("command")
            val sending=launch {queue.synchronize()}
            committed.await();sending.cancelAndJoin()
            assertEquals("SENDING",queue.entries().single().text("state"))
            val restored=ObservationQueue(lab.store,Session(lab.api,lab.sessionStore))
            restored.synchronize()
            assertEquals(1,posts);assertEquals<JsonElement?>(original,saved)
            assertEquals(original,restored.entries().single().getValue("command"))
            assertEquals("RECORDED",restored.entries().single().text("state"))
        }
    }

    @Test fun clearAndAccountChangeDuringLookupNeverResurrectOldQueue(): Unit = runBlocking {
        for(found in listOf(false,true)) {
            val entered=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
            var posts=0
            Lab { request ->
                if(request.method!=HttpMethod.Get) {posts++;error("Removed command must not be submitted")}
                entered.complete(Unit);release.await()
                if(found)HttpStatusCode.OK to recorded(request.url.encodedPath.substringAfterLast('/'))
                else HttpStatusCode.NotFound to obj("code" to "not_found")
            }.use { lab ->
                lab.sessionStore.write(credentials("one"))
                val old=ObservationQueue(lab.store,Session(lab.api,lab.sessionStore))
                old.enqueue(newId(),newId(),1,"Observación de cuenta anterior")
                val sending=launch {old.synchronize()};entered.await()
                withTimeout(1000) {ObservationQueue.clearStore(lab.store)}
                lab.sessionStore.write(credentials("two"))
                val current=ObservationQueue(lab.store,Session(lab.api,lab.sessionStore))
                val fresh=current.enqueue(newId(),newId(),1,"Observación de cuenta nueva")
                release.complete(Unit);sending.join()
                assertEquals(0,posts)
                val row=current.entries().single()
                assertEquals("two",row.text("user"));assertEquals("PENDING",row.text("state"))
                assertEquals(fresh,row.getValue("command").jsonObject.text("id"))
                assertEquals(1,codec.parseToJsonElement(lab.store.value!!).jsonArray.size)
            }
        }
    }

    @Test fun failedCompletionWriteLeavesRecoverableCommand(): Unit = runBlocking {
        var gets=0
        Lab { request ->
            assertEquals(HttpMethod.Get,request.method)
            gets++
            HttpStatusCode.OK to recorded(request.url.encodedPath.substringAfterLast('/'))
        }.use { lab ->
            lab.sessionStore.write(credentials("one"))
            val queue=ObservationQueue(lab.store,Session(lab.api,lab.sessionStore))
            queue.enqueue(newId(),newId(),1,"Recuperación de escritura atómica")
            val original=queue.entries().single().getValue("command")
            lab.store.failCompletion=true
            assertFailsWith<java.io.IOException> {queue.synchronize()}
            assertEquals("SENDING",queue.entries().single().text("state"))
            queue.synchronize()
            assertEquals(2,gets)
            assertEquals(original,queue.entries().single().getValue("command"))
            assertEquals("RECORDED",queue.entries().single().text("state"))
        }
    }
}
