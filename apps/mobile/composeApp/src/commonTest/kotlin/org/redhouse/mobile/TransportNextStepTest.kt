package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class TransportNextStepTest {
    @Test fun actionsRespectRoleInstitutionAndStatus() {
        assertNull(transportAction("TRANSPORT", "a", "a", "b", "PLANNED"))
        assertEquals("PREPARED", transportAction("OPERATOR", "a", "a", "b", "PLANNED"))
        assertNull(transportAction("OPERATOR", "b", "a", "b", "PLANNED"))
        assertEquals("COLLECTED", transportAction("TRANSPORT", "a", "a", "b", "PREPARED"))
        assertNull(transportAction("OPERATOR", "a", "a", "b", "DELIVERED"))
        assertEquals("ACCEPTED", transportAction("OPERATOR", "b", "a", "b", "DELIVERED"))
    }
}
