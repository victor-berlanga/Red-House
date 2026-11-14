package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.datetime.TimeZone

class DayFilterTest {
    @Test fun inclusiveDaysFollowLocalMidnightsAcrossDst() {
        val zone=TimeZone.of("America/New_York")
        val spring=dayFilterBounds(LocalDate(2026,3,8),LocalDate(2026,3,8),zone)
        assertEquals("2026-03-08T05:00:00Z",spring.first)
        assertEquals("2026-03-09T04:00:00Z",spring.second)
        val autumn=dayFilterBounds(LocalDate(2026,11,1),LocalDate(2026,11,1),zone)
        assertEquals("2026-11-01T04:00:00Z",autumn.first)
        assertEquals("2026-11-02T05:00:00Z",autumn.second)
        assertEquals(23L*3600,(Instant.parse(spring.second)-Instant.parse(spring.first)).inWholeSeconds)
    }
    @Test fun openBoundsAndInvalidRange() {
        val zone=TimeZone.UTC
        assertEquals("" to "",dayFilterBounds(null,null,zone))
        assertEquals("" to "2026-11-15T00:00:00Z",dayFilterBounds(null,LocalDate(2026,11,14),zone))
        assertFailsWith<IllegalArgumentException> {dayFilterBounds(LocalDate(2026,11,15),LocalDate(2026,11,14),zone)}
    }
}
