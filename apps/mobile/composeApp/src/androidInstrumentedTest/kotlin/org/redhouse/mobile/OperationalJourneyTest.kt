package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

/** Real synthetic controls and samples; no clinical approval, release or calculated eligibility. */
@RunWith(AndroidJUnit4::class)
class OperationalJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private val lab by lazy {codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject}
    private fun shown(text:String){compose.waitUntil(90000){compose.onAllNodesWithText(text,substring=true).fetchSemanticsNodes().isNotEmpty()}}
    private fun click(text:String){revealDestination(compose,text);
        compose.waitUntil(90000){compose.onAllNodesWithText(text).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}
        if(text=="Confirmar")compose.onNodeWithText(text).performClick() else presentationClick(compose,text)
    }
    private fun fill(text:String,value:String){compose.onNodeWithText(text).performScrollTo().performTextReplacement(value)}
    private fun login(user:String){shown("Iniciar sesión");fill("Cuenta",user);fill("Contraseña",lab.text("password"));click("Iniciar sesión")}
    private fun logout(){click("Cerrar sesión");shown("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())}
    @Test fun operatorRecordsManualReadingWithoutReleasingUnit(){
        login("operator1");click("Inventario");shown(lab.text("operational_folio"))
        compose.onAllNodesWithText("Ver detalle")[0].performScrollTo().performClick();shown("Folio: "+lab.text("operational_folio"))
        fill("Referencia de calibración del instrumento","CAL-SINTETICA");fill("Lectura manual en °C","NaN")
        compose.onNodeWithText("Registrar lectura manual").assertIsNotEnabled()
        fill("Lectura manual en °C","4.25");click("Registrar lectura manual");click("Confirmar")
        shown("Lectura registrada. Excursión: false; intervalo: false");shown("Estado: ${displayValue("status","QUARANTINE")}")
        logout()
    }
    @Test fun medicalReadsIncompleteSyntheticSample(){
        login("medical1");click("Muestras autorizadas");shown(lab.text("operational_sample_identifier"))
        compose.onAllNodesWithText("Ver detalle")[0].performScrollTo().performClick();shown("Identificador: "+lab.text("operational_sample_identifier"))
        click("Consultar completitud registrada");shown("Completitud: false · perfil 1 · sintético true · faltantes: ABO")
        compose.onAllNodesWithText("Liberar unidad").assertCountEquals(0);logout()
    }
}
