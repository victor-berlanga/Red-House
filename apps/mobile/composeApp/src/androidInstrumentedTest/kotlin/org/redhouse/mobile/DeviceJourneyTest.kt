package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.*
import org.junit.runner.RunWith
import org.junit.Assert.*
import kotlinx.serialization.json.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class DeviceJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun text(value:String)=compose.onNodeWithText(value)
    @Test fun loginNavigationAndNativeLocation() {
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val lab=codec.parseToJsonElement(instrumentation.context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        compose.waitUntil(120000){compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty()}
        text("Cuenta").performTextInput("transport1")
        text("Contraseña").performTextInput(lab.text("password"))
        text("Iniciar sesión").performScrollTo().performClick()
        revealDestination(compose,"Traslados")
        compose.waitUntil(120000){compose.onAllNodesWithText("Traslados").fetchSemanticsNodes().any{!it.config.contains(androidx.compose.ui.semantics.SemanticsProperties.Disabled)}}
        text("Traslados").performScrollTo().performClick()
        compose.waitUntil(120000){compose.onAllNodesWithText("Abrir traslado").fetchSemanticsNodes().isNotEmpty()}
        compose.onAllNodesWithText("Abrir traslado")[0].performScrollTo().performClick()
        compose.waitUntil(120000){compose.onAllNodesWithText("Traslado ·",substring=true).fetchSemanticsNodes().isNotEmpty()}
        val device=UiDevice.getInstance(instrumentation)
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.ACCESS_FINE_LOCATION")
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.ACCESS_COARSE_LOCATION")
        val latch=CountDownLatch(1);var result:PhonePosition?=null;var failure:String?=null
        compose.runOnUiThread{compose.activity.deviceAccess.locate{point,error->result=point;failure=error;latch.countDown()}}
        assertTrue("GPS callback timeout",latch.await(40,TimeUnit.SECONDS))
        assertNotNull("Inject geo fix through adb emu geo fix; $failure",result)
        assertTrue("Emulator must label position simulated",result!!.simulated)
        assertEquals(25.6866,result!!.latitude,0.02)
        presentationClick(compose,"Autorizar ubicación durante esta tarea")
        compose.waitUntil(30000){compose.onAllNodesWithText("Capturar y publicar ubicación").fetchSemanticsNodes().any{!it.config.contains(androidx.compose.ui.semantics.SemanticsProperties.Disabled)}}
        text("Capturar y publicar ubicación").performScrollTo().performClick()
        compose.waitUntil(60000){compose.onAllNodesWithText("Ubicación guardada para este traslado").fetchSemanticsNodes().isNotEmpty()}
        compose.onNodeWithText("SIMULADA / INYECTADA",substring=true).assertExists()
        compose.runOnUiThread {
            fun maps(view:android.view.View):List<org.osmdroid.views.MapView> =
                if(view is org.osmdroid.views.MapView)listOf(view)
                else if(view is android.view.ViewGroup)(0 until view.childCount).flatMap{maps(view.getChildAt(it))}
                else emptyList()
            val markers=maps(compose.activity.window.decorView).flatMap{it.overlays.filterIsInstance<org.osmdroid.views.overlay.Marker>()}
            assertTrue("WSS point must update the native map marker",markers.any{it.isEnabled && kotlin.math.abs(it.position.latitude-25.6866)<0.02 && kotlin.math.abs(it.position.longitude+100.3161)<0.02})
        }
        // Ciphertext is inspectable; credentials and coordinates must not be plain text.
        val stored=codec.parseToJsonElement(AndroidSecureStore(compose.activity).read()!!).jsonObject
        val sensitive=listOf(lab.text("password"),stored.text("access_token"),stored.text("refresh_token"),"25.6866")
        val encrypted=compose.activity.noBackupFilesDir.listFiles().orEmpty().filter{it.extension=="gcm"}
        assertTrue(encrypted.any{it.name=="session.gcm"})
        encrypted.forEach {file->val raw=file.readBytes().toString(Charsets.ISO_8859_1);sensitive.forEach{assertFalse("Sensitive value present in local ciphertext",raw.contains(it))}}
        revealDestination(compose,"Cerrar sesión")
        text("Cerrar sesión").performScrollTo().performClick()
        compose.waitUntil(120000){compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty()}
        assertNull(AndroidSecureStore(compose.activity).read())
    }
}
