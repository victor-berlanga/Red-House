package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.http.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

/** Huecos H1 (evaluaciones humanas) y H2 (consentimiento firmado) del donante. */
class DonorDocumentsTest {
    private val donorId = "11111111-1111-4111-8111-111111111111"
    private val docId = "22222222-2222-4222-8222-222222222222"

    private fun review(id: String, decision: String, at: String, reason: String = "Nota visible") =
        buildJsonObject { put("id", id); put("decision", decision); put("reason", reason); put("actor_id", "x"); put("created_at", at) }

    @Test fun reviewsAreParsedNewestFirstWithoutReviewer() {
        val donor = buildJsonObject { put("reviews", buildJsonArray {
            add(review("a", "DEFERRED", "2026-11-01T10:00:00Z", "Aplazado por hemoglobina"))
            add(review("b", "ELIGIBLE", "2026-11-10T10:00:00+00:00"))
            add(buildJsonObject { put("id", "sin-decision") })
        }) }
        val rows = parseDonorReviews(donor)!!
        assertEquals(listOf("b", "a"), rows.map { it.id })
        assertEquals("Aplazado por hemoglobina", rows.last().note)
        assertEquals("Elegible para donar", displayValue("status", rows.first().decision))
    }

    @Test fun reviewsStatesLoadingErrorEmptyAndLoaded() {
        assertEquals(ReviewsUi.Loading, reviewsUi(true, null, null))
        assertEquals(ReviewsUi.Error("fallo"), reviewsUi(false, "fallo", null))
        assertTrue(reviewsUi(false, null, null) is ReviewsUi.Error) // fuera de contrato no es «vacío»
        assertNull(parseDonorReviews(buildJsonObject { put("reviews", "no es lista") }))
        assertEquals(ReviewsUi.Empty, reviewsUi(false, null, parseDonorReviews(buildJsonObject { put("reviews", buildJsonArray {}) })))
        assertTrue(reviewsUi(false, null, listOf(DonorReview("a", "ELIGIBLE", "", ""))) is ReviewsUi.Loaded)
    }

    private fun status(file: String, analysis: String) = buildJsonObject { put("file_status", file); put("analysis", analysis) }
    private val meta = buildJsonObject { put("id", docId); put("version", 2); put("created_at", "2026-11-15T10:00:00Z") }

    @Test fun consentStatusMapping() {
        fun state(file: String, analysis: String) = consentDocFromStatus(meta, status(file, analysis)).status
        assertEquals(ConsentDocStatus.Verified, state("VERIFIED", "CLEAN"))
        assertEquals(ConsentDocStatus.InReview, state("PENDING", "PENDING"))
        assertEquals(ConsentDocStatus.InReview, state("VERIFIED", "PENDING"))
        assertEquals(ConsentDocStatus.Rejected, state("REJECTED", "PENDING"))
        assertEquals(ConsentDocStatus.Rejected, state("PENDING", "INFECTED"))
        assertEquals(ConsentDocStatus.Failed, state("ERROR", "ERROR"))
        assertEquals(ConsentDocStatus.Failed, state("MISSING", "PENDING"))
        assertEquals(ConsentDocStatus.Unknown, state("RARO", "PENDING"))
        assertEquals(2, consentDocFromStatus(meta, status("VERIFIED", "CLEAN")).version)
    }

    @Test fun latestDocumentIsHighestConsentVersion() {
        fun item(id: String, version: Int, category: String = "CONSENT") = buildJsonObject { put("id", id); put("version", version); put("category", category); put("subject_kind", "DONOR") }
        assertEquals("v3", latestConsentDocument(listOf(item("v1", 1), item("v3", 3), item("v2", 2), item("x", 9, "LAB_RESULT")))!!.text("id"))
        assertNull(latestConsentDocument(emptyList()))
    }

    @Test fun consentStepAppearsOnlyWhenItIsMissingAndNothingMoreUrgentExists() {
        val book = DonorStep(DonorStepKind.Book, "Aún no tienes cita", "Buscar horarios")
        val appointment = DonorStep(DonorStepKind.Appointment, "Cita", "Ver mi cita")
        val register = DonorStep(DonorStepKind.Register, "Registro", "Registrarme")
        val missing = ConsentDoc(ConsentDocStatus.Missing)
        assertEquals(DonorStepKind.Consent, donorNextStepWithConsent(book, true, missing).kind)
        assertEquals(DonorStepKind.Consent, donorNextStepWithConsent(book, true, ConsentDoc(ConsentDocStatus.Rejected)).kind)
        assertEquals(DonorStepKind.Consent, donorNextStepWithConsent(book, true, ConsentDoc(ConsentDocStatus.Failed)).kind)
        for (ok in listOf(ConsentDocStatus.Verified, ConsentDocStatus.InReview, ConsentDocStatus.Unknown))
            assertEquals(DonorStepKind.Book, donorNextStepWithConsent(book, true, ConsentDoc(ok)).kind)
        assertEquals(DonorStepKind.Book, donorNextStepWithConsent(book, false, missing).kind)
        assertEquals(DonorStepKind.Register, donorNextStepWithConsent(register, false, missing).kind)
        assertEquals(DonorStepKind.Appointment, donorNextStepWithConsent(appointment, true, missing).kind)
        assertEquals("Falta tu consentimiento firmado", consentReminder(appointment, true, missing))
        assertEquals("Vuelve a cargar tu consentimiento", consentReminder(appointment, true, ConsentDoc(ConsentDocStatus.Rejected)))
        assertNull(consentReminder(book, true, missing))
        assertNull(consentReminder(appointment, true, ConsentDoc(ConsentDocStatus.Verified)))
    }

