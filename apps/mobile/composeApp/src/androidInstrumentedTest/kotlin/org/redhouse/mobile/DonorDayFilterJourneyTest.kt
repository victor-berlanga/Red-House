package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Read-only donor navigation using the current isolated fixture. */
@RunWith(AndroidJUnit4::class)
class DonorDayFilterJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun shown(text:String)=compose.waitUntil(90000) {compose.onAllNodesWithText(text,substring=true).fetchSemanticsNodes().isNotEmpty()}
    private fun capture(stage:String) {compose.waitForIdle();android.util.Log.i("DonorDayVisual",stage);Thread.sleep(12000)}

    @Test fun homeAndInclusiveCalendarFilters() {
        val lab=readMobileLabFixture()
        shown("Iniciar sesión")
        compose.onNodeWithText("Cuenta").performTextReplacement("donor1")
        compose.onNodeWithText("Contraseña").performTextReplacement(lab.text("password"))
        presentationClick(compose,"Iniciar sesión")
        shown("No tienes citas próximas.")
        capture("donor-home")
        presentationClick(compose,"Campañas")
        presentationClick(compose,"Buscar y filtrar campañas")
        shown("Fecha inicial")
        capture("filters-empty")
        presentationClick(compose,"Fecha inicial")
        shown("Elegir fecha")
        capture("filter-calendar")
        presentationClick(compose,"Elegir fecha")
        shown("Desde ·")
        presentationClick(compose,"Fecha final")
        shown("Elegir fecha")
        presentationClick(compose,"Elegir fecha")
        shown("Hasta ·")
        capture("filters-selected")
        presentationClick(compose,"Buscar campañas")
        shown("No encontramos campañas con estos filtros.")
        capture("filters-applied")
        presentationClick(compose,"Cerrar sesión")
    }
}
