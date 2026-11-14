package org.redhouse.mobile

import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.jsonObject

/** Synthetic fixture is private to the target app and consumed once per test run. */
internal fun readMobileLabFixture() = InstrumentationRegistry.getInstrumentation().let { instrumentation ->
    val privateFixture=instrumentation.targetContext.filesDir.resolve("redhouse-test-fixture.json")
    val content=if(InstrumentationRegistry.getArguments().getString("fixtureMode")=="asset") {
        instrumentation.context.assets.open("lab.json").bufferedReader().use {it.readText()}
    } else {
        check(privateFixture.isFile) {"Falta el fixture privado del ensayo."}
        try {privateFixture.readText()} finally {check(privateFixture.delete()) {"No se pudo eliminar el fixture privado."}}
    }
    codec.parseToJsonElement(content).jsonObject
}
