package org.redhouse.mobile

import kotlin.test.*

class FormValidationTest {
    private val id="12345678-1234-1234-1234-123456789abc"
    @Test fun planningRejectsMalformedIdentityAndUnzonedOrReversedTimes(){
        assertNotNull(planningError("invalid",id,"2026-11-09T12:00:00Z","2026-11-09T13:00:00Z","Motivo"))
        assertNotNull(planningError(id,id,"2026-11-09T12:00:00","2026-11-09T13:00:00Z","Motivo"))
        assertNotNull(planningError(id,id,"2026-11-09T14:00:00Z","2026-11-09T13:00:00Z","Motivo"))
        assertNull(planningError(id,id,"2026-11-09T06:00:00-06:00","2026-11-09T13:00:00Z","Motivo"))
    }
    @Test fun temperaturesMustBeFiniteWithoutInventingClinicalLimits(){
        assertNull(finiteTemperature("NaN"));assertNull(finiteTemperature("Infinity"));assertNull(finiteTemperature("1e999"))
        assertEquals(-50.0,finiteTemperature("-50"));assertEquals(4.2,finiteTemperature(" 4.2 "))
    }
}
