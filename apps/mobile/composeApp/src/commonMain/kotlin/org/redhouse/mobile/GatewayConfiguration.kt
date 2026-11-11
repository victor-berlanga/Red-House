package org.redhouse.mobile

/** A session and its pending observations belong to one server environment. */
internal object GatewayConfiguration {
    fun stored(config: SecureStore): String? = config.read()?.takeIf {
        it.isNotBlank() && (MobileEnvironment.editableGateway || it == MobileEnvironment.gateway)
    }

    suspend fun prepare(config: SecureStore, session: SecureStore, journal: SecureStore,
                queue: SecureStore, cancelWork: () -> Unit): String {
        val previous = config.read()
        if (MobileEnvironment.editableGateway) return previous.orEmpty()
        if (previous != MobileEnvironment.gateway) {
            // Do not forward credentials or replay another environment's observations.
            cancelWork()
            session.write(null)
            journal.write(null)
            ObservationQueue.clearStore(queue)
            config.write(MobileEnvironment.gateway)
        }
        return MobileEnvironment.gateway
    }
}
