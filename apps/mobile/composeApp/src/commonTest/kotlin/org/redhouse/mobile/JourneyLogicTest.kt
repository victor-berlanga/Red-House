package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

private fun shipment(id: String, status: String) = buildJsonObject { put("id", id); put("status", status) }

class JourneyNavigationTest {
    @Test fun donorSeesFiveShortDestinationsStartingAtHome() {
        val destinations = primaryDestinations("DONOR")
        assertEquals(listOf("Inicio", "Citas", "Campañas", "Avisos", "Cuenta"), destinations)
        assertTrue(destinations.size <= 5)
    }
    @Test fun transportSeesOrdersAndHomeWithoutSeparatePendingTab() {
        val destinations = primaryDestinations("TRANSPORT")
        assertEquals(listOf("Inicio", "Traslados", "Avisos", "Cuenta"), destinations)
        assertFalse("Pendientes" in destinations)
    }
    @Test fun otherRolesHaveNoMobileScreensOnlyAccountToSignOut() {
        for (role in listOf("OPERATOR", "COORDINATOR", "MEDICAL", "ADMIN", "AUDITOR")) {
            assertEquals(listOf("Cuenta"), primaryDestinations(role), role)
            assertEquals(listOf("Perfil", "Avisos"), screens(role).map { it.title }, role)
            assertFalse(role in mobileRoles)
        }
        assertEquals(setOf("DONOR", "TRANSPORT"), mobileRoles)
    }
    @Test fun roleScreensKeepTheirServicesAndPaths() {
        assertEquals(listOf("Perfil", "Mi expediente", "Campañas", "Horarios", "Mis citas", "Avisos"), screens("DONOR").map { it.title })
        assertEquals(listOf("Perfil", "Traslados", "Avisos"), screens("TRANSPORT").map { it.title })
        assertEquals("/api/v1/shipments", screens("TRANSPORT")[1].path)
    }
}