    @Test fun progressAndErrorsAreReadable() {
        assertEquals("Paso 2 de 3 · Subiendo archivo… 42 %", consentProgressText(ConsentUploadStage.Uploading, 0.42f))
        assertEquals("Paso 1 de 3 · Preparando carga…", consentProgressText(ConsentUploadStage.Preparing, null))
        assertTrue(consentUploadError(ApiFailure(422, "file_validation")).contains("JPEG"))
        assertTrue(consentUploadError(ApiFailure(412, "stale_version")).contains("Actualiza"))
        assertTrue(consentUploadError(IllegalStateException()).contains("no se duplicará"))
    }

    private class Memory : SecureStore {
        var value: String? = null
        override fun read() = value
        override fun write(value: String?) { this.value = value }
    }

    private fun json(data: JsonObject, status: HttpStatusCode = HttpStatusCode.OK) =
        buildJsonObject { put("data", data); put("meta", JsonObject(emptyMap())) }.toString() to status

    @Test fun uploadPreparesPutsVerifiesAndReleasesKey()=runTest {
        val prepares = mutableListOf<String>(); val verifies = mutableListOf<String>(); var bodies = mutableListOf<JsonObject>()
        var puts = 0; var verifyFailures = 1
        val client = HttpClient(MockEngine { request ->
            val path = request.url.encodedPath
            val headers = headersOf(HttpHeaders.ContentType, "application/json")
            when {
                path.startsWith("/storage/") -> { puts++; respond("", if (puts == 1) HttpStatusCode.Created else HttpStatusCode.PreconditionFailed) }
                path.endsWith("/login") -> respond(json(buildJsonObject { put("access_token", "a"); put("refresh_token", "r"); put("user", obj("id" to "u", "tenant_id" to "t", "role" to "DONOR")) }).first, headers = headers)
                path.endsWith("/documents") -> {
                    prepares += request.headers["Idempotency-Key"].orEmpty()
                    bodies += codec.parseToJsonElement((request.body as io.ktor.http.content.TextContent).text).jsonObject
                    respond(json(buildJsonObject { put("id", docId); put("upload_url", "https://example.com/storage/v1/objects/cap"); put("upload_headers", obj("Content-Type" to "image/jpeg")) }).first, HttpStatusCode.Created, headers)
                }
                path.endsWith("/verify") -> {
                    verifies += request.headers["Idempotency-Key"].orEmpty()
                    if (verifyFailures-- > 0) respond("{\"error\":{\"code\":\"storage_unavailable\"}}", HttpStatusCode.ServiceUnavailable, headers)
                    else respond(json(obj("id" to docId, "status" to "VERIFIED")).first, headers = headers)
                }
                else -> error("inesperada: $path")
            }
        })
        val session = Session(Api(client, mapOf("identidad" to "https://example.com", "documentos" to "https://example.com")), Memory())
        session.login("donor1", "p", "")
        val store = Memory(); val photo = byteArrayOf(1, 2, 3)
        val stages = mutableListOf<ConsentUploadStage>()
        assertFailsWith<ApiFailure> { MobileRepository(session, LocalJournal(store), "ANDROID").uploadConsentDocument(donorId, photo, "33333333-3333-4333-8333-333333333333") { s, _ -> stages += s } }
        val ok = MobileRepository(session, LocalJournal(store), "ANDROID").uploadConsentDocument(donorId, photo, docId) // el documento vigente ya cambió, pero el reintento conserva el cuerpo original
        assertEquals("VERIFIED", ok.text("status"))
        assertEquals(1, prepares.distinct().size) // misma clave tras perder la respuesta: no duplica el documento
        assertEquals(listOf(prepares.first() + "-verify", prepares.first() + "-verify"), verifies)
        assertEquals("DONOR", bodies.first().text("subject_kind")); assertEquals("CONSENT", bodies.first().text("category"))
        assertEquals(donorId, bodies.first().text("subject_id")); assertEquals("image/jpeg", bodies.first().text("mime_type"))
        assertTrue(bodies.first().text("policy_reference").isNotBlank())
        assertEquals("33333333-3333-4333-8333-333333333333", bodies.first().text("supersedes"))
        assertEquals(bodies.first(), bodies.first().let { bodies[1] }) // mismo cuerpo exacto: el servidor no responde 409 por huella distinta
        assertEquals(listOf(ConsentUploadStage.Preparing, ConsentUploadStage.Uploading, ConsentUploadStage.Verifying), stages.distinct())
        // Éxito: la clave se liberó; una carga posterior del mismo archivo es un documento nuevo.
        verifyFailures = 0
        MobileRepository(session, LocalJournal(store), "ANDROID").uploadConsentDocument(donorId, photo)
        assertEquals(2, prepares.distinct().size)
        client.close()
    }

    @Test fun invalidInputsNeverReachTheServer()=runTest {
        val client = HttpClient(MockEngine { error("no debe haber red") })
        val session = Session(Api(client, mapOf("documentos" to "https://example.com")), Memory())
        val repo = MobileRepository(session, LocalJournal(Memory()), "ANDROID")
        assertFailsWith<IllegalArgumentException> { repo.uploadConsentDocument(donorId, ByteArray(0)) }
        assertFailsWith<IllegalArgumentException> { repo.uploadConsentDocument(donorId, ByteArray(CONSENT_MAX_BYTES + 1)) }
        assertFailsWith<IllegalArgumentException> { repo.uploadConsentDocument("../x", byteArrayOf(1)) }
        assertFailsWith<IllegalArgumentException> { repo.loadDonorReviews("../x") }
        client.close()
    }
}
