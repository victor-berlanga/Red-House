package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.http.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

/** Pure recovery logic with real Session/Api and MockEngine; no network or GPS integration claim. */
class TrackingReconnectTest {
    private class Memory(var value:String?=null):SecureStore {
        override fun read()=value
        override fun write(value:String?){this.value=value}
    }
    private val shipment="00000000-0000-4000-8000-000000000001"
    private val user=obj("id" to "00000000-0000-4000-8000-000000000002",
        "tenant_id" to "00000000-0000-4000-8000-000000000003","role" to "TRANSPORT")
    private val headers=headersOf(HttpHeaders.ContentType,"application/json")
    private fun envelope(data:JsonObject)=buildJsonObject {put("meta",obj("service" to "test"));put("data",data)}.toString()
    private fun saved()=Memory(buildJsonObject {put("user",user);put("access_token","old");put("refresh_token","renew")}.toString())

    private fun subscribed()=buildJsonObject {
        put("type","subscribed");put("shipment_id",shipment);put("cursor",1);put("state","LIVE")
        put("position",obj("captured_at" to "2026-11-17T00:00:00Z"))
    }

    @Test fun websocketCodesRetainServerStatusSemantics() {
        for(code in listOf("unauthorized","auth_timeout")) assertEquals(401,trackingSocketFailure(code).status)
        for(code in listOf("redis_unavailable","database_unavailable","tracking_unavailable")) assertEquals(503,trackingSocketFailure(code).status)
        for(code in listOf("connection_limit","subscription_limit","rate_limit")) assertEquals(429,trackingSocketFailure(code).status)
        assertEquals(408,trackingSocketFailure("idle_timeout").status)
    }

    @Test fun unauthorizedSocketRechecksSessionRotatesAndReconnectsWithoutReplayingPosition()=runTest {
        var expired=false;var rotations=0;var connections=0
        val paths=mutableListOf<String>()
        val client=HttpClient(MockEngine {request->
            paths+=request.url.encodedPath
            when(request.url.encodedPath) {
                "/api/v1/auth/refresh"->{rotations++;respond(envelope(obj("access_token" to "new","refresh_token" to "rotated")),headers=headers)}
                "/api/v1/auth/me"->if(expired && request.headers[HttpHeaders.Authorization]=="Bearer old")
                    respond("{}",HttpStatusCode.Unauthorized,headers)
                    else respond(envelope(user),headers=headers)
                else->error("Unexpected request")
            }
        })
        try {
            val store=saved();val session=Session(Api(client,mapOf("identidad" to "https://example.com")),store)
            val journalStore=Memory();val journal=LocalJournal(journalStore);journal.bind("owner")
            val pending=obj("event_id" to shipment,"captured_at" to "2026-11-17T00:00:00Z")
            journal.put("position:$shipment",pending)
            val tracking=Tracking(client,session,"https://example.com",journal)
            tracking.followConnection(shipment) {receiveEvent->
                connections++
                if(connections==1) {
                    assertEquals("old",session.accessToken());expired=true
                    receiveEvent(subscribed());assertNotNull(tracking.state.value.position)
                    throw trackingSocketFailure("unauthorized")
                }
                assertEquals("new",session.accessToken());assertNull(tracking.state.value.position)
                // A later genuine denial must terminate, not trigger another refresh.
                throw trackingSocketFailure("forbidden")
            }
            assertEquals(2,connections);assertEquals(1,rotations)
            assertEquals(listOf("/api/v1/auth/me","/api/v1/auth/me","/api/v1/auth/refresh","/api/v1/auth/me"),paths)
            assertEquals(pending,LocalJournal(journalStore).value("position:$shipment"))
            assertFalse(tracking.state.value.connected);assertNull(tracking.state.value.position)
            assertNull(tracking.state.value.acknowledged)
        } finally {client.close()}
    }

    @Test fun revokedSessionStopsAfterSessionRejectsRefresh()=runTest {
        var expired=false;var rotations=0;var connections=0
        val client=HttpClient(MockEngine {request->
            if(request.url.encodedPath.endsWith("refresh")) {
                rotations++;respond("{}",HttpStatusCode.Unauthorized,headers)
            } else if(expired) respond("{}",HttpStatusCode.Unauthorized,headers)
            else respond(envelope(user),headers=headers)
        })
        try {
            val store=saved();val session=Session(Api(client,mapOf("identidad" to "https://example.com")),store)
            val tracking=Tracking(client,session,"https://example.com")
            tracking.followConnection(shipment) {connections++;expired=true;throw trackingSocketFailure("unauthorized")}
            assertEquals(1,connections);assertEquals(1,rotations)
            assertNull(store.value);assertNull(session.user);assertFalse(tracking.state.value.connected)
        } finally {client.close()}
    }

