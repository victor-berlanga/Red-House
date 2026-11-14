package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith
import java.time.ZonedDateTime

/** The fixture is a real reserved resource; planning and cancellation occur only through Compose. */
@RunWith(AndroidJUnit4::class)
class PlanningJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun shown(text:String){compose.waitUntil(90000){compose.onAllNodesWithText(text,substring=true).fetchSemanticsNodes().isNotEmpty()}}
    private fun click(text:String){revealDestination(compose,text);
        compose.waitUntil(90000){compose.onAllNodesWithText(text).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}
        if(text=="Confirmar")compose.onNodeWithText(text).performClick() else presentationClick(compose,text)
    }
    private fun fill(text:String,value:String){compose.onNodeWithText(text).performScrollTo().performTextReplacement(value)}
    private fun chooseTime(label:String,value:ZonedDateTime) {
        click("Elegir $label");click("Elegir hora")
        val fields=compose.onAllNodes(isEditable())
        fields[0].performTextReplacement(value.hour.toString().padStart(2,'0'))
        fields[1].performTextReplacement(value.minute.toString().padStart(2,'0'))
        compose.onNodeWithText("Segundos").performTextReplacement("00")
        click("Aceptar")
    }
    @Test fun coordinatorPlansAndCancelsBeforeCollection(){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        shown("Iniciar sesión");fill("Cuenta","coordinator1");fill("Contraseña",lab.text("password"));click("Iniciar sesión")
        click("Programar traslado")
        click("Reserva")
        compose.waitUntil(90000){compose.onAllNodesWithTag("reservation:"+lab.text("planning_reservation_id")).fetchSemanticsNodes().isNotEmpty()}
        compose.onNodeWithTag("reservation:"+lab.text("planning_reservation_id")).performScrollTo().performClick()
        click("Transportista")
        compose.waitUntil(90000){compose.onAllNodesWithTag("transporter:"+lab.getValue("accounts").jsonObject.text("transport1")).fetchSemanticsNodes().isNotEmpty()}
        compose.onNodeWithTag("transporter:"+lab.getValue("accounts").jsonObject.text("transport1")).performScrollTo().performClick()
        val now=ZonedDateTime.now()
        org.junit.Assume.assumeTrue("Fixture requires both times on the current local date",now.hour<23)
        chooseTime("salida",now.plusMinutes(5))
        chooseTime("llegada prevista",now.plusMinutes(45))
        fill("Motivo de programación","Programación sintética confirmada desde interfaz nativa")
        click("Revisar programación");click("Confirmar");shown("Traslado programado")
        click("Volver");click("Traslados");shown("Abrir tarea y mapa")
        compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick();shown("Traslado · ${displayValue("status","PLANNED")}")
        fill("Motivo de cancelación (mínimo 6 caracteres)","Cancelación sintética previa a recolección")
        click("Cancelar antes de recolección");click("Confirmar");shown("Traslado · ${displayValue("status","CANCELLED")}")
        compose.activityRule.scenario.recreate();shown("Traslados")
        click("Traslados");shown("Abrir tarea y mapa");compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick();shown("Traslado · ${displayValue("status","CANCELLED")}")
        click("Cerrar sesión");shown("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
