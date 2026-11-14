package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Synthetic shipment and emulated camera; actual UI and HTTPS file service. */
@RunWith(AndroidJUnit4::class)
class PhotoEvidenceJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun enabled(label:String) {
        revealDestination(compose,label)
        compose.waitUntil(90000) {compose.onAllNodesWithText(label).fetchSemanticsNodes().any {!it.config.contains(SemanticsProperties.Disabled)}}
    }
    private fun shown(label:String) {
        compose.waitUntil(90000) {compose.onAllNodesWithText(label,substring=true).fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()}
    }
    private fun click(label:String)=presentationClick(compose,label)
    private fun fill(label:String,value:String)=compose.onNodeWithText(label).performScrollTo().performTextReplacement(value)

    @Test fun captureUploadAndVerifyThroughTheTask() {
        val lab=readMobileLabFixture()
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.CAMERA")
        enabled("Iniciar sesión");fill("Cuenta","operator1");fill("Contraseña",lab.text("password"));click("Iniciar sesión")
        enabled("Traslados");click("Traslados");enabled("Abrir tarea y mapa")
        compose.onAllNodesWithText("Abrir tarea y mapa")[0].performScrollTo().performClick()
        shown("Traslado · Planificado")
        android.util.Log.i("PhotoJourney","task-loaded")
        Thread.sleep(8000) // Leave time to capture this real screen on the host.
        click("Siguiente paso: Preparar unidad");click("Continuar")
        fill("Observación / motivo (mínimo 6 caracteres)","Evidencia sintética de prueba")
        click("Revisar");click("Evidencia");click("Capturar evidencia")
        val shutter=device.wait(Until.findObject(By.res("com.android.camera2","shutter_button")),30000)
            ?:device.findObject(By.desc("Shutter"))
        assertNotNull("Cámara sin disparador",shutter)
        var done:androidx.test.uiautomator.UiObject2?=null
        repeat(3) {
            if(done==null) {
                device.findObject(By.res("com.android.camera2","shutter_button"))?.click()
                done=device.wait(Until.findObject(By.res("com.android.camera2","done_button")),8000)
                    ?:device.findObject(By.desc("Done"))
            }
        }
        assertNotNull("Cámara no confirmó la fotografía",done);done!!.click()
        compose.waitUntil(90000) {compose.onAllNodesWithContentDescription("Vista previa de evidencia").fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()}
        compose.onNodeWithContentDescription("Vista previa de evidencia").performScrollTo()
        android.util.Log.i("PhotoJourney","photo-preview")
        Thread.sleep(8000)
        // The fixture stores the first PUT, then deliberately returns 503. Retrying
        // the still-visible photo must reuse the key and accept the object's 412.
        click("Cargar y verificar");shown("El servicio no está disponible")
        click("Cargar y verificar");shown("Evidencia · VERIFIED")
        android.util.Log.i("PhotoJourney","photo-verified")
        Thread.sleep(8000)
        assertFalse(java.io.File(InstrumentationRegistry.getInstrumentation().targetContext.cacheDir,"capture").listFiles().orEmpty().any())
        click("Cerrar sesión");enabled("Iniciar sesión")
    }
}
