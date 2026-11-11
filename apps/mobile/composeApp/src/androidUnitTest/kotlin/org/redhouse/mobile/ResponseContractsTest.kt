package org.redhouse.mobile

import kotlin.test.*
import kotlinx.serialization.json.*

class ResponseContractsTest {
    @Test fun malformedCriticalResponseNeverBecomesAConfirmedShipment(){
        val malformed=obj("id" to newId(),"origin_id" to newId(),"destination_id" to newId(),"status" to "ACCEPTED","version" to "not-a-number")
        assertEquals("response_contract",assertFailsWith<ApiFailure>{validateResponse("transporte","/api/v1/shipments/${newId()}",malformed)}.code)
    }
    @Test fun unacknowledgedSyncAndUnknownPlatformAreRejected(){
        val command=buildJsonObject{put("command_id",newId());put("status","PENDING");put("cursor",1);put("shipment_version",1)}
        assertEquals(502,assertFailsWith<ApiFailure>{validateResponse("transporte","/api/v1/sync/commands/${newId()}",command)}.status)
        val device=buildJsonObject{put("id",newId());put("user_id",newId());put("tenant_id",newId());put("source","UNKNOWN");put("active",true);put("version",1);put("expires_at","2030-01-01T00:00:00Z")}
        assertFailsWith<ApiFailure>{validateResponse("identidad","/api/v1/mobile/devices",device)}
    }
}
