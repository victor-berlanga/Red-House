package org.redhouse.mobile

import io.ktor.client.*
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import io.ktor.http.content.TextContent
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

class SessionTest {
    private class Memory : SecureStore {
        var value: String? = null
        override fun read() = value
        override fun write(value: String?) { this.value = value }
    }
    private val user = obj("id" to "u1", "tenant_id" to "t1", "role" to "TRANSPORT")
    private fun loginResult() = buildJsonObject { put("access_token", "old"); put("refresh_token", "renew"); put("user", user) }
    private fun envelope(data: JsonObject) = buildJsonObject { put("data", data); put("meta", obj("service" to "test")) }.toString()
    private val headers = headersOf(HttpHeaders.ContentType, "application/json")
    @Test fun insecureConfigurationRejected() {
        assertFailsWith<IllegalArgumentException> { requireHttps("http://localhost:5101") }
        assertFailsWith<IllegalArgumentException> { requireHttps("https://user:pass@example.com") }
        requireHttps("https://example.com/services/identidad-acceso")
    }
    @Test fun donorNavigationHasNoOperationalInventory() {
        val paths = screens("DONOR").map { it.path }
        assertFalse(paths.any { "shipments" in it || "resources" in it || "requests" in it })
        assertTrue(paths.any { "appointments" in it })
    }
    @Test fun loginUsesJsonAndDoesNotStorePassword() = runTest {
        val store = Memory()
        val api = Api(HttpClient(MockEngine {
            assertEquals("application/json", it.headers[HttpHeaders.Accept])
            respond(envelope(loginResult()), headers = headers)
        }), mapOf("identidad" to "https://example.com"))
        Session(api, store).login("user", "unique-secret", "")
        assertFalse(store.value!!.contains("unique-secret"))
        assertEquals("renew", codec.parseToJsonElement(store.value!!).jsonObject.text("refresh_token"))
    }
    @Test fun simultaneousUnauthorizedRequestsRotateOnce() = runTest {
        var rotations = 0
        val api = Api(HttpClient(MockEngine { request ->
            when (request.url.encodedPath) {
                "/api/v1/auth/login" -> respond(envelope(loginResult()), headers = headers)
                "/api/v1/auth/refresh" -> {
                    rotations++; delay(10)
                    respond(envelope(obj("access_token" to "new", "refresh_token" to "rotated")), headers = headers)
                }
                else -> if (request.headers[HttpHeaders.Authorization] == "Bearer old") respond("{}", HttpStatusCode.Unauthorized, headers)
                        else respond(envelope(user), headers = headers)
            }
        }), mapOf("identidad" to "https://example.com"))
        val store=Memory(); val session = Session(api, store); session.login("user", "password", "")
        val worker=Session(api,store)
        coroutineScope { List(8) { index -> async { (if(index%2==0)session else worker).request("identidad", "/api/v1/auth/me") } }.awaitAll() }
        assertEquals(1, rotations)
    }
    @Test fun lostRefreshClearsCredentials() = runTest {
        val store = Memory()
        val api = Api(HttpClient(MockEngine { request ->
            when (request.url.encodedPath) {
                "/api/v1/auth/login" -> respond(envelope(loginResult()), headers = headers)
                "/api/v1/auth/refresh" -> error("response lost")
                else -> respond("{}", HttpStatusCode.Unauthorized, headers)
            }
        }), mapOf("identidad" to "https://example.com"))
        val session = Session(api, store); session.login("u", "p", "")
        assertFails { session.request("identidad", "/api/v1/auth/me") }
        assertNull(store.value); assertNull(session.user)
    }
    @Test fun offlineLogoutDestroysLocalCredentials() = runTest {
        val store = Memory()
        val api = Api(HttpClient(MockEngine { request ->
            if (request.url.encodedPath.endsWith("login")) respond(envelope(loginResult()), headers = headers) else error("offline")
        }), mapOf("identidad" to "https://example.com"))
        val session = Session(api, store); session.login("u", "p", "")
        assertFalse(session.logout()); assertNull(store.value)
    }
    @Test fun htmlRejectedAsContractFailure() = runTest {
        val api = Api(HttpClient(MockEngine { respond("<html/>", headers = headersOf(HttpHeaders.ContentType, "text/html")) }), mapOf("identidad" to "https://example.com"))
        assertEquals("contract", assertFailsWith<ApiFailure> { api.call("identidad", "/api/v1/auth/me") }.code)
    }

    @Test fun staleSessionCannotSendAfterAccountSwitch()=runTest {
        val store=Memory();var login=0;var protected=0
        val api=Api(HttpClient(MockEngine{request->
            if(request.url.encodedPath.endsWith("login")) {
                login++;val result=JsonObject(loginResult()+("user" to obj("id" to "user-$login","tenant_id" to "tenant","role" to "TRANSPORT")))
                respond(envelope(result),headers=headers)
            }else {protected++;respond(envelope(obj("ok" to "yes")),headers=headers)}
        }),mapOf("identidad" to "https://example.com"))
        val old=Session(api,store);old.login("first","password","")
        Session(api,store).login("second","password","")
        assertEquals("identity_changed",assertFailsWith<ApiFailure>{old.request("identidad","/api/v1/auth/me")}.code)
        assertEquals(0,protected)
    }
    @Test fun mfaChallengeRequiresASecondLoginWithCode() = runTest {
        var calls=0
        val store=Memory()
        val api=Api(HttpClient(MockEngine { request ->
            calls++
            val body=codec.parseToJsonElement((request.body as TextContent).text).jsonObject
            if(calls==1) {
                assertFalse(body.containsKey("otp"))
                respond("{\"error\":{\"code\":\"mfa_required\"}}",HttpStatusCode.Unauthorized,headers)
            } else {
                assertEquals("123456",body.text("otp"))
                respond(envelope(loginResult()),headers=headers)
            }
        }),mapOf("identidad" to "https://example.com"))
        val session=Session(api,store)
        assertEquals("mfa_required",assertFailsWith<ApiFailure>{session.login("user","secret","")}.code)
        assertNull(store.value)
        session.login("user","secret","123456")
        assertEquals(2,calls);assertNotNull(store.value)
    }

}
