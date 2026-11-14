package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

class TransportNextStepTest {
    @Test fun actionsRespectRoleInstitutionAndStatus() {
        assertNull(transportAction("TRANSPORT", "a", "a", "b", "PLANNED"))
        assertEquals("PREPARED", transportAction("OPERATOR", "a", "a", "b", "PLANNED"))
        assertNull(transportAction("OPERATOR", "b", "a", "b", "PLANNED"))
        assertEquals("COLLECTED", transportAction("TRANSPORT", "a", "a", "b", "PREPARED"))
        assertNull(transportAction("OPERATOR", "a", "a", "b", "DELIVERED"))
        assertEquals("ACCEPTED", transportAction("OPERATOR", "b", "a", "b", "DELIVERED"))
    }
    @Test fun locationSummaryDoesNotImplyARecentFix() {
        assertTrue(transportLocationSummary(null,true).contains("Sin ubicación"))
        val point=buildJsonObject {put("captured_at","2026-11-13T15:21:00Z");put("simulated",true);put("fix_valid",true);put("latitude",25.6);put("longitude",-100.3)}
        assertTrue(transportLocationSummary(point,true).contains("Última ubicación"))
        assertTrue(transportLocationSummary(point,true).contains("simulada"))
        assertTrue(transportLocationSummary(point,false).contains("sin conexión"))
        val invalid=buildJsonObject {put("captured_at","2026-11-13T15:21:00Z");put("fix_valid",false);put("source","SIMULATOR")}
        val invalidSummary=transportLocationSummary(invalid,true)
        assertTrue(invalidSummary.contains("Sin señal GPS"))
        assertTrue(invalidSummary.contains("simulada"))
        assertTrue(!invalidSummary.contains("Última ubicación"))
        assertNull(validMapPosition(invalid))
        assertNull(validMapPosition(buildJsonObject {put("latitude",25.0);put("longitude",-100.0)}))
        assertNull(validMapPosition(buildJsonObject {put("fix_valid",true);put("latitude",91.0);put("longitude",-100.0)}))
        assertNull(validMapPosition(buildJsonObject {put("fix_valid",true);put("latitude","NaN");put("longitude",-100.0)}))
        assertNull(validMapPosition(buildJsonObject {put("fix_valid",true);put("latitude",buildJsonObject {});put("longitude",-100.0)}))
        assertEquals(25.6 to -100.3,validMapPosition(point))
    }
}
