package org.redhouse.mobile

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.TextButton
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.activity.compose.setContent
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.runner.RunWith
import org.junit.Rule
import org.junit.Test
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.TimeZone
import kotlinx.datetime.toInstant
import kotlinx.datetime.toLocalDateTime

@RunWith(AndroidJUnit4::class)
class DateTimeCancelTest {
    @get:Rule val compose = createAndroidComposeRule<DateTimeTestActivity>()

    @Test fun calendarForVisualInspection() {
        org.junit.Assume.assumeTrue(androidx.test.platform.app.InstrumentationRegistry.getArguments().getString("visualCapture")=="true")
        compose.activityRule.scenario.onActivity { activity ->
            activity.setContent {MaterialTheme {DateTimeField("horario", "2026-11-13T15:21:03Z", {})}}
        }
        compose.onNodeWithText("horario ·",substring=true).performClick()
        org.junit.Assert.assertTrue(compose.onAllNodesWithText("noviembre",substring=true,ignoreCase=true).fetchSemanticsNodes().size>=2)
        android.util.Log.i("DateTimeVisual", "calendar-open")
        Thread.sleep(30000) // The instrumentation thread waits while the host captures the live dialog.
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Test fun localeInsideDialogIsSpanish() {
        compose.activityRule.scenario.onActivity { activity ->
            activity.setContent {
                MaterialTheme {
                    DatePickerDialog(onDismissRequest={},confirmButton={TextButton(onClick={}) {Text("Listo")}}) {
                        SpanishPickerEnvironment {Text("Idioma: ${LocalConfiguration.current.locales[0].toLanguageTag()}")}
                    }
                }
            }
        }
        compose.onNodeWithText("Idioma: es-MX").assertExists()
    }

    @Test fun cancellingTimeRestoresSavedValueOnReopen() {
        // Isolated component fixture; this test makes no authentication or business claims.
        compose.activityRule.scenario.onActivity { activity ->
            activity.setContent {
                var value by androidx.compose.runtime.remember { mutableStateOf("2026-11-13T15:21:03.123456789Z") }
                MaterialTheme { Column { DateTimeField("horario", value, { value = it }); Text("Valor: $value") } }
            }
        }
        fun openTime() {
            compose.onNodeWithText("horario ·", substring = true).performClick()
            org.junit.Assert.assertTrue(compose.onAllNodesWithText("noviembre",substring=true,ignoreCase=true).fetchSemanticsNodes().size>=2)
            compose.onNodeWithText("Elegir hora").performClick()
        }
        openTime()
        compose.onNode(hasText("Minuto") and hasSetTextAction()).performTextReplacement("42")
        compose.onNodeWithText("Cancelar").performClick()
        compose.onNodeWithText("Valor: 2026-11-13T15:21:03.123456789Z").assertExists()
        openTime()
        compose.onNode(hasText("21") and hasSetTextAction()).assertExists()
        compose.onNode(hasText("Minuto") and hasSetTextAction()).performTextReplacement("42")
        compose.onNodeWithText("Aceptar").performClick()
        val zone=TimeZone.currentSystemDefault()
        val original=Instant.parse("2026-11-13T15:21:03.123456789Z").toLocalDateTime(zone)
        val expected=LocalDateTime(original.year,original.monthNumber,original.dayOfMonth,original.hour,42,original.second,original.nanosecond).toInstant(zone)
        compose.onNodeWithText("Valor: $expected").assertExists()
    }
}
