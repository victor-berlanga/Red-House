package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
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
    @Test fun noticeCodesDoNotTranslateFreeTextOrUnknownCodes() {
        assertEquals("Recordatorio de tu cita",displayValue("message_code","APPOINTMENT_REMINDER"))
        assertEquals("Evaluación del donante registrada",displayValue("message_code","DONOR_REVIEWED"))
        assertEquals("APPOINTMENT_REMINDER",displayValue("title","APPOINTMENT_REMINDER"))
        assertEquals("APPOINTMENT_REMINDER",displayValue("message","APPOINTMENT_REMINDER"))
        assertEquals("FUTURE_NOTICE",displayValue("message_code","FUTURE_NOTICE"))
    }
    @Test fun labelsDoNotChangeFreeTextOrMergeUncertainty() {
        assertEquals("AUTHORIZED", displayValue("title", "AUTHORIZED"))
        assertEquals("Autorizado documentalmente", displayValue("result_state", "AUTHORIZED"))
        assertNotEquals(displayValue("status", "UNCERTAIN"), displayValue("status", "CONFIRMED"))
        assertNotEquals(displayValue("status", "NOT_CHECKED"), displayValue("status", "REJECTED"))
        assertEquals("Aplazado", displayValue("status", "DEFERRED"))
        assertEquals("FUTURE_STATE", displayValue("status", "FUTURE_STATE"))
    }
    @Test fun severityUrgencyAndEligibilityAreShownInSpanish() {
        assertEquals("Informativo", displayValue("severity", "INFO"))
        assertEquals("Advertencia", displayValue("severity", "WARNING"))
        assertEquals("Crítico", displayValue("severity", "CRITICAL"))
        assertEquals("FUTURE_LEVEL", displayValue("severity", "FUTURE_LEVEL"))
        assertEquals("Alta", displayValue("urgency", "HIGH"))
        assertEquals("Elegible para donar", displayValue("status", "ELIGIBLE"))
        assertEquals("Leída", displayValue("status", "ACKNOWLEDGED"))
        // Free text keeps the code as sent; only the coded fields are translated.
        assertEquals("INFO", displayValue("message", "INFO"))
        assertEquals("ELIGIBLE", displayValue("title", "ELIGIBLE"))
    }
    @Test fun nestedDetailDoesNotRepeatTheShellTitle() {
        assertNull(detailSubtitle("Avisos", "Avisos"))
        assertNull(detailSubtitle("", "Avisos"))
        assertEquals("Muestras autorizadas", detailSubtitle("Muestras autorizadas", "Laboratorio"))
    }
    @Test fun revokedSessionIsNotReportedAsWrongPassword() {
        assertEquals("Cuenta o contraseña incorrectas.", failureMessage(ApiFailure(401, "unauthorized"), signedIn = false))
        assertEquals("Sesión vencida o revocada. Inicia sesión.", failureMessage(ApiFailure(401, "unauthorized"), signedIn = true))
        assertEquals("Sesión vencida o revocada. Inicia sesión.", failureMessage(ApiFailure(401, "session"), signedIn = true))
        assertEquals("Sin permiso sobre este recurso.", failureMessage(ApiFailure(403, "forbidden"), signedIn = true))
    }
}
