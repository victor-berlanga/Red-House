package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import kotlinx.coroutines.test.runTest
import kotlin.test.*

class TrackingRecoveryTest {
    private class Memory:SecureStore {
        private var content:String?=null
        override fun read()=content
        override fun write(value:String?){content=value}
    }
    @Test fun explicitDiscardKeepsOtherTaskAndCustodyWithoutInventingAcknowledgement()=runTest {
        val client=HttpClient(MockEngine{error("Local discard must not call a service")})
        try {
            val store=Memory();val journal=LocalJournal(store);journal.bind("owner")
            val task=newId();val other=newId();val event=newId()
            journal.put("position:$task",obj("event_id" to event,"captured_at" to "2026-01-01T00:00:00Z"))
            journal.put("position:$other",obj("event_id" to newId()))
            val custody=obj("id" to newId());journal.put("transition:$task",custody)
            val session=Session(Api(client,mapOf("identidad" to "https://example.com")),Memory())
            val tracking=Tracking(client,session,"https://example.com",journal)
            tracking.discardPending(task)
            val restored=LocalJournal(store)
            assertNull(restored.value("position:$task"))
            assertNotNull(restored.value("position:$other"))
            assertEquals(custody,restored.value("transition:$task"))
            assertNull(tracking.state.value.acknowledged)
            assertFalse(tracking.state.value.connected)
        }finally{client.close()}
    }
}
