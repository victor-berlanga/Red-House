package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.http.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

class PhotoRecoveryTest {
    private class Memory:SecureStore {
        var value:String?=null
        override fun read()=value
        override fun write(value:String?) {this.value=value}
    }

    @Test fun separateStableKeysAndReplayAfterLostResponses()=runTest {
        val prepares=mutableListOf<String>()
        val verifications=mutableListOf<String>()
        var uploads=0
        var verified=false
        val client=HttpClient(MockEngine { request ->
            val path=request.url.encodedPath
            if(path.startsWith("/storage/")) {
                uploads++
                respond("",if(uploads==1) HttpStatusCode.ServiceUnavailable else HttpStatusCode.PreconditionFailed)
            } else {
                val data=when {
                    path.endsWith("/login") -> buildJsonObject {
                        put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "OPERATOR"))
                    }
                    path.endsWith("/files") -> {
                        prepares+=request.headers["Idempotency-Key"].orEmpty()
                        buildJsonObject {
                            put("file",obj("id" to "f","status" to if(verified) "VERIFIED" else "PENDING"))
                            put("upload_url","https://example.com/storage/v1/objects/capability")
                            put("upload_headers",obj("Content-Type" to "image/jpeg"))
                        }
                    }
                    path.endsWith("/verify") -> {
                        verifications+=request.headers["Idempotency-Key"].orEmpty()
                        if(!verified) {verified=true;error("verification response lost")}
                        obj("id" to "f","status" to "VERIFIED")
                    }
                    else -> error("unexpected request")
                }
                respond(buildJsonObject {put("data",data);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            }
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","documentos" to "https://example.com")),Memory())
        session.login("operator1","password","")
        val store=Memory()
        val photo=byteArrayOf(1,2,3)
        assertFailsWith<ApiFailure> {MobileRepository(session,LocalJournal(store),"ANDROID").uploadPhoto("shipment",photo)}
        assertFails {MobileRepository(session,LocalJournal(store),"ANDROID").uploadPhoto("shipment",photo)}
        val result=MobileRepository(session,LocalJournal(store),"ANDROID").uploadPhoto("shipment",photo)
        assertEquals("VERIFIED",result.text("status"))
        assertEquals(3,prepares.size);assertTrue(prepares.first().isNotBlank());assertEquals(1,prepares.distinct().size)
        assertEquals(2,verifications.size);assertEquals(1,verifications.distinct().size)
        assertEquals(prepares.first()+"-verify",verifications.first())
        assertEquals(2,uploads) // VERIFIED replay must never issue another PUT.
        client.close()
    }

    @Test fun scannerFailureRetriesVerificationWithoutAnotherUpload()=runTest {
        var stored=false
        var scanFailed=false
        var uploads=0
        val keys=mutableListOf<String>()
        val client=HttpClient(MockEngine { request ->
            val path=request.url.encodedPath
            if(path.startsWith("/storage/")) {
                uploads++;stored=true;respond("",HttpStatusCode.Created)
            } else if(path.endsWith("/verify") && !scanFailed) {
                keys+=request.headers["Idempotency-Key"].orEmpty();scanFailed=true
                respond("{\"error\":{\"code\":\"scanner_unavailable\"}}",HttpStatusCode.ServiceUnavailable,headersOf(HttpHeaders.ContentType,"application/json"))
            } else {
                val data=when {
                    path.endsWith("/login") -> buildJsonObject {
                        put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "OPERATOR"))
                    }
                    path.endsWith("/files") -> buildJsonObject {
                        put("file",obj("id" to "f","status" to if(stored) "ERROR" else "PENDING"))
                        put("upload_url","https://example.com/storage/v1/objects/capability")
                        put("upload_headers",obj("Content-Type" to "image/jpeg"))
                    }
                    path.endsWith("/verify") -> {
                        keys+=request.headers["Idempotency-Key"].orEmpty();obj("id" to "f","status" to "VERIFIED")
                    }
                    else -> error("unexpected request")
                }
                respond(buildJsonObject {put("data",data);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            }
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","documentos" to "https://example.com")),Memory())
        session.login("operator1","password","")
        val store=Memory();val photo=byteArrayOf(1,2,3)
        assertEquals("scanner_unavailable",assertFailsWith<ApiFailure> {MobileRepository(session,LocalJournal(store),"ANDROID").uploadPhoto("shipment",photo)}.code)
        assertEquals("VERIFIED",MobileRepository(session,LocalJournal(store),"ANDROID").uploadPhoto("shipment",photo).text("status"))
        assertEquals(1,uploads);assertEquals(2,keys.size);assertTrue(keys.first().isNotBlank());assertEquals(keys.first(),keys.last())
        client.close()
    }
}
