package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith
import java.time.Instant

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
    @Test fun coordinatorPlansAndCancelsBeforeCollection(){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        shown("Iniciar sesión");fill("Gateway HTTPS",lab.text("android_gateway"));fill("Cuenta institucional","coordinator1");fill("Contraseña",lab.text("password"));click("Iniciar sesión")
        click("Programar traslado")
        fill("Referencia de reserva confirmada",lab.text("planning_reservation_id"))
        fill("Referencia del transportista de origen",lab.getValue("accounts").jsonObject.text("transport1"))
        val now=Instant.now()
        fill("Salida · fecha, hora y zona",now.plusSeconds(300).toString())
        fill("Llegada prevista · fecha, hora y zona",now.plusSeconds(2700).toString())
        fill("Motivo de programación","Programación sintética confirmada desde interfaz nativa")
        click("Revisar programación");click("Confirmar");shown("· PLANNED")
        click("Volver");click("Traslados");shown("Abrir tarea y mapa")
        compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick();shown("Estado: ${displayValue("status","PLANNED")}")
        fill("Motivo de cancelación (mínimo 6 caracteres)","Cancelación sintética previa a recolección")
        click("Cancelar antes de recolección");click("Confirmar");shown("Estado: ${displayValue("status","CANCELLED")}")
        compose.activityRule.scenario.recreate();shown("Traslados")
        click("Traslados");shown("Abrir tarea y mapa");compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick();shown("Estado: ${displayValue("status","CANCELLED")}")
        click("Cerrar sesión");shown("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
