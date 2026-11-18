package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import kotlin.test.*

class DonorPaginationTest {
    @Test fun pageMismatchDoesNotReplaceConfirmedRows() {
        fun response(page:Int,size:Int)=buildJsonObject {put("page",page);put("page_size",size);put("total",21);put("items",buildJsonArray {add(obj("id" to "first"))})}
        var confirmed=checkedPage(response(1,20),1)
        assertFailsWith<ApiFailure> { confirmed=checkedPage(response(1,20),2) }
        assertEquals(1,confirmed.getValue("page").jsonPrimitive.int)
        assertEquals("first",confirmed.getValue("items").jsonArray.first().jsonObject.text("id"))
        assertFailsWith<ApiFailure> { checkedPage(response(2,100),2) }
    }
    private class Memory : SecureStore {
        var value:String?=null
        override fun read()=value
        override fun write(value:String?) { this.value=value }
    }
    @Test fun failedNextPageKeepsTheConfirmedPage()=runTest {
        val client=HttpClient(MockEngine { request ->
            val path=request.url.encodedPath
            if(path.endsWith("login")) {
                val login=buildJsonObject {put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))}
                respond(buildJsonObject {put("data",login);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            } else if(request.url.parameters["page"]=="2") {
                respond("{\"error\":{\"code\":\"unavailable\",\"message\":\"No disponible\"}}",HttpStatusCode.ServiceUnavailable,headersOf(HttpHeaders.ContentType,"application/json"))
            } else {
                val result=buildJsonObject {put("items",buildJsonArray {add(obj("id" to "first"))});put("page",1);put("page_size",20);put("total",21)}
                respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            }
        })
        val session=Session(Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com")),Memory())
        session.login("u","p","")
        val repository=MobileRepository(session,LocalJournal(Memory()),"ANDROID")
        var confirmed=checkedPage(repository.listPage("donantes","/api/v1/appointments/agenda",1),1)
        try {confirmed=checkedPage(repository.listPage("donantes","/api/v1/appointments/agenda",2),2);fail("Expected failure")}
        catch(_:ApiFailure) { }
        assertEquals(1,confirmed.getValue("page").jsonPrimitive.int)
        assertEquals("first",confirmed.getValue("items").jsonArray.first().jsonObject.text("id"))
    }
    /** Slot row with every field the campaign-slots contract requires since fd4fbcf. */
    private fun slot(id:String)=buildJsonObject {
        put("id",id);put("campaign_id","campaign");put("site_id","site");put("campaign_title","Campaña académica");put("site_name","Sede académica")
        put("starts_at","2026-11-17T18:00:00Z");put("ends_at","2026-11-17T19:00:00Z");put("available",1)
    }
    @Test fun requestedPageAndExistingFilterArePreserved()=runTest {
        val requested=mutableListOf<Int>()
        val client=HttpClient(MockEngine { request ->
            val result=if(request.url.encodedPath.endsWith("login")) buildJsonObject {
                put("access_token","a");put("refresh_token","r");put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
            } else {
                assertEquals("true",request.url.parameters["active"])
                val page=request.url.parameters["page"]!!.toInt();requested.add(page)
                buildJsonObject {put("items",buildJsonArray { for(i in if(page==1) 1..100 else 101..103) add(slot("$i")) });put("total",103);put("page",page);put("page_size",100)}
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val api=Api(client,mapOf("identidad" to "https://example.com","donantes" to "https://example.com"))
        val session=Session(api,Memory());session.login("u","p","")
        val rows=MobileRepository(session,LocalJournal(Memory()),"ANDROID").listPage("donantes","/api/v1/campaign-slots?active=true",2)
        assertEquals(listOf(2),requested);assertEquals(3,rows.getValue("items").jsonArray.size);assertEquals("103",rows.getValue("items").jsonArray.last().jsonObject.text("id"))
    }
    @Test fun publicFeedRequestsOnlyTheSelectedServerPageWithoutCredentials()=runTest {
        val client=HttpClient(MockEngine { request ->
            assertEquals("/api/v1/public/campaign-feed",request.url.encodedPath)
            assertEquals("6",request.url.parameters["page"])
            assertEquals("20",request.url.parameters["page_size"])
            assertEquals("Sede ñ",request.url.parameters["q"])
            assertEquals("2026-11-01T00:00:00Z",request.url.parameters["from_at"])
            assertEquals("2026-12-01T00:00:00Z",request.url.parameters["until_at"])
            assertNull(request.headers[HttpHeaders.Authorization])
            val item=obj("title" to "Campaña", "starts_at" to "2026-11-13T15:00:00Z", "ends_at" to "2026-11-13T16:00:00Z", "venue" to "Sede", "information" to "Datos públicos")
            val result=buildJsonObject {put("items",buildJsonArray {add(item)});put("total",101);put("page",6);put("page_size",20)}
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        val repository=MobileRepository(Session(Api(client,mapOf("donantes" to "https://example.com")),Memory()),LocalJournal(Memory()),"ANDROID")
        val page=repository.publicCampaignPage(6,"Sede ñ","2026-11-01T00:00:00Z","2026-12-01T00:00:00Z")
        assertEquals(1,page.getValue("items").jsonArray.size)
        assertEquals(101,page.getValue("total").jsonPrimitive.int)
    }
    @Test fun withdrawalUsesOnlyTheLatestGrantedPolicy() {
        val granted=buildJsonObject {put("granted",true);put("policy_version","v2")}
        val withdrawn=buildJsonObject {put("granted",false);put("policy_version","v2")}
        assertEquals("v2",withdrawableConsentPolicy(listOf(granted)))
        assertNull(withdrawableConsentPolicy(listOf(withdrawn,granted)))
        assertNull(withdrawableConsentPolicy(emptyList()))
        assertNull(withdrawableConsentPolicy(listOf(buildJsonObject {put("granted",true)})))
    }
    @Test fun shareContainsOnlyPublishedFields() {
        val text=publicCampaignText(obj("title" to "Campaña", "venue" to "Sede", "information" to "Información", "id" to "secret"))
        assertTrue(text.contains("Campaña"));assertTrue(text.contains("Sede"));assertFalse(text.contains("secret"))
    }
}
