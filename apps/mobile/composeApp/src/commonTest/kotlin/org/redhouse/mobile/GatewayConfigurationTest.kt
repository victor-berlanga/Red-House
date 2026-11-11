package org.redhouse.mobile

import kotlinx.coroutines.test.runTest
import kotlin.test.*

class GatewayConfigurationTest {
    private class MemoryStore(var value: String? = null): SecureStore {
        override fun read() = value
        override fun write(value: String?) { this.value = value }
    }

    @Test fun switchingFromLabNeverReusesCredentialsOrPendingObservations() = runTest {
        val config = MemoryStore("https://10.0.2.2:18443")
        val session = MemoryStore("old-session")
        val journal = MemoryStore("old-command")
        val queue = MemoryStore("old-observation")
        var cancelled = false
        assertNull(GatewayConfiguration.stored(config))
        val origin = GatewayConfiguration.prepare(config, session, journal, queue) { cancelled = true }
        assertEquals("https://34.18.186.116", origin)
        assertTrue(cancelled)
        assertNull(session.value); assertNull(journal.value); assertNull(queue.value)
        assertEquals(origin, GatewayConfiguration.stored(config))
    }

    @Test fun sameServerPreservesSessionAndDurableObservations() = runTest {
        val config = MemoryStore(MobileEnvironment.gateway)
        val session = MemoryStore("session")
        val journal = MemoryStore("command")
        val queue = MemoryStore("observation")
        GatewayConfiguration.prepare(config, session, journal, queue) { fail("Must not cancel this server's work") }
        assertEquals("session", session.value)
        assertEquals("command", journal.value)
        assertEquals("observation", queue.value)
    }
}
