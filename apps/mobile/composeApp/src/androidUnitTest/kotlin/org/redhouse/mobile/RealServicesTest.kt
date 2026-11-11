package org.redhouse.mobile

import io.ktor.client.*
import io.ktor.client.statement.*
import io.ktor.client.engine.okhttp.*
import io.ktor.client.plugins.websocket.*
import io.ktor.client.plugins.observer.*
import io.ktor.http.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import kotlinx.datetime.Clock
import kotlinx.serialization.json.*
import kotlin.test.*
import org.junit.Assume.assumeTrue
import java.io.File
import java.security.KeyStore
import java.security.cert.CertificateFactory
import javax.net.ssl.*

/** Uses the disposable HTTP/WSS service lab, never MockEngine or production. */
class RealServicesTest {
    private class Store : SecureStore {var data:String?=null;override fun read()=data;override fun write(value:String?){data=value}}
    @Test fun transportJourneyAgainstRealServices()=runBlocking {
        val path=System.getenv("REDHOUSE_MOBILE_LAB")
        assumeTrue("Start tests/real_backend.py and set REDHOUSE_MOBILE_LAB",path!=null)
        val lab=codec.parseToJsonElement(File(path!!).readText()).jsonObject
        val ca=CertificateFactory.getInstance("X.509").generateCertificate(File(lab.text("ca")).inputStream())
        val keys=KeyStore.getInstance(KeyStore.getDefaultType()).apply {load(null);setCertificateEntry("ephemeral-lab",ca)}
        val trust=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply {init(keys)}.trustManagers.single() as X509TrustManager
        val tls=SSLContext.getInstance("TLS").apply {init(null,arrayOf(trust),null)}
        val client=HttpClient(OkHttp){engine{config{sslSocketFactory(tls.socketFactory,trust)}};install(WebSockets);install(ResponseObserver){onResponse{println("${it.request.method.value} ${it.request.url.encodedPath}: ${it.status.value}")}};followRedirects=false}
        val api=Api(client,gatewayBases(lab.text("gateway")))
        fun session()=Session(api,Store())
        val transport=session();transport.login("transport1",lab.text("password"),"")
        assertEquals("TRANSPORT",transport.restore().text("role"))
        val journal=LocalJournal(Store());journal.bind(transport.user!!.text("id"))
        val repository=MobileRepository(transport,journal,"ANDROID")
        val id=lab.text("shipment_id");var row=repository.shipment(id)
        assertEquals("PREPARED",row.text("status"))
        val institutions=transport.request("identidad","/api/v1/institutions?page_size=100")["items"]!!.jsonArray
        assertTrue(institutions.any{it.jsonObject.text("id")==row.text("origin_id")})
        val routes=transport.request("geografia","/api/v1/routes?page_size=100")["items"]!!.jsonArray
        assertTrue(routes.any{it.jsonObject.text("origin_id")==row.text("origin_id") && it.jsonObject.text("source").isNotBlank()})
        val context=transport.request("transporte","/api/v1/shipments/$id/operational-context")
        assertEquals(row.text("origin_id"),context.getValue("origin").jsonObject.text("id"))
        assertEquals(transport.user!!.text("id"),context.text("transport_user_id"))
        assertTrue(context.getValue("origin").jsonObject.getValue("operators").jsonArray.any{it.jsonObject.text("id")==lab.getValue("accounts").jsonObject.text("operator1")})
        repository.device();repository.startTracking(row)
        assertFailsWith<ApiFailure>{repository.scan(id,newId())}.also{assertEquals(409,it.status)}
        assertTrue(repository.scan(id,lab.text("resource_id"))["verified"]!!.jsonPrimitive.boolean)
        val tracking=Tracking(client,transport,api.bases.getValue("transporte"),journal)
        val follower=launch {tracking.follow(id)}
        withTimeout(15000){tracking.state.first{it.connected}}
        val point=buildJsonObject {
            put("event_id",newId());put("shipment_id",id);put("device_id",journal.deviceId());put("source","ANDROID");put("simulated",true)
            put("sequence",journal.sequence());put("captured_at",Clock.System.now().toString());put("fix_valid",true)
            put("latitude",25.6866);put("longitude",-100.3161);put("accuracy_m",12.0)
        }
        tracking.publish(point)
        withTimeout(10000){tracking.state.first{it.position?.text("event_id")==point.text("event_id")}}
        assertNull(journal.value("position:$id"))
        val queueStore=Store();val queue=ObservationQueue(queueStore,transport)
        queue.enqueue(id,journal.deviceId(),row["version"]!!.jsonPrimitive.int,"Observación sintética del cliente Kotlin")
        ObservationQueue(queueStore,transport).synchronize()
        assertEquals("RECORDED",queue.entries().single().text("state"))
        suspend fun transition(state:String,actor:MobileRepository,counterparty:String?=null){
            row=actor.transition(id,buildJsonObject {
                put("state",state);put("version",row.getValue("version"));put("reason","Confirmación sintética del cliente Kotlin");put("human_confirmation",true)
                if(counterparty!=null)put("custody",buildJsonObject{
                    put("scanned_resource_id",lab.text("resource_id"));put("seal","Prueba Kotlin");put("captured_at",Clock.System.now().toString());put("electronic_acceptance",true)
                    put("reported_handover_user_id",lab["accounts"]!!.jsonObject.text(counterparty))
                })
            });assertEquals(state,row.text("status"))
        }
        transition("COLLECTED",repository,"operator1");transition("IN_TRANSIT",repository)
        repository.scan(id,lab.text("resource_id"));transition("DELIVERED",repository,"operator2")
        follower.cancelAndJoin()
        val operator=session();operator.login("operator2",lab.text("password"),"")
        val operatorRepository=MobileRepository(operator,LocalJournal(Store()),"ANDROID")
        operatorRepository.scan(id,lab.text("resource_id"));transition("ACCEPTED",operatorRepository,"transport1")
        operator.request("inventario","/api/v1/resources")
        val coordinator=session();coordinator.login("coordinator1",lab.text("password"),"")
        assertEquals("ACCEPTED",coordinator.request("transporte","/api/v1/shipments/$id").text("status"))
        coordinator.request("alertas","/api/v1/alerts")
        val donor=session();donor.login("donor1",lab.text("password"),"")
        donor.request("donantes","/api/v1/campaigns")
        assertEquals(403,assertFailsWith<ApiFailure>{donor.request("transporte","/api/v1/shipments/$id")}.status)
        assertEquals(403,assertFailsWith<ApiFailure>{transport.request("donantes","/api/v1/donors")}.status)
        repository.revokeDevice()
        assertTrue(transport.logout());assertTrue(operator.logout());assertTrue(coordinator.logout());assertTrue(donor.logout())
        client.close()
    }
    @Test fun donorBookingRescheduleCancelAndScope()=runBlocking {
        val path=System.getenv("REDHOUSE_MOBILE_LAB")
        assumeTrue("Start tests/real_backend.py and set REDHOUSE_MOBILE_LAB",path!=null)
        val lab=codec.parseToJsonElement(File(path!!).readText()).jsonObject
        val ca=CertificateFactory.getInstance("X.509").generateCertificate(File(lab.text("ca")).inputStream())
        val keys=KeyStore.getInstance(KeyStore.getDefaultType()).apply {load(null);setCertificateEntry("ephemeral-lab",ca)}
        val trust=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply {init(keys)}.trustManagers.single() as X509TrustManager
        val tls=SSLContext.getInstance("TLS").apply {init(null,arrayOf(trust),null)}
        val client=HttpClient(OkHttp){engine{config{sslSocketFactory(tls.socketFactory,trust)}};install(WebSockets);install(ResponseObserver){onResponse{println("${it.request.method.value} ${it.request.url.encodedPath}: ${it.status.value}")}};followRedirects=false}
        val api=Api(client,gatewayBases(lab.text("gateway")))
        fun session()=Session(api,Store())

        val admin=session();admin.login("admin1",lab.text("password"),"")
        val operator=session();operator.login("operator1",lab.text("password"),"")
        val donor=session();donor.login("donor1",lab.text("password"),"")
        val repo=MobileRepository(donor,LocalJournal(Store()),"ANDROID")
        donor.request("donantes","/api/v1/public/campaigns")
        val site=admin.request("identidad","/api/v1/catalogues/sites",HttpMethod.Post,obj("name" to "Sede Kotlin ${newId()}","municipality" to "Monterrey","address" to "Dirección sintética"),newId())
        val start=Clock.System.now()+kotlin.time.Duration.parse("2h")
        val end=start+kotlin.time.Duration.parse("4h")
        val campaign=operator.request("donantes","/api/v1/campaigns",HttpMethod.Post,buildJsonObject{put("title","Campaña sintética Kotlin");put("starts_at",start.toString());put("ends_at",end.toString());put("capacity",2)},newId())
        suspend fun slot(offset:Int)=operator.request("donantes","/api/v1/campaign-slots",HttpMethod.Post,buildJsonObject{put("campaign_id",campaign.text("id"));put("site_id",site.text("id"));put("starts_at",(start+kotlin.time.Duration.parse("${offset}h")).toString());put("ends_at",(start+kotlin.time.Duration.parse("${offset+1}h")).toString());put("capacity",1)},newId())
        val first=slot(0);val second=slot(1)
        // The real schema allows one linked record per account. Repeated lab runs reuse it.
        val own=donor.request("donantes","/api/v1/donors")["items"]!!.jsonArray.firstOrNull()?.jsonObject
            ?:repo.execute("donantes","/api/v1/donors",buildJsonObject{put("folio","KT-"+newId().take(20));put("display_name","Donante sintético Kotlin");put("blood_group","O+");put("consent",true)})
        repo.execute("donantes","/api/v1/donors/${own.text("id")}/consents",buildJsonObject{put("version",own.getValue("version"));put("policy_version","PRUEBA-NO-CLINICA");put("reference","Consentimiento sintético de integración");put("effective_at",Clock.System.now().toString());put("granted",true);put("human_confirmation",true);put("reason","Consentimiento sintético para integración real")})
        val appointment=repo.execute("donantes","/api/v1/appointments",obj("donor_id" to own.text("id"),"campaign_id" to campaign.text("id"),"slot_id" to first.text("id")))
        var schedule=donor.request("donantes","/api/v1/appointments/${appointment.text("id")}/schedule")
        assertEquals(first.text("id"),schedule.text("slot_id"))
        schedule=repo.execute("donantes","/api/v1/appointments/${appointment.text("id")}/commands",buildJsonObject{put("action","RESCHEDULE");put("slot_id",second.text("id"));put("version",schedule.getValue("version"));put("human_confirmation",true);put("reason","Cambio sintético desde cliente Kotlin")})
        assertEquals(second.text("id"),schedule.text("slot_id"))
        assertEquals("CANCELLED",repo.execute("donantes","/api/v1/appointments/${appointment.text("id")}/cancel").text("status"))
        val stranger=session();stranger.login("donor2",lab.text("password"),"")
        assertEquals(403,assertFailsWith<ApiFailure>{stranger.request("donantes","/api/v1/donors/${own.text("id")}")}.status)
        assertEquals(403,assertFailsWith<ApiFailure>{donor.request("inventario","/api/v1/resources")}.status)
        assertTrue(donor.logout());assertTrue(operator.logout());assertTrue(admin.logout());assertTrue(stranger.logout());client.close()
    }
}
