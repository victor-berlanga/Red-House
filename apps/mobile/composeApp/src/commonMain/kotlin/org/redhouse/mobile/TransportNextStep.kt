package org.redhouse.mobile

internal fun transportAction(role: String, tenant: String, origin: String, destination: String, status: String): String? = when {
    role == "TRANSPORT" && status == "PREPARED" -> "COLLECTED"
    role == "TRANSPORT" && status == "COLLECTED" -> "IN_TRANSIT"
    role == "TRANSPORT" && status == "IN_TRANSIT" -> "DELIVERED"
    role == "OPERATOR" && tenant == origin && status == "PLANNED" -> "PREPARED"
    role == "OPERATOR" && tenant == destination && status == "DELIVERED" -> "ACCEPTED"
    else -> null
}
