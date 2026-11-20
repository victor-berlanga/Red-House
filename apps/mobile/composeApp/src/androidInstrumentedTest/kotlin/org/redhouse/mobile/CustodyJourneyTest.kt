package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

/** Real camera frames, Compose interactions and HTTPS owners; no injected scan result. */
@RunWith(AndroidJUnit4::class)
class CustodyJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private val lab by lazy {readMobileLabFixture()}
    private fun enabled(label:String){revealDestination(compose,label);compose.waitUntil(90000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}}
    // The native scanner temporarily replaces the Compose activity; absence of a root
    // while camera frames are decoded is expected, not a failed UI assertion.
    private fun shown(label:String){compose.waitUntil(90000){compose.onAllNodesWithText(label,substring=true).fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()}}
    private fun click(label:String){presentationClick(compose,label)}
    private fun fill(label:String,value:String){compose.onNodeWithText(label).performScrollTo().performTextReplacement(value)}
    private fun login(user:String){
        enabled("Iniciar sesión");fill("Cuenta",user);fill("Contraseña",lab.text("password"));click("Iniciar sesión");enabled("Traslados")
        click("Traslados");enabled("Abrir traslado");compose.onAllNodesWithText("Abrir traslado")[0].performScrollTo().performClick();shown("Traslado ·")
    }
    private fun scan(){
        android.util.Log.i("CustodyJourney","optical_scan_requested")
        click("Escanear unidad");shown("Código verificado")
        android.util.Log.i("CustodyJourney","optical_scan_verified")
    }
    private fun step(action:String,state:String,counterpart:String?=null){
        if(compose.onAllNodesWithText("Paso 1 de 3").fetchSemanticsNodes().isEmpty()) click("Siguiente paso: $action")
        if(counterpart!=null){scan();fill("Sello verificado","SELLO-NATIVO-SINTETICO")}
        click("Continuar")
        if(counterpart!=null){shown(counterpart);click(counterpart)}
        fill("Observación / motivo (mínimo 6 caracteres)","Transferencia sintética comprobada desde Compose")
        click("Revisar");click(action);click("Confirmar");shown("Traslado · ${displayValue("status",state)}")
        android.util.Log.i("CustodyJourney","state=$state")
    }
    @Test fun opticalScanCollectionAndDelivery(){
        UiDevice.getInstance(InstrumentationRegistry.getInstrumentation()).executeShellCommand("pm grant org.redhouse.mobile android.permission.CAMERA")
        login("transport1");click("Consultar contactos y ruta de esta tarea");shown("Ruta vinculada a la reserva")
        click("Siguiente paso: Confirmar recolección")
        compose.onNodeWithText("Continuar").assertIsNotEnabled()
        step("Confirmar recolección","COLLECTED","operator1")
        step("Iniciar traslado","IN_TRANSIT")
        step("Confirmar entrega física","DELIVERED","operator2")
        // La aceptación en destino (OPERATOR) y la lectura del coordinador ya no se hacen en móvil.
        click("Cerrar sesión")
        enabled("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
