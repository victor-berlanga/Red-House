package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class FormAndRecreationTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun shown(label:String){compose.waitUntil(90000){compose.onAllNodesWithText(label,substring=true).fetchSemanticsNodes().isNotEmpty()}}
    private fun click(label:String){revealDestination(compose,label);compose.waitUntil(90000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}};presentationClick(compose,label)}
    private fun fill(label:String,value:String){compose.onNodeWithText(label).performScrollTo().performTextReplacement(value)}
    @Test fun rotationRestoresAuthorizedSessionWithLargeText(){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        shown("Iniciar sesión");fill("Cuenta","transport1");fill("Contraseña",lab.text("password"));click("Iniciar sesión")
        shown("Traslados")
        Assert.assertTrue("Run with font_scale 1.3 or larger",compose.activity.resources.configuration.fontScale>=1.3f)
        for((requested,expected) in listOf(
            android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE to android.content.res.Configuration.ORIENTATION_LANDSCAPE,
            android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT to android.content.res.Configuration.ORIENTATION_PORTRAIT)){
            compose.activityRule.scenario.onActivity{it.requestedOrientation=requested}
            compose.waitUntil(90000){compose.activity.resources.configuration.orientation==expected && compose.onAllNodesWithText("Traslados").fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()}
            compose.onAllNodesWithText("Mi expediente").assertCountEquals(0)
            click("Avisos");compose.waitUntil(90000){compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty()}
        }
        click("Cerrar sesión");shown("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
    @Test fun transportActivityRecreationReauthorizesTheSameRole(){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        shown("Iniciar sesión");fill("Cuenta","transport1");fill("Contraseña",lab.text("password"));click("Iniciar sesión")
        shown("Traslados")
        compose.onAllNodesWithText("Código de verificación").assertCountEquals(0)
        // Real Activity destruction reconstructs Compose and reloads encrypted credentials via /auth/me.
        compose.activityRule.scenario.recreate();shown("Traslados")
        compose.onAllNodesWithText("Mi expediente").assertCountEquals(0)
        click("Avisos");compose.waitUntil(90000){compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty()}
        click("Cerrar sesión");shown("Iniciar sesión");Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
