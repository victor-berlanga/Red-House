package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

/**
 * Navegación y lecturas reales de los dos perfiles de la app móvil (DONOR y TRANSPORT).
 * Los demás perfiles ya no tienen pantallas en móvil: usan portal o escritorio.
 */
@RunWith(AndroidJUnit4::class)
class ProfileQueriesTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun enabled(label:String){revealDestination(compose,label);compose.waitUntil(60000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}}
    private fun click(label:String){revealDestination(compose,label);enabled(label);presentationClick(compose,label)}
    private fun shownAny(vararg labels:String){compose.waitUntil(60000){labels.any{compose.onAllNodesWithText(it,substring=true).fetchSemanticsNodes().isNotEmpty()}}}
    private fun login(user:String){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        enabled("Iniciar sesión")
        compose.onNodeWithText("Cuenta").performTextInput(user)
        compose.onNodeWithText("Contraseña").performTextInput(lab.text("password"))
        click("Iniciar sesión")
    }
    private fun notices(){
        click("Avisos")
        compose.waitUntil(60000){compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty()}
        compose.onAllNodesWithText("Gestionar citas e historial").assertCountEquals(0)
    }
    @Test fun donorHomeAppointmentsAndNotices(){
        login("donor1")
        shownAny("Siguiente paso","Tu próxima cita")
        compose.onAllNodesWithText("Traslados").assertCountEquals(0)
        click("Citas");shownAny("Mis citas")
        notices()
        click("Cerrar sesión");enabled("Iniciar sesión")
    }
    @Test fun transportHomeOrdersAndNotices(){
        login("transport1")
        shownAny("Traslado activo","Sin traslado activo")
        compose.onAllNodesWithText("Mi expediente").assertCountEquals(0)
        click("Traslados");shownAny("Abrir traslado","No tienes traslados asignados.")
        notices()
        click("Cerrar sesión");enabled("Iniciar sesión")
    }
}
