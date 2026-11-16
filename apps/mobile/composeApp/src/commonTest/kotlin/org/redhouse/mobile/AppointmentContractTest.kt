package org.redhouse.mobile

import kotlinx.serialization.json.*
import kotlin.test.*

class AppointmentContractTest {
    @Test fun availabilityRequiresCampaignAndSiteLabels() {
        val slot=obj("id" to "slot","campaign_id" to "campaign","site_id" to "site",
            "campaign_title" to "Campaña académica","site_name" to "Sede académica",
            "starts_at" to "2026-11-17T18:00:00Z","ends_at" to "2026-11-17T19:00:00Z")
        fun page(row:JsonObject)=buildJsonObject {
            put("items",JsonArray(listOf(JsonObject(row+("available" to JsonPrimitive(1))))))
            put("page",1);put("page_size",20);put("total",1)
        }
        validateResponse("donantes","/api/v1/campaign-slots?page=1",page(slot))
        for(field in listOf("campaign_title","site_name")) {
            assertEquals("response_contract",assertFailsWith<ApiFailure>{
                validateResponse("donantes","/api/v1/campaign-slots",page(JsonObject(slot-field)))
            }.code)
        }
    }
}
