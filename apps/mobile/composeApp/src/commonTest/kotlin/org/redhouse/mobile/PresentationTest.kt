package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals

class PresentationTest {
    @Test fun datesKeepOffsetAndPrecision() {
        assertEquals("10/11/2026 · 09:12:13.456 UTC-06:00", displayDate("2026-11-10T09:12:13.456-06:00"))
        assertEquals("10/11/2026 · 15:12:13 UTC", displayDate("2026-11-10T15:12:13Z"))
        assertEquals("dato no disponible", displayDate("dato no disponible"))
    }
    @Test fun labelsDoNotChangeFreeTextOrMergeUncertainty() {
        assertEquals("AUTHORIZED", displayValue("title", "AUTHORIZED"))
        assertEquals("Autorizado documentalmente", displayValue("result_state", "AUTHORIZED"))
        assertNotEquals(displayValue("status", "UNCERTAIN"), displayValue("status", "CONFIRMED"))
        assertNotEquals(displayValue("status", "NOT_CHECKED"), displayValue("status", "REJECTED"))
        assertEquals("FUTURE_STATE", displayValue("status", "FUTURE_STATE"))
    }
}
