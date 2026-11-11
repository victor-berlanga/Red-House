package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

class ObservationQueueTest {
    private class Memory : SecureStore {
        var value: String? = null
        override fun read() = value
        override fun write(value: String?) { this.value = value }
    }
    private fun envelope(data: JsonObject) = buildJsonObject { put("meta", obj("service" to "unit-double")); put("data", data) }.toString()
    private val headers = headersOf(HttpHeaders.ContentType, "application/json")
    @Test fun queuedObservationNeverRunsUnderAnotherIdentity() = runTest {
        var account = "one"
        var calls = 0
        val api = Api(HttpClient(MockEngine {
            if (it.url.encodedPath.endsWith("login")) respond(envelope(buildJsonObject {
                put("access_token", "access"); put("refresh_token", "refresh")
                put("user", obj("id" to account, "tenant_id" to "tenant", "role" to "TRANSPORT"))
            }), headers = headers) else { calls++; error("Must not send") }
        }), mapOf("identidad" to "https://example.com", "transporte" to "https://example.com"))
        val session = Session(api, Memory())
        val store = Memory(); val queue = ObservationQueue(store, session)
        session.login("one", "secret", "")
        queue.enqueue(newId(), newId(), 1, "Observación técnica")
        val original = store.value
        account = "two"; session.login("two", "secret", "")
        queue.synchronize()
        assertEquals(0, calls); assertEquals(original, store.value)
    }
    @Test fun missingAcknowledgementNeverBecomesConfirmed() = runTest {
        val api = Api(HttpClient(MockEngine {
            if (it.url.encodedPath.endsWith("login")) respond(envelope(buildJsonObject {
                put("access_token", "access"); put("refresh_token", "refresh")
                put("user", obj("id" to "one", "tenant_id" to "tenant", "role" to "TRANSPORT"))
            }), headers = headers) else respond(envelope(obj("unexpected" to "payload")), headers = headers)
        }), mapOf("identidad" to "https://example.com", "transporte" to "https://example.com"))
        val session = Session(api, Memory()); session.login("one", "secret", "")
        val store = Memory(); val queue = ObservationQueue(store, session)
        val id = queue.enqueue(newId(), newId(), 1, "Observación técnica")
        queue.synchronize()
        val row = codec.parseToJsonElement(store.value!!).jsonArray.single().jsonObject
        assertEquals("UNCERTAIN", row.text("state"))
        assertEquals(id, row.getValue("command").jsonObject.text("id"))
        assertFalse(store.value!!.contains("access_token"))
        assertEquals("TRANSPORT_OBSERVATION", row.getValue("command").jsonObject.getValue("body").jsonObject.text("command"))
    }
}