class TransportJourneyTest {
    @Test fun primaryActionFollowsOrderStatus() {
        assertEquals("Recolectar", transportStep("PREPARED")?.label)
        assertTrue(transportStep("PREPARED")!!.verifiesUnit)
        assertEquals("Iniciar traslado", transportStep("COLLECTED")?.label)
        assertFalse(transportStep("COLLECTED")!!.verifiesUnit)
        assertEquals("Entregar", transportStep("IN_TRANSIT")?.label)
        assertTrue(transportStep("IN_TRANSIT")!!.verifiesUnit)
        for (status in listOf("PLANNED", "DELIVERED", "ACCEPTED", "CANCELLED", "REJECTED")) assertNull(transportStep(status), status)
    }
    @Test fun stagesAdvanceAndAcceptedCountsAsDelivered() {
        assertEquals(-1, transportStageIndex("PLANNED"))
        assertEquals(0, transportStageIndex("PREPARED"))
        assertEquals(1, transportStageIndex("COLLECTED"))
        assertEquals(2, transportStageIndex("IN_TRANSIT"))
        assertEquals(3, transportStageIndex("DELIVERED"))
        assertEquals(3, transportStageIndex("ACCEPTED"))
        assertEquals(-1, transportStageIndex("CANCELLED"))
    }
    @Test fun activeOrderIsTheOneAlreadyMovingThenTheNextToCollect() {
        val rows = listOf(shipment("a", "PLANNED"), shipment("b", "PREPARED"), shipment("c", "IN_TRANSIT"), shipment("d", "DELIVERED"))
        assertEquals("c", activeShipment(rows)?.text("id"))
        assertEquals(listOf("c", "b", "a", "d"), orderedShipments(rows).map { it.text("id") })
        assertEquals("b", activeShipment(rows.filter { it.text("id") != "c" })?.text("id"))
    }
    @Test fun noActiveOrderWhenOnlyWaitingOrClosed() {
        assertNull(activeShipment(emptyList()))
        assertNull(activeShipment(listOf(shipment("a", "PLANNED"), shipment("b", "DELIVERED"), shipment("c", "CANCELLED"))))
    }
    @Test fun orderingIsStableAmongEqualStatuses() {
        val rows = listOf(shipment("x1", "PREPARED"), shipment("x2", "PREPARED"), shipment("x3", "PREPARED"))
        assertEquals(listOf("x1", "x2", "x3"), orderedShipments(rows).map { it.text("id") })
        assertSame(rows[0], activeShipment(rows))
    }
    @Test fun waitingTextExplainsWhoActsNext() {
        assertEquals("La institución prepara la unidad", transportWaitingText("PLANNED"))
        assertTrue(transportWaitingText("DELIVERED").contains("institución"))
    }
    @Test fun mapsGoToOriginBeforeCollectionAndToDestinationAfter() {
        assertEquals("Banco Norte", mapsPlaceName("PREPARED", "Banco Norte", "Hospital Sur"))
        assertEquals("Hospital Sur", mapsPlaceName("IN_TRANSIT", "Banco Norte", "Hospital Sur"))
        assertEquals("", mapsPlaceName("COLLECTED", "Banco Norte", " "))
    }
    @Test fun systemMapLinksUseCoordinatesOrAnEncodedName() {
        val byName = MapTarget(null, null, "Hospital Sur & Centro")
        assertTrue(geoUri(byName).startsWith("geo:0,0?q="))
        assertFalse(geoUri(byName).contains(" "))
        assertFalse(geoUri(byName).contains("& "))
        assertEquals("https://maps.apple.com/?q=Hospital%20Sur%20%26%20Centro", appleMapsUrl(byName))
        val point = MapTarget(25.6, -100.3)
        assertEquals("geo:25.6,-100.3?q=25.6,-100.3", geoUri(point))
        assertEquals("https://maps.apple.com/?ll=25.6,-100.3", appleMapsUrl(point))
        assertTrue(MapTarget(null, null, " ").isEmpty)
        assertFalse(point.isEmpty)
    }
    @Test fun stateTonesDoNotMixDoneWithAlertOrWaiting() {
        assertEquals(StatusTone.Done, statusTone("DELIVERED"))
        assertEquals(StatusTone.Active, statusTone("IN_TRANSIT"))
        assertEquals(StatusTone.Active, statusTone("BOOKED"))
        assertEquals(StatusTone.Waiting, statusTone("PLANNED"))
        assertEquals(StatusTone.Alert, statusTone("CANCELLED"))
        assertEquals(StatusTone.Alert, statusTone("UNCERTAIN"))
        assertEquals(StatusTone.Neutral, statusTone("FUTURE_STATE"))
    }
}

class DonorJourneyLogicTest {
    private val appointment: JsonObject = buildJsonObject { put("title", "Campaña de otoño"); put("status", "BOOKED") }
    @Test fun withoutRecordTheNextStepIsCompletingThePreliminaryRegistration() {
        val step = donorNextStep(donorLoaded = true, hasRecord = false, nextLoaded = true, next = null, busy = false)
        assertEquals(DonorStepKind.Register, step.kind)
        assertEquals("Registrarme", step.action)
    }
    @Test fun withAnUpcomingAppointmentItIsShown() {
        val step = donorNextStep(true, true, true, appointment, false)
        assertEquals(DonorStepKind.Appointment, step.kind)
        assertEquals("Campaña de otoño", step.title)
        assertEquals("Ver mi cita", step.action)
    }
    @Test fun withRecordAndNoAppointmentItSuggestsBooking() {
        val step = donorNextStep(true, true, true, null, false)
        assertEquals(DonorStepKind.Book, step.kind)
    }
    @Test fun loadingAndFailureAreNotGuessed() {
        assertEquals(DonorStepKind.Loading, donorNextStep(false, false, false, null, busy = true).kind)
        assertEquals(DonorStepKind.Error, donorNextStep(true, true, false, null, busy = false).kind)
        // Si el expediente aún no se pudo consultar, no se afirma que falte el registro.
        assertNotNull(donorNextStep(false, false, true, null, false).also { assertEquals(DonorStepKind.Book, it.kind) })
    }
    @Test fun unreadNoticesIgnoreAcknowledgedAndDismissed() {
        val rows = listOf("OPEN", "PENDING", "ACKNOWLEDGED", "DISMISSED", "").map { buildJsonObject { put("status", it) } }
        assertEquals(3, unreadNotices(rows))
        assertEquals(0, unreadNotices(emptyList()))
    }
}
