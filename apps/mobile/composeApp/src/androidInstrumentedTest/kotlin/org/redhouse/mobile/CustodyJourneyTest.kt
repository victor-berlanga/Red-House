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
    private val lab by lazy {codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject}
    private fun enabled(label:String){revealDestination(compose,label);compose.waitUntil(90000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}}
    // The native scanner temporarily replaces the Compose activity; absence of a root
    // while camera frames are decoded is expected, not a failed UI assertion.
    private fun shown(label:String){compose.waitUntil(90000){compose.onAllNodesWithText(label,substring=true).fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()}}
    private fun click(label:String){revealDestination(compose,label);enabled(label);val node=compose.onAllNodes(hasText(label) and hasClickAction())[0];if(label=="Confirmar")node.performClick() else node.performScrollTo().performClick()}
    private fun fill(label:String,value:String){compose.onNodeWithText(label).performScrollTo().performTextReplacement(value)}
    private fun login(user:String){
        enabled("Iniciar sesión");fill("Gateway HTTPS",lab.text("android_gateway"));fill("Cuenta institucional",user);fill("Contraseña",lab.text("password"));click("Iniciar sesión");enabled("Traslados")
        click("Traslados");enabled("Abrir tarea y mapa");compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick();shown("Traslado ${lab.text("shipment_id").take(8)}")
    }
    private fun scan(){
        android.util.Log.i("CustodyJourney","optical_scan_requested")
        click("Escanear unidad");shown("Código verificado por Transporte")
        android.util.Log.i("CustodyJourney","optical_scan_verified")
    }
    private fun step(action:String,state:String,counterpart:String?=null){
        if(counterpart!=null){scan();fill("Sello verificado","SELLO-NATIVO-SINTETICO");click(counterpart)}
        fill("Observación / motivo (mínimo 6 caracteres)","Transferencia sintética comprobada desde Compose")
        click(action);click("Confirmar");shown("Estado: ${displayValue("status",state)}")
        android.util.Log.i("CustodyJourney","state=$state")
    }
    @Test fun opticalScanCollectionDeliveryAcceptanceAndCoordinatorRead(){
        UiDevice.getInstance(InstrumentationRegistry.getInstrumentation()).executeShellCommand("pm grant org.redhouse.mobile android.permission.CAMERA")
        login("transport1");click("Consultar contactos y ruta de esta tarea");shown("Ruta vinculada a la reserva")
        fill("Observación / motivo (mínimo 6 caracteres)","Intento sintético sin escaneo")
        click("Confirmar recolección");click("Confirmar");shown("Escanea y verifica la unidad antes de transferir.");shown("Estado: ${displayValue("status","PREPARED")}")
        step("Confirmar recolección","COLLECTED","Contraparte: operator1")
        step("Iniciar traslado","IN_TRANSIT")
        step("Confirmar entrega física","DELIVERED","Contraparte: operator2")
        click("Cerrar sesión");login("operator2");click("Consultar contactos y ruta de esta tarea");shown("Ruta vinculada a la reserva")
        step("Aceptar recepción logística","ACCEPTED","Seleccionar transportista asignado")
        click("Cerrar sesión");login("coordinator1");shown("Estado: ${displayValue("status","ACCEPTED")}");click("Cerrar sesión")
        enabled("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
