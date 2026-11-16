package org.redhouse.mobile

import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.JsonPrimitive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SessionOwnerTest {
    private class Memory(var raw:String?,private val name:String,private val writes:MutableList<String>):SecureStore {
        var failNextWrite=false
        override fun read()=raw
        override fun write(value:String?){
            if(failNextWrite){failNextWrite=false;writes+="$name-failed";throw IllegalStateException("Injected store failure")}
            raw=value;writes+=name
        }
    }
    private class Pending {
        val writes=mutableListOf<String>()
        val local=Memory(null,"journal",writes)
        val queue=Memory("[{\"user\":\"user-a\",\"tenant\":\"tenant-a\",\"state\":\"UNCERTAIN\",\"command\":{\"id\":\"saved-observation\"}}]","queue",writes)
        val journal=LocalJournal(local)
        init {
            journal.bind("https://gateway.test:user-a:tenant-a")
            journal.put("command:donantes:/api/v1/appointments",obj("id" to "original-key","body" to "original-body"))
            writes.clear()
        }
    }
    @Test fun failedAuthenticationPreservesJournalAndQueue()=runTest {
        val pending=Pending();val beforeJournal=pending.local.raw;val beforeQueue=pending.queue.raw
        assertFailsWith<ApiFailure> {
            authenticateAndBindOwner("https://gateway.test",pending.journal,pending.queue) {
                throw ApiFailure(401,"unauthorized")
            }
        }
        assertEquals(beforeJournal,pending.local.raw);assertEquals(beforeQueue,pending.queue.raw)
        assertTrue(pending.writes.isEmpty())
    }
    @Test fun sameAuthenticatedOwnerPreservesOriginalCommandsAndObservations()=runTest {
        val pending=Pending();val beforeJournal=pending.local.raw;val beforeQueue=pending.queue.raw
        val user=authenticateAndBindOwner("https://gateway.test",pending.journal,pending.queue) {
            pending.writes+="authenticated";obj("id" to "user-a","tenant_id" to "tenant-a")
        }
        assertEquals("user-a",user.text("id"))
        assertEquals(beforeJournal,pending.local.raw);assertEquals(beforeQueue,pending.queue.raw)
        assertEquals(listOf("authenticated"),pending.writes)
    }
    @Test fun differentAuthenticatedOwnerClearsQueueAndBindsBeforeReturn()=runTest {
        for((gateway,userId,tenantId) in listOf(
            Triple("https://gateway.test","user-b","tenant-a"),
            Triple("https://gateway.test","user-a","tenant-b"),
            Triple("https://other.test","user-a","tenant-a")
        )) {
            val pending=Pending()
            authenticateAndBindOwner(gateway,pending.journal,pending.queue) {
                pending.writes+="authenticated";obj("id" to userId,"tenant_id" to tenantId)
            }
            assertEquals(JsonPrimitive("$gateway:$userId:$tenantId"),pending.journal.value("identity"))
            assertTrue(pending.journal.pendingCommands().isEmpty());assertNull(pending.queue.raw)
            assertEquals(listOf("authenticated","queue","journal"),pending.writes)
        }
    }
    @Test fun failedOwnerPersistenceKeepsOriginalIdentityAndRetryPersistsNewOwner()=runTest {
        val pending=Pending()
        val oldIdentity=pending.journal.value("identity")
        val oldCommands=pending.journal.pendingCommands()
        val oldDisk=pending.local.raw
        val nextUser=obj("id" to "user-b","tenant_id" to "tenant-a")
        var published=false
        pending.local.failNextWrite=true
        assertFailsWith<IllegalStateException> {
            authenticateAndBindOwner("https://gateway.test",pending.journal,pending.queue) {
                pending.writes+="authenticated";nextUser
            }
            published=true
        }
        assertFalse(published)
        assertEquals(oldDisk,pending.local.raw)
        assertEquals(oldIdentity,pending.journal.value("identity"))
        assertEquals(oldCommands,pending.journal.pendingCommands())
        assertEquals(oldIdentity,LocalJournal(pending.local).value("identity"))
        // Queue removal may finish before journal persistence fails; no multistore transaction is claimed.
        assertNull(pending.queue.raw)
        authenticateAndBindOwner("https://gateway.test",pending.journal,pending.queue) {
            pending.writes+="authenticated";nextUser
        }
        val newIdentity=JsonPrimitive("https://gateway.test:user-b:tenant-a")
        assertEquals(newIdentity,pending.journal.value("identity"))
        assertEquals(newIdentity,LocalJournal(pending.local).value("identity"))
        assertTrue(pending.journal.pendingCommands().isEmpty())
        assertEquals(listOf("authenticated","queue","journal-failed","authenticated","queue","journal"),pending.writes)
    }
}
