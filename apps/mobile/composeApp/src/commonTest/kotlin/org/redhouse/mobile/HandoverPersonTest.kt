package org.redhouse.mobile

import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class HandoverPersonTest {
    private val task = buildJsonObject { put("id", "s"); put("version", 4) }
    private val context = buildJsonObject { put("shipment_id", "s"); put("shipment_version", 4); put("transport_user_id", "u") }
    private fun projection(shipment: String = "s", version: Int = 4, user: String = "u", name: String = "Cuenta operativa") = buildJsonObject {
        put("shipment_id", shipment); put("shipment_version", version)
        put("transport_user", buildJsonObject { put("id", user); put("name", name) })
    }

    @Test fun personMustMatchAssignmentAndVersion() {
        assertEquals("Cuenta operativa", validatedHandoverPerson("s", task, context, projection())?.text("name"))
        assertNull(validatedHandoverPerson("s", buildJsonObject { put("id", "other"); put("version", 4) }, context, projection()))
        assertNull(validatedHandoverPerson("s", task, context, projection(shipment = "other")))
        assertNull(validatedHandoverPerson("s", task, context, projection(version = 5)))
        assertNull(validatedHandoverPerson("s", task, context, projection(user = "other")))
        assertNull(validatedHandoverPerson("s", task, context, projection(name = "")))
    }
}
