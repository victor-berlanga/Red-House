package org.redhouse.mobile

import kotlinx.serialization.json.*
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import io.ktor.http.HttpMethod
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** Only nonclinical observations. No custody, reservation or approval commands enter this queue. */
class ObservationQueue(private val store: SecureStore, private val session: Session) {
    companion object { private val processLock = Mutex(); suspend fun clearStore(store:SecureStore)=processLock.withLock{store.write(null)} }
    private val lock = processLock
    fun entries(): List<JsonObject> = read().filter { it.text("user")==session.user?.text("id") && it.text("tenant")==session.user?.text("tenant_id") }
    private fun read(): List<JsonObject> = store.read()?.let { codec.parseToJsonElement(it).jsonArray.map { row -> row.jsonObject } } ?: emptyList()
    private fun save(rows: List<JsonObject>) { store.write(if (rows.isEmpty()) null else JsonArray(rows).toString()) }
    suspend fun enqueue(shipment: String, device: String, version: Int, reason: String): String = lock.withLock {
        require(reason.length in 6..1000 && version > 0)
        val user = session.user ?: throw ApiFailure(401, "session")
        require(user.text("role") == "TRANSPORT")
        val id = newId()
        val rows = read(); require(rows.size < 100)
        val command = buildJsonObject {
            put("id", id); put("shipment_id", shipment); put("device_id", device)
            put("expected_version", version); put("captured_at", Clock.System.now().toString())
            put("body", obj("command" to "TRANSPORT_OBSERVATION", "reason" to reason))
        }
        save(rows + buildJsonObject { put("user", user.text("id")); put("tenant", user.text("tenant_id")); put("command", command); put("state", "PENDING") })
        id
    }
    suspend fun synchronize(manual: Boolean = false) = lock.withLock {
        val user = session.user ?: throw ApiFailure(401, "session")
        val rows = read().toMutableList()
        for (i in rows.indices) {
            val row = rows[i]; val command = row.getValue("command").jsonObject
            if (row.text("user") != user.text("id") || row.text("tenant") != user.text("tenant_id")) continue
            if (row.text("state") !in setOf("PENDING", "UNCERTAIN", "SENDING")) continue
            val attempts=row["attempts"]?.jsonPrimitive?.intOrNull?:0
            val next=row["next_at"]?.jsonPrimitive?.longOrNull?:0L
            
            val expired = Clock.System.now() - Instant.parse(command.text("captured_at")) > kotlin.time.Duration.parse("24h")
            if(!expired && !manual && (attempts>=5 || Clock.System.now().toEpochMilliseconds()<next)) continue
            var state = "EXPIRED"
            rows[i]=JsonObject(row+("state" to JsonPrimitive("SENDING")));save(rows)
            if (!expired) {
                state = try {
                    val result = try { session.request("transporte", "/api/v1/sync/commands/${command.text("id")}") }
                    catch (e: ApiFailure) {
                        if (e.status != 404) throw e
                        session.request("transporte", "/api/v1/sync/commands", HttpMethod.Post, command, command.text("id"))
                    }
                    if (result.text("status") != "RECORDED" || result.text("command_id") != command.text("id")) throw ApiFailure(502, "sync_contract")
                    "RECORDED"
                } catch (e: ApiFailure) { when (e.status) { 409 -> "CONFLICT"; 403, 422 -> "REJECTED"; else -> "UNCERTAIN" } }
                catch (e: kotlinx.coroutines.CancellationException) { throw e }
                catch (_: Exception) { "UNCERTAIN" }
            }
            rows[i] = JsonObject(row + mapOf("state" to JsonPrimitive(state), "attempts" to JsonPrimitive(attempts+1),
                "next_at" to JsonPrimitive(Clock.System.now().toEpochMilliseconds()+(30_000L shl attempts.coerceAtMost(5))))); save(rows)
        }
    }
    suspend fun dismissCompleted()=lock.withLock {save(read().filter{it.text("state") !in setOf("RECORDED","EXPIRED","REJECTED")})}
    suspend fun clear() = lock.withLock { store.write(null) }
}
