package org.redhouse.mobile

import kotlinx.serialization.json.*
import kotlin.test.*

class OperationalContextTest {
    private fun context(changed:Boolean=false,current:Int=2)=buildJsonObject {
        put("shipment_id","s");put("shipment_version",3);put("transport_user_id","u");put("consulted_at","2026-11-09T12:00:00Z")
        listOf("origin","destination").forEach {key->put(key,buildJsonObject{put("id",key);put("name",key);put("contacts",JsonArray(emptyList()));put("operators",JsonArray(emptyList()))})}
        put("route",buildJsonObject{put("id","r");put("reserved_version",2);put("current_version",current);put("changed",changed);put("distance_km",42.0);put("travel_minutes",60);put("source","SYNTHETIC");put("updated_at","2026-11-09T12:00:00Z")})
    }
    @Test fun malformedNestedContactsAndMisrepresentedRouteAreRejected(){
        validateResponse("transporte","/api/v1/shipments/s/operational-context",context())
        validateResponse("transporte","/api/v1/shipments/s/operational-context",context(true,3))
        assertFailsWith<ApiFailure>{validateResponse("transporte","/api/v1/shipments/s/operational-context",context(false,3))}
        val broken=JsonObject(context()+ ("origin" to obj("id" to "o","name" to "o")))
        assertFailsWith<ApiFailure>{validateResponse("transporte","/api/v1/shipments/s/operational-context",broken)}
    }
}
