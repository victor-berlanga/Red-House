package org.redhouse.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlinx.datetime.Instant
import kotlinx.serialization.json.*

class TransportSummaryTest {
    private fun parse(text: String) = codec.parseToJsonElement(text).jsonObject

    @Test fun countersGroupStatusesLikeTheJourney() {
        val data = parse("""{"total":9,"statuses":[{"status":"PLANNED","value":2},{"status":"PREPARED","value":1},{"status":"IN_TRANSIT","value":1},
            {"status":"COLLECTED","value":1},{"status":"ACCEPTED","value":2},{"status":"INCIDENT","value":1},{"status":"CANCELLED","value":1}]}""")
        assertEquals(SummaryCounts(pending = 3, inProgress = 3, delivered = 2, closed = 1, total = 9), summaryCounts(data))
    }

    @Test fun emptySummaryIsAllZero() {
        assertEquals(SummaryCounts(0, 0, 0, 0, 0), summaryCounts(parse("""{"total":0,"statuses":[]}""")))
    }

    @Test fun malformedSummaryIsRejectedNotShownAsZero() {
        assertFailsWith<ApiFailure> { summaryCounts(parse("""{"total":1}""")) }
        assertFailsWith<ApiFailure> { summaryCounts(parse("""{"total":1,"statuses":[{"status":"PLANNED","value":"x"}]}""")) }
        assertFailsWith<ApiFailure> { summaryCounts(parse("""{"total":1,"statuses":[{"status":"PLANNED","value":-1}]}""")) }
    }

    @Test fun metricsKeepMissingValuesAndSummarizeDestinations() {
        val data = parse("""{"scope":"Tareas propias","series":[
            {"title":"Traslados por etapa","denominator":3,"unit":"registros","values":[{"label":"PLANNED","value":2},{"label":"ACCEPTED","value":1}]},
            {"title":"Cobertura por destino","denominator":3,"unit":"registros","values":[{"label":"8f1c0000-0000-4000-8000-000000000001","value":2},{"label":"8f1c0000-0000-4000-8000-000000000002","value":1}]},
            {"title":"Recolección a aceptación","denominator":0,"unit":"minutos","values":[{"label":"Media observada","value":null}]}]}""")
        val series = metricSeries(data)
        assertEquals(listOf("Planificado", "Aceptado"), series[0].points.map { it.label })
        assertEquals(listOf(MetricPoint("Destinos distintos", 2.0)), series[1].points)
        assertTrue(series[1].points.none { it.label.contains("8f1c") })
        assertEquals(null, series[2].points.single().value)
        assertEquals("Sin datos", metricValueText(null, "minutos"))
        assertEquals("12.5 minutos", metricValueText(12.5, "minutos"))
        assertEquals("3", metricValueText(3.0, "registros"))
        assertFailsWith<ApiFailure> { metricSeries(parse("""{"scope":"x"}""")) }
    }

    @Test fun reportBodyIsShipmentsCsvWithinTheServerWindow() {
        val body = shipmentReportBody(Instant.parse("2026-11-20T12:00:00Z"))
        assertEquals("SHIPMENTS", body.text("report"))
        assertEquals("CSV", body.text("format"))
        assertEquals("2026-10-21T12:00:00Z", body.text("from_at"))
        assertEquals("2026-12-20T12:00:00Z", body.text("until_at"))
        assertEquals("America/Monterrey", body.text("timezone"))
    }

    @Test fun csvParsingHandlesBomQuotesAndEmbeddedBreaks() {
        val table = parseCsv("﻿a,b\r\n\"x,1\",\"di \"\"hola\"\"\"\r\n\"l1\nl2\",z\r\n")
        assertEquals(listOf(listOf("a", "b"), listOf("x,1", "di \"hola\""), listOf("l1\nl2", "z")), table)
    }

    @Test fun shipmentLinesReadColumnsByNameAndHideMissingMarkers() {
        val csv = "﻿departure_at,eta,id,status\r\n2026-11-20T08:00:00-06:00,Sin dato,11111111-2222-4333-8444-555555555555,PLANNED\r\n"
        val line = shipmentReportLines(csv).single()
        assertEquals("Traslado 11111111", line.title)
        assertEquals("PLANNED", line.status)
        assertEquals("", line.eta)
        assertEquals("2026-11-20T08:00:00-06:00", line.departure)
        assertTrue(shipmentReportLines("sin_resultados\r\nSin dato\r\n").isEmpty())
        assertTrue(shipmentReportLines("").isEmpty())
    }

    @Test fun reportStatusTextIsReadable() {
        assertEquals("Listo", reportStatusText("COMPLETE"))
        assertEquals("En preparación", reportStatusText("PENDING"))
        assertTrue(reportStatusText("RETRYABLE").contains("solicita otro"))
    }
}
