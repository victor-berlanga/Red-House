package org.redhouse.mobile

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Resolve ownership only after authentication succeeds; no pending data is touched on failure. */
internal suspend fun authenticateAndBindOwner(
    gateway:String,journal:LocalJournal,queueStore:SecureStore,authenticate:suspend ()->JsonObject
):JsonObject {
    val user=authenticate()
    val userId=user.text("id");val tenantId=user.text("tenant_id")
    require(userId.isNotBlank() && tenantId.isNotBlank()) {"No se confirmó la identidad autenticada."}
    val identity="$gateway:$userId:$tenantId"
    if(journal.value("identity")?.jsonPrimitive?.content!=identity) {
        ObservationQueue.clearStore(queueStore)
        journal.bind(identity)
    }
    return user
}
