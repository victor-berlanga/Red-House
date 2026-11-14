package org.redhouse.mobile

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Only display a person when the task, context and projection describe the same assignment. */
fun validatedHandoverPerson(id: String, task: JsonObject, context: JsonObject, projection: JsonObject): JsonObject? {
    val version = task["version"]?.jsonPrimitive?.contentOrNull ?: return null
    if (id.isBlank() || task.text("id") != id || context.text("shipment_id") != id || projection.text("shipment_id") != id ||
        context["shipment_version"]?.jsonPrimitive?.contentOrNull != version ||
        projection["shipment_version"]?.jsonPrimitive?.contentOrNull != version) return null
    val person = projection["transport_user"] as? JsonObject ?: return null
    if (person.text("id").isBlank() || person.text("id") != context.text("transport_user_id") || person.text("name").isBlank()) return null
    return person
}