    @Test fun forbiddenAndClosedAssignmentsNeverRetry()=runTest {
        for(code in listOf("forbidden","tracking_closed","unassigned_device","unknown_failure")) {
            var reads=0;var connections=0
            val client=HttpClient(MockEngine {request->
                assertEquals("/api/v1/auth/me",request.url.encodedPath);reads++
                respond(envelope(user),headers=headers)
            })
            try {
                val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
                tracking.followConnection(shipment) {receiveEvent->
                    connections++;receiveEvent(subscribed());assertNotNull(tracking.state.value.position)
                    receiveEvent(obj("type" to "error","code" to code))
                }
                assertEquals(1,reads);assertEquals(1,connections)
                assertFalse(tracking.state.value.connected);assertNull(tracking.state.value.position)
                assertEquals(403,trackingSocketFailure(code).status)
            } finally {client.close()}
        }
    }

    @Test fun transientErrorsUseBoundedReconnectAndKeepAuthorizationCheck()=runTest {
        var reads=0;var connections=0
        val errors=listOf("tracking_unavailable","redis_unavailable","database_unavailable","rate_limit","idle_timeout")
        val client=HttpClient(MockEngine {request->
            assertEquals("/api/v1/auth/me",request.url.encodedPath);reads++
            respond(envelope(user),headers=headers)
        })
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {
                val code=errors.getOrNull(connections)?:"tracking_closed"
                connections++;throw trackingSocketFailure(code)
            }
            assertEquals(6,reads);assertEquals(6,connections)
            assertFalse(tracking.state.value.connected)
        } finally {client.close()}
    }

    @Test fun repeatedUnauthorizedSocketCannotCreateAnUnboundedLoop()=runTest {
        var reads=0;var connections=0
        val client=HttpClient(MockEngine {request->
            assertEquals("/api/v1/auth/me",request.url.encodedPath);reads++
            respond(envelope(user),headers=headers)
        })
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {connections++;throw trackingSocketFailure("unauthorized")}
            assertEquals(8,reads);assertEquals(8,connections)
            assertFalse(tracking.state.value.connected)
        } finally {client.close()}
    }

    @Test fun subscribedThenDisconnectIsBoundedEvenWithSnapshotAndStatus()=runTest {
        var connections=0
        val client=HttpClient(MockEngine {respond(envelope(user),headers=headers)})
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {receiveEvent->
                connections++;assertTrue(connections<=8)
                receiveEvent(subscribed())
                receiveEvent(obj("type" to "tracking.status","state" to "LIVE"))
                // A clean socket close after subscription is also a consecutive failure.
            }
            assertEquals(8,connections);assertFalse(tracking.state.value.connected)
            assertNotNull(tracking.state.value.position)
        } finally {client.close()}
    }

    @Test fun heartbeatAllowsLongSessionButNextConsecutiveFailuresStillStop()=runTest {
        var reads=0;var connections=0
        val client=HttpClient(MockEngine {reads++;respond(envelope(user),headers=headers)})
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {receiveEvent->
                connections++;assertTrue(connections<=19)
                receiveEvent(subscribed())
                if(connections<=12) receiveEvent(obj("type" to "heartbeat"))
                receiveEvent(obj("type" to "error","code" to "unauthorized"))
            }
            // Twelve healthy connections, then the eighth failure since the last heartbeat.
            assertEquals(19,connections);assertEquals(connections,reads)
            assertFalse(tracking.state.value.connected);assertNull(tracking.state.value.position)
        } finally {client.close()}
    }

    @Test fun heartbeatBeforeSubscriptionCannotResetFailures()=runTest {
        var connections=0
        val client=HttpClient(MockEngine {respond(envelope(user),headers=headers)})
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {receiveEvent->
                connections++;assertTrue(connections<=8)
                receiveEvent(obj("type" to "heartbeat"))
                throw trackingSocketFailure("tracking_unavailable")
            }
            assertEquals(8,connections);assertFalse(tracking.state.value.connected)
        } finally {client.close()}
    }

    @Test fun httpForbiddenDuringRecheckPurgesAndStopsWithoutOpeningAnotherSocket()=runTest {
        var reads=0;var connections=0
        val client=HttpClient(MockEngine {request->
            assertEquals("/api/v1/auth/me",request.url.encodedPath);reads++
            if(reads==1) respond(envelope(user),headers=headers)
            else respond("{}",HttpStatusCode.Forbidden,headers)
        })
        try {
            val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),saved()),"https://example.com")
            tracking.followConnection(shipment) {receiveEvent->
                connections++;receiveEvent(subscribed())
                throw trackingSocketFailure("tracking_unavailable")
            }
            assertEquals(2,reads);assertEquals(1,connections)
            assertFalse(tracking.state.value.connected);assertNull(tracking.state.value.position)
        } finally {client.close()}
    }

    @Test fun cancellationClosesWithoutAnotherAttempt()=runTest {
        var reads=0;var connections=0
        val client=HttpClient(MockEngine {reads++;respond(envelope(user),headers=headers)})
        try {
            val store=saved();val tracking=Tracking(client,Session(Api(client,mapOf("identidad" to "https://example.com")),store),"https://example.com")
            assertFailsWith<CancellationException> {
                tracking.followConnection(shipment) {connections++;throw CancellationException("foreground ended")}
            }
            assertEquals(1,reads);assertEquals(1,connections);assertNotNull(store.value)
            assertFalse(tracking.state.value.connected)
        } finally {client.close()}
    }
}
