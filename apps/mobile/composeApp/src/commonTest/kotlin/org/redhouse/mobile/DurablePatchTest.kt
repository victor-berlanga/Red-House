package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.http.*
import io.ktor.http.content.TextContent
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

class DurablePatchTest {
    private class Memory : SecureStore {
        var value:String?=null
        var failNextWrite=false
        override fun read()=value
        override fun write(value:String?) {
            if(failNextWrite){failNextWrite=false;throw IllegalStateException("Injected store failure")}
            this.value=value
        }
    }

    @Test fun legacyJournalWithoutMethodReplaysPost()=runTest {
        var method:HttpMethod?=null
        val client=HttpClient(MockEngine { request ->
            val result=if(request.url.encodedPath.endsWith("/login")) buildJsonObject {
                put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
            } else {method=request.method;obj("ok" to "yes")}
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory());session.login("u","p","")
        val journal=LocalJournal(Memory());val body=obj("value" to "original")
        val command=buildJsonObject {put("id","stable");put("service","donantes");put("path","/api/v1/old");put("body",body)}
        journal.put("command:donantes:/api/v1/old",command)
        MobileRepository(session,journal,"ANDROID").recover(command)
        assertEquals(HttpMethod.Post,method);assertTrue(journal.pendingCommands().isEmpty())
    }
    @Test fun staleVersionDoesNotLeaveAnUnrecoverablePendingPatch()=runTest {
        val client=HttpClient(MockEngine { request ->
            if(request.url.encodedPath.endsWith("/login")) {
                val login=buildJsonObject {put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))}
                respond(buildJsonObject {put("data",login);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            } else respond("{\"error\":{\"code\":\"stale_version\"}}",HttpStatusCode.Conflict,headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory());session.login("u","p","")
        val journal=LocalJournal(Memory());val repository=MobileRepository(session,journal,"ANDROID")
        val body=buildJsonObject {put("display_name","Nombre");put("version",1)}
        assertEquals("stale_version",assertFailsWith<ApiFailure>{repository.execute("donantes","/api/v1/donors/d/personal",body,HttpMethod.Patch)}.code)
        assertTrue(journal.pendingCommands().isEmpty())
    }
    @Test fun lostPatchReplaysIdenticalBodyAndKeyAfterRecreation()=runTest {
        val calls=mutableListOf<Triple<HttpMethod,String,String>>()
        val client=HttpClient(MockEngine { request ->
            val result=if(request.url.encodedPath.endsWith("/login")) buildJsonObject {
                put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
            } else {
                calls.add(Triple(request.method,request.headers["Idempotency-Key"].orEmpty(),(request.body as TextContent).text))
                if(calls.size==1) error("response lost")
                buildJsonObject {put("id","d");put("display_name","Nombre nuevo");put("version",2)}
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory())
        session.login("u","p","")
        val storage=Memory();val journal=LocalJournal(storage);val body=buildJsonObject {put("display_name","Nombre nuevo");put("version",1)}
        val first=MobileRepository(session,journal,"ANDROID")
        assertFails {first.execute("donantes","/api/v1/donors/d/personal",body,HttpMethod.Patch)}
        val recovered=MobileRepository(session,LocalJournal(storage),"ANDROID")
        val pending=recovered.journal.pendingCommands().values.single().jsonObject
        assertEquals("Nombre nuevo",recovered.recover(pending).text("display_name"))
        assertEquals(2,calls.size);assertEquals(HttpMethod.Patch,calls[0].first)
        assertTrue(calls[0].second.isNotBlank());assertEquals(calls[0],calls[1])
        assertTrue(recovered.journal.pendingCommands().isEmpty())
    }
    @Test fun uncertainReservationBlocksNewBodyAndOnlyExplicitlyReplaysOriginal()=runTest {
        val calls=mutableListOf<Pair<String,String>>()
        val client=HttpClient(MockEngine { request ->
            if(request.url.encodedPath.endsWith("/login")) {
                val login=buildJsonObject {put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))}
                respond(buildJsonObject {put("data",login);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            } else {
                calls.add(request.headers["Idempotency-Key"].orEmpty() to (request.body as TextContent).text)
                if(calls.size==1) error("response lost")
                val status=if(calls.size==2)HttpStatusCode.ServiceUnavailable else HttpStatusCode.Conflict
                val code=if(calls.size==2)"service_unavailable" else "active_appointment"
                respond("{\"error\":{\"code\":\"$code\"}}",status,headersOf(HttpHeaders.ContentType,"application/json"))
            }
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory());session.login("u","p","")
        val storage=Memory();val repository=MobileRepository(session,LocalJournal(storage),"IOS")
        val original=obj("donor_id" to "d","campaign_id" to "c","slot_id" to "original")
        assertFails {repository.execute("donantes","/api/v1/appointments",original)}
        val saved=repository.journal.pendingCommands().values.single().jsonObject
        val changed=JsonObject(original+("slot_id" to JsonPrimitive("another")))
        assertEquals("pending_operation",assertFailsWith<ApiFailure>{repository.execute("donantes","/api/v1/appointments",changed)}.code)
        assertEquals(1,calls.size)
        val forged=JsonObject(saved+("id" to JsonPrimitive("different-key")))
        assertEquals("pending_operation_changed",assertFailsWith<ApiFailure>{repository.recover(forged)}.code)
        assertEquals(saved,repository.journal.pendingCommands().values.single())
        val restored=MobileRepository(session,LocalJournal(storage),"IOS")
        assertEquals(503,assertFailsWith<ApiFailure>{restored.recover(saved)}.status)
        assertEquals(saved,restored.journal.pendingCommands().values.single())
        assertEquals("active_appointment",assertFailsWith<ApiFailure>{restored.recover(saved)}.code)
        assertTrue(restored.journal.pendingCommands().isEmpty())
        assertEquals(3,calls.size);assertTrue(calls[0].first.isNotBlank());assertTrue(calls.all {it==calls[0]})
        assertEquals("pending_operation_changed",assertFailsWith<ApiFailure>{restored.recover(saved)}.code)
        assertEquals(3,calls.size)
    }
    @Test fun failedCommandPreparationSendsNothingAndRetryPersistsBeforeHttp()=runTest {
        val storage=Memory();val calls=mutableListOf<Pair<String,String>>()
        val body=buildJsonObject {put("display_name","Nombre");put("version",1)}
        val client=HttpClient(MockEngine { request ->
            val result=if(request.url.encodedPath.endsWith("/login")) buildJsonObject {
                put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
            } else {
                val persisted=LocalJournal(storage).pendingCommands().values.single().jsonObject
                val key=request.headers["Idempotency-Key"].orEmpty()
                assertTrue(key.isNotBlank());assertEquals(persisted.text("id"),key)
                assertEquals(body,persisted["body"]);assertEquals("PATCH",persisted.text("method"))
                calls+=key to (request.body as TextContent).text
                buildJsonObject {put("id","d");put("display_name","Nombre");put("version",2)}
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory())
            session.login("u","p","")
            val repository=MobileRepository(session,LocalJournal(storage),"ANDROID")
            storage.failNextWrite=true
            assertFailsWith<IllegalStateException>{repository.execute("donantes","/api/v1/donors/d/personal",body,HttpMethod.Patch)}
            assertTrue(calls.isEmpty());assertTrue(repository.journal.pendingCommands().isEmpty());assertNull(storage.value)
            assertEquals("Nombre",repository.execute("donantes","/api/v1/donors/d/personal",body,HttpMethod.Patch).text("display_name"))
            assertEquals(1,calls.size);assertEquals(body,codec.parseToJsonElement(calls.single().second))
            assertTrue(repository.journal.pendingCommands().isEmpty());assertTrue(LocalJournal(storage).pendingCommands().isEmpty())
        } finally {client.close()}
    }
    @Test fun failedConfirmedCommandRemovalKeepsOriginalKeyForRecovery()=runTest {
        val storage=Memory();val calls=mutableListOf<Pair<String,String>>()
        val body=buildJsonObject {put("display_name","Nombre");put("version",1)}
        val client=HttpClient(MockEngine { request ->
            val result=if(request.url.encodedPath.endsWith("/login")) buildJsonObject {
                put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
            } else {
                val persisted=LocalJournal(storage).pendingCommands().values.single().jsonObject
                val key=request.headers["Idempotency-Key"].orEmpty()
                assertEquals(persisted.text("id"),key)
                calls+=key to (request.body as TextContent).text
                if(calls.size==1)storage.failNextWrite=true
                buildJsonObject {put("id","d");put("display_name","Nombre");put("version",2)}
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory())
            session.login("u","p","")
            val repository=MobileRepository(session,LocalJournal(storage),"ANDROID")
            assertFailsWith<IllegalStateException>{repository.execute("donantes","/api/v1/donors/d/personal",body,HttpMethod.Patch)}
            val pending=repository.journal.pendingCommands().values.single().jsonObject
            assertEquals(calls.single().first,pending.text("id"));assertEquals(body,pending["body"])
            val restored=MobileRepository(session,LocalJournal(storage),"ANDROID")
            assertEquals(pending,restored.journal.pendingCommands().values.single())
            assertEquals("Nombre",restored.recover(pending).text("display_name"))
            assertEquals(2,calls.size);assertEquals(calls[0],calls[1])
            assertTrue(restored.journal.pendingCommands().isEmpty());assertTrue(LocalJournal(storage).pendingCommands().isEmpty())
        } finally {client.close()}
    }
}
