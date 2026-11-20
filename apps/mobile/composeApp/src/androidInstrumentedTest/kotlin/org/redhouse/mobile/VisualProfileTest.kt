package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Runtime-only demo credentials. No business writes, embedded secrets or disabled FLAG_SECURE. */
@RunWith(AndroidJUnit4::class)
class VisualProfileTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun capture(stage:String) {
        compose.waitForIdle()
        android.util.Log.i("VisualQuality",stage)
        Thread.sleep(4000) // Host captures the visible emulator window during this interval.
    }
    private fun fill(label:String,value:String) {
        compose.onNodeWithText(label).performScrollTo()
        compose.waitForIdle()
        compose.onNodeWithText(label).performTextReplacement(value)
    }
    @Test fun authenticatedNavigationAndAccount() {
        val args=InstrumentationRegistry.getArguments()
        org.junit.Assume.assumeTrue("Requires runtime demo credentials",args.containsKey("demoUser") && args.containsKey("demoPassword"))
        val user=requireNotNull(args.getString("demoUser"))
        val password=requireNotNull(args.getString("demoPassword"))
        Thread.sleep(2000) // Let Activity restoration settle before querying its editable nodes.
        val first=requireNotNull(args.getString("firstDestination"))
        compose.waitUntil(60000) {compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes().isNotEmpty()}
        if(compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isEmpty()) presentationClick(compose,"Cerrar sesión")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes().isNotEmpty()}
        fill("Cuenta",user)
        fill("Contraseña",password)
        presentationClick(compose,"Iniciar sesión")
        args.getString("demoOtp")?.let { code ->
            compose.waitUntil(60000) {compose.onAllNodesWithText("Código de verificación").fetchSemanticsNodes().isNotEmpty()}
            compose.onNodeWithText("Código de verificación").assertIsFocused()
            fill("Código de verificación",code);presentationClick(compose,"Iniciar sesión")
        }
        try {compose.waitUntil(60000) {compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty() || (first=="Inicio" && (compose.onAllNodesWithText("Siguiente paso").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Traslado activo").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Sin traslado activo").fetchSemanticsNodes().isNotEmpty()) && compose.onAllNodesWithText("Consultando tus citas…").fetchSemanticsNodes().isEmpty())}}
        catch(error:Exception) {capture("login-or-query-error");throw error}
        compose.onNode(hasText(first) and hasClickAction()).assertIsDisplayed()
        compose.onAllNodesWithText("Secciones").assertCountEquals(0)
        capture("work")
        if(user=="transport1") {
            presentationClick(compose,"Traslados")
            compose.waitUntil(60000) {compose.onAllNodesWithText("Abrir traslado").fetchSemanticsNodes().isNotEmpty()}
            presentationClick(compose,"Abrir traslado")
            compose.waitUntil(60000) {compose.onAllNodesWithText("Contactos y ruta").fetchSemanticsNodes().isNotEmpty()}
            capture("task")
            presentationClick(compose,"Contactos y ruta")
            presentationClick(compose,"Consultar contactos y ruta de esta tarea")
            compose.waitForIdle();Thread.sleep(1500);capture("contacts")
            UiDevice.getInstance(InstrumentationRegistry.getInstrumentation()).pressBack()
        }
        if(user=="donor1") {
            presentationClick(compose,"Citas")
            compose.waitUntil(60000) {compose.onAllNodesWithText("Buscar horarios").fetchSemanticsNodes().isNotEmpty()}
            capture("appointments")
            presentationClick(compose,"Buscar horarios");capture("booking-form")
            UiDevice.getInstance(InstrumentationRegistry.getInstrumentation()).pressBack()
            presentationClick(compose,"Inicio")
            compose.onAllNodes(hasText("Siguiente paso") or hasText("Tu próxima cita")).onFirst().assertExists()
        }
        presentationClick(compose,"Cuenta")
        compose.onNode(hasText("Información de la cuenta") and hasClickAction()).performScrollTo().assertIsDisplayed()
        compose.onAllNodesWithText("Activar notificaciones").assertCountEquals(0)
        capture("account")
        presentationClick(compose,"Privacidad y permisos");capture("privacy")
        UiDevice.getInstance(InstrumentationRegistry.getInstrumentation()).pressBack()
        compose.onNode(hasText("Información de la cuenta") and hasClickAction()).assertExists()
        presentationClick(compose,"Avisos")
        compose.waitUntil(60000) {compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty()}
        compose.onAllNodesWithText("Programar traslado").assertCountEquals(0)
        capture("notices")
        presentationClick(compose,"Cerrar sesión")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty()}
        org.junit.Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
