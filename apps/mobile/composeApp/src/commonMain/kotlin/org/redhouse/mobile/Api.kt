package org.redhouse.mobile

import io.ktor.client.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.client.plugins.*
import io.ktor.http.*
import kotlinx.serialization.json.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

val codec = Json { ignoreUnknownKeys = true }
fun JsonObject.text(key: String) = this[key]?.jsonPrimitive?.contentOrNull.orEmpty()
fun obj(vararg pairs: Pair<String, String>) = buildJsonObject { pairs.forEach { put(it.first, it.second) } }
interface SecureStore {
    fun read(): String?
    /** Replace the complete encrypted record atomically. Null destroys local credentials. */
    fun write(value: String?)
}
class ApiFailure(val status: Int, val code: String) : Exception(when (status) {
    401 -> "Sesión vencida o revocada. Inicia sesión."
    403 -> "Sin permiso sobre este recurso."
    409 -> "Conflicto: consulta el estado vigente antes de continuar."
    422 -> "Revisa los datos y la versión de la operación."
    429 -> "Límite de solicitudes. Espera antes de reintentar."
    503 -> "Dependencia no disponible."
    else -> "Respuesta no válida del servicio."
})
class Api(val client: HttpClient, val bases: Map<String, String>, private val parsingDispatcher: CoroutineDispatcher = Dispatchers.Default) {
    init { require(bases.isNotEmpty()); bases.values.forEach(::requireHttps) }
    suspend fun call(service: String, path: String, method: HttpMethod = HttpMethod.Get,
                     body: JsonObject? = null, token: String? = null, key: String? = null): JsonObject {
        require(path.startsWith("/api/v1/") && !path.contains(".."))
        val response = client.request(bases.getValue(service).trimEnd('/') + path) {
            this.method = method
            accept(ContentType.Application.Json)
            header("X-Correlation-ID", newId())
            token?.let { bearerAuth(it) }
            key?.let { header("Idempotency-Key", it) }
            if (body != null) { contentType(ContentType.Application.Json); setBody(body.toString()) }
        }
        if (response.contentType()?.withoutParameters() != ContentType.Application.Json) throw ApiFailure(502, "contract")
        val raw = response.bodyAsText()
        if (raw.length > 2_000_000) throw ApiFailure(502, "size")
        return withContext(parsingDispatcher) {
            val value = try { codec.parseToJsonElement(raw).jsonObject } catch (_: Exception) { throw ApiFailure(502, "contract") }
            if (!response.status.isSuccess()) throw ApiFailure(response.status.value, value["error"]?.jsonObject?.text("code").orEmpty())
            if (value["meta"] !is JsonObject || value["data"] !is JsonObject) throw ApiFailure(502, "envelope")
            value.getValue("data").jsonObject.also{validateResponse(service,path,it)}
        }
    }
}
fun requireHttps(value: String) {
    val url = Url(value)
    require(url.protocol == URLProtocol.HTTPS && url.host.isNotBlank() && url.user == null && url.password == null && url.parameters.isEmpty() && url.fragment.isEmpty()) { "Configura una URL HTTPS sin credenciales ni parámetros." }
}
expect fun newId(): String
expect fun platformClient(): HttpClient

/** Serializes rotation and logout. A lost refresh response is never replayed. */
class Session(val api: Api, private val store: SecureStore) {
    companion object { private val processMutex = Mutex() }
    private val mutex = processMutex
    private fun reload(): JsonObject? {
        val latest=store.read()?.let {runCatching {codec.parseToJsonElement(it).jsonObject}.getOrNull()}
        val oldUser=record?.get("user")?.jsonObject
        val nextUser=latest?.get("user")?.jsonObject
        if(oldUser!=null && nextUser!=null && (oldUser.text("id")!=nextUser.text("id") || oldUser.text("tenant_id")!=nextUser.text("tenant_id"))) throw ApiFailure(401,"identity_changed")
        record=latest;return record
    }
    private var record: JsonObject? = store.read()?.let { runCatching { codec.parseToJsonElement(it).jsonObject }.getOrNull() }
    val user: JsonObject? get() = record?.get("user")?.jsonObject
    private fun save(value: JsonObject?) { store.write(value?.toString()); record = value }
    suspend fun login(username: String, password: String, otp: String) = mutex.withLock {
        save(null)
        val result = api.call("identidad", "/api/v1/auth/login", HttpMethod.Post, buildJsonObject {
            put("username", username); put("password", password); if (otp.isNotBlank()) put("otp", otp)
        })
        require(result.text("access_token").isNotBlank() && result.text("refresh_token").isNotBlank())
        require(result["user"] is JsonObject)
        save(result)
    }
    suspend fun request(service: String, path: String, method: HttpMethod = HttpMethod.Get,
                        body: JsonObject? = null, key: String? = null): JsonObject {
        val before = mutex.withLock { reload() ?: throw ApiFailure(401, "session") }
        try { return api.call(service, path, method, body, before.text("access_token"), key) }
        catch (e: ApiFailure) { if (e.status != 401) throw e }
        val after = mutex.withLock {
            val current = reload() ?: throw ApiFailure(401, "session")
            // Account switching must not replay a request under a different identity.
            if (current["user"] != before["user"]) throw ApiFailure(401, "identity_changed")
            if (current.text("access_token") == before.text("access_token")) {
                try {
                    val refreshed = api.call("identidad", "/api/v1/auth/refresh", HttpMethod.Post, obj("refresh_token" to current.text("refresh_token")))
                    require(refreshed.text("access_token").isNotBlank() && refreshed.text("refresh_token").isNotBlank())
                    save(JsonObject(refreshed + ("user" to current.getValue("user"))))
                } catch (e: Exception) { save(null); throw e }
            }
            record ?: throw ApiFailure(401, "session")
        }
        return api.call(service, path, method, body, after.text("access_token"), key)
    }
    suspend fun logout(): Boolean = mutex.withLock {
        val old = reload()
        save(null)
        if (old == null) return@withLock true
        try { api.call("identidad", "/api/v1/auth/revoke", HttpMethod.Post, obj("refresh_token" to old.text("refresh_token"))); true }
        catch (e: CancellationException) { throw e }
        catch (_: Exception) { false }
    }
    suspend fun restore(): JsonObject {
        val result=request("identidad","/api/v1/auth/me")
        val fresh=result.also { if(it.text("id").isBlank() || it.text("role").isBlank() || it.text("tenant_id").isBlank()) throw ApiFailure(502,"profile_contract") }
        mutex.withLock { val current=reload()?:throw ApiFailure(401,"session"); if(current["user"]?.jsonObject?.text("id")!=fresh.text("id") || current["user"]?.jsonObject?.text("tenant_id")!=fresh.text("tenant_id")) throw ApiFailure(401,"identity_changed"); save(JsonObject(current+("user" to fresh))) }
        return fresh
    }
    suspend fun accessToken(): String = mutex.withLock { reload()?.text("access_token") ?: throw ApiFailure(401, "session") }
}
