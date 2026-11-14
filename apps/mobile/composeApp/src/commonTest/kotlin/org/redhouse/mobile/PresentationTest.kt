package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.datetime.LocalDate
import kotlinx.datetime.TimeZone

class PresentationTest {
    @Test fun datesKeepOffsetAndPrecision() {
        assertEquals("10/11/2026 · 09:12:13.456 UTC-06:00", displayDate("2026-11-10T09:12:13.456-06:00"))
        assertEquals("10/11/2026 · 15:12:13 UTC", displayDate("2026-11-10T15:12:13Z"))
        assertEquals("dato no disponible", displayDate("dato no disponible"))
    }
    @Test fun briefDatesUseTheSameLocalInstantRegardlessOfSourceOffset() {
        val first=displayBriefDate("2026-11-10T15:12:13.456Z")
        val second=displayBriefDate("2026-11-10T09:12:13.456-06:00")
        assertEquals(first,second)
        assertFalse(first.contains(".456"));assertFalse(first.contains("UTC"))
    }
    @Test fun selectedLocalTimePreservesSecondsAndRejectsClockGap() {
        assertEquals("2026-11-10T15:12:13Z",localCandidates(LocalDate(2026,11,10),9,12,13,TimeZone.of("America/Monterrey")).single().toString())
        assertEquals("2026-11-10T15:12:13.123456Z",localCandidates(LocalDate(2026,11,10),9,12,13,TimeZone.of("America/Monterrey"),123456000).single().toString())
        assertTrue(localCandidates(LocalDate(2026,3,8),2,30,0,TimeZone.of("America/New_York")).isEmpty())
        assertEquals(2,localCandidates(LocalDate(2026,11,1),1,30,0,TimeZone.of("America/New_York")).size)
    }
    @Test fun labelsDoNotChangeFreeTextOrMergeUncertainty() {
        assertEquals("AUTHORIZED", displayValue("title", "AUTHORIZED"))
        assertEquals("Autorizado documentalmente", displayValue("result_state", "AUTHORIZED"))
        assertNotEquals(displayValue("status", "UNCERTAIN"), displayValue("status", "CONFIRMED"))
        assertNotEquals(displayValue("status", "NOT_CHECKED"), displayValue("status", "REJECTED"))
        assertEquals("Aplazado", displayValue("status", "DEFERRED"))
        assertEquals("FUTURE_STATE", displayValue("status", "FUTURE_STATE"))
    }
}
