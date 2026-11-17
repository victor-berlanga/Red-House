package org.redhouse.mobile

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import io.ktor.http.content.TextContent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.CoroutineStart
import kotlinx.serialization.json.*
import kotlin.test.*

class PreliminaryDonorRegistrationTest {
    private class Memory:SecureStore {
        var value:String?=null
        override fun read()=value
        override fun write(value:String?) {this.value=value}
    }
    private val folio="MOB-012345678901234567890123"
    private fun registered(body:JsonObject,user:String="u")=JsonObject(body+buildJsonObject {
        put("id","00000000-0000-0000-0000-000000000001");put("user_id",user);put("tenant_id","t")
        put("status","PRELIMINARY");put("version",1)
    })
    private fun login()=buildJsonObject {
        put("access_token","synthetic-access");put("refresh_token","synthetic-refresh")
        put("user",obj("id" to "u","tenant_id" to "t","role" to "DONOR"))
    }
    @Test fun unknownGroupAndUncheckedAcknowledgementNeverProduceARegistrationBody() {
        assertFailsWith<IllegalArgumentException>{preliminaryDonorBody("Nombre",null,true,folio)}
        assertFailsWith<IllegalArgumentException>{preliminaryDonorBody("Nombre","UNKNOWN",true,folio)}
        assertFailsWith<IllegalArgumentException>{preliminaryDonorBody("Nombre","O+",false,folio)}
        assertFailsWith<IllegalArgumentException>{preliminaryDonorBody("  ","O+",true,folio)}
        val body=preliminaryDonorBody(" Nombre ","O+",true,folio)
        assertEquals("Nombre",body.text("display_name"));assertEquals(folio,body.text("folio"))
        assertEquals(setOf("folio","display_name","blood_group","consent"),body.keys)
        assertEquals(JsonPrimitive(true),body["consent"])
    }
    @Test fun lostRegistrationOnlyRecoversThePersistedOriginalBodyAndKey()=runTest {
        val storage=Memory();val calls=mutableListOf<Pair<String,String>>()
        val original=preliminaryDonorBody("Nombre","O+",true,folio)
        val client=HttpClient(MockEngine {request->
            val result=if(request.url.encodedPath.endsWith("/login"))login() else {
                val key=request.headers["Idempotency-Key"].orEmpty();val body=(request.body as TextContent).text
                val persisted=LocalJournal(storage).pendingCommands().values.single().jsonObject
                assertEquals(key,persisted.text("id"));assertEquals(original,persisted["body"])
                assertTrue(key.isNotBlank());calls+=key to body
                if(calls.size==1)error("Synthetic lost response")
                registered(original)
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","")
            val first=MobileRepository(session,LocalJournal(storage),"ANDROID")
            assertFails {registerPreliminaryDonor(first,original)}
            val restored=MobileRepository(session,LocalJournal(storage),"ANDROID")
            assertEquals("pending_operation",assertFailsWith<ApiFailure>{registerPreliminaryDonor(restored,preliminaryDonorBody("Otro nombre","A+",true,folio))}.code)
            assertEquals(1,calls.size)
            val pending=restored.journal.pendingCommands().values.single().jsonObject
            assertEquals("PRELIMINARY",restored.recover(pending).text("status"))
            assertEquals(2,calls.size);assertEquals(calls[0],calls[1]);assertTrue(restored.journal.pendingCommands().isEmpty())
        }finally {client.close()}
    }
    @Test fun responseForAnotherOwnerCannotDiscardTheRecoverableCommand()=runTest {
        val storage=Memory();val calls=mutableListOf<Pair<String,String>>()
        val body=preliminaryDonorBody("Nombre","AB-",true,folio)
        val client=HttpClient(MockEngine {request->
            val result=if(request.url.encodedPath.endsWith("/login"))login() else {
                calls+=request.headers["Idempotency-Key"].orEmpty() to (request.body as TextContent).text
                registered(body,if(calls.size==1)"another-user" else "u")
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","")
            val repository=MobileRepository(session,LocalJournal(storage),"IOS")
            assertEquals("response_contract",assertFailsWith<ApiFailure>{registerPreliminaryDonor(repository,body)}.code)
            val pending=LocalJournal(storage).pendingCommands().values.single().jsonObject
            assertEquals("u",repository.recover(pending).text("user_id"))
            assertEquals(calls[0],calls[1]);assertTrue(repository.journal.pendingCommands().isEmpty())
        }finally {client.close()}
    }
    @Test fun aChangedSessionCannotValidateTheResponseAsTheNewOwner()=runTest {
        val storage=Memory();val started=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
        var loginUser="u"
        val body=preliminaryDonorBody("Nombre","O-",true,folio)
        val client=HttpClient(MockEngine {request->
            val result=if(request.url.encodedPath.endsWith("/login"))JsonObject(login()+
                ("user" to obj("id" to loginUser,"tenant_id" to "t","role" to "DONOR"))) else {
                started.complete(Unit);release.await();registered(body,"another-user")
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","")
            val repository=MobileRepository(session,LocalJournal(storage),"IOS")
            val attempted=async {runCatching {registerPreliminaryDonor(repository,body)}}
            started.await();loginUser="another-user";session.login("synthetic-second","synthetic","");release.complete(Unit)
            assertEquals("identity_changed",(attempted.await().exceptionOrNull() as ApiFailure).code)
            assertEquals(body,LocalJournal(storage).pendingCommands().values.single().jsonObject["body"])
        }finally {release.complete(Unit);client.close()}
    }
    @Test fun validOriginalResponseAfterLoginChangeRetainsTheOriginalCommand()=runTest {
        val storage=Memory();val started=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
        var loginUser="u"
        val body=preliminaryDonorBody("Nombre","O-",true,folio)
        val client=HttpClient(MockEngine {request->
            val result=if(request.url.encodedPath.endsWith("/login"))JsonObject(login()+
                ("user" to obj("id" to loginUser,"tenant_id" to "t","role" to "DONOR"))) else {
                started.complete(Unit);release.await();registered(body)
            }
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","")
            val repository=MobileRepository(session,LocalJournal(storage),"ANDROID")
            val attempted=async {runCatching {registerPreliminaryDonor(repository,body)}}
            started.await();val original=LocalJournal(storage).pendingCommands().values.single()
            loginUser="another-user";session.login("synthetic-second","synthetic","");release.complete(Unit)
            assertEquals("identity_changed",(attempted.await().exceptionOrNull() as ApiFailure).code)
            assertEquals(original,LocalJournal(storage).pendingCommands().values.single())
        }finally {release.complete(Unit);client.close()}
    }
    @Test fun lateForbiddenResponseCannotRemoveAReplacementCommand()=runTest {
        val storage=Memory();val started=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
        val body=preliminaryDonorBody("Nombre","B-",true,folio)
        val client=HttpClient(MockEngine {request->
            if(request.url.encodedPath.endsWith("/login"))
                respond(buildJsonObject {put("data",login());put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            else {
                started.complete(Unit);release.await()
                respond("{\"error\":{\"code\":\"forbidden\"}}",HttpStatusCode.Forbidden,headersOf(HttpHeaders.ContentType,"application/json"))
            }
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","")
            val repository=MobileRepository(session,LocalJournal(storage),"ANDROID")
            val attempted=async {runCatching {registerPreliminaryDonor(repository,body)}}
            started.await()
            val name="command:donantes:/api/v1/donors"
            val original=repository.journal.value(name)!!.jsonObject
            val replacement=JsonObject(original+("id" to JsonPrimitive("replacement-command")))
            repository.journal.put(name,replacement);release.complete(Unit)
            assertEquals("identity_changed",(attempted.await().exceptionOrNull() as ApiFailure).code)
            assertEquals(replacement,LocalJournal(storage).value(name))
        }finally {release.complete(Unit);client.close()}
    }
    @Test fun queuedRequestCannotSelectNewLoginIdentityBeforeHttp()=runTest {
        val loginStarted=CompletableDeferred<Unit>();val finishLogin=CompletableDeferred<Unit>()
        var loginCount=0;var registrationHttp=0
        val client=HttpClient(MockEngine {request->
            val result=if(request.url.encodedPath.endsWith("/login")) {
                loginCount++
                if(loginCount==2) {loginStarted.complete(Unit);finishLogin.await()}
                JsonObject(login()+("user" to obj("id" to if(loginCount==1)"u" else "another-user","tenant_id" to "t","role" to "DONOR")))
            }else {registrationHttp++;registered(preliminaryDonorBody("Nombre","O+",true,folio))}
            respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
        })
        try {
            val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
            session.login("synthetic","synthetic","");val expected=session.user!!
            val switching=async(start=CoroutineStart.UNDISPATCHED) {session.login("synthetic-second","synthetic","")}
            loginStarted.await()
            val request=async(start=CoroutineStart.UNDISPATCHED) {runCatching {
                session.request("donantes","/api/v1/donors",HttpMethod.Post,
                    preliminaryDonorBody("Nombre","O+",true,folio),"synthetic-stable-key",expectedIdentity=expected)
            }}
            finishLogin.complete(Unit);switching.await()
            assertEquals("identity_changed",(request.await().exceptionOrNull() as ApiFailure).code)
            assertEquals(0,registrationHttp)
        }finally {finishLogin.complete(Unit);client.close()}
    }
    @Test fun repositoryWaitPreservesOwnerBeforeNewRegistrationAndRecovery()=runTest {
        for(recovering in listOf(false,true)) {
            val storage=Memory();val blocked=CompletableDeferred<Unit>();val release=CompletableDeferred<Unit>()
            var loginUser="u";var registrationHttp=0
            val body=preliminaryDonorBody("Nombre","O+",true,folio)
            val client=HttpClient(MockEngine {request->
                val result=when {
                    request.url.encodedPath.endsWith("/login") -> JsonObject(login()+
                        ("user" to obj("id" to loginUser,"tenant_id" to "t","role" to "DONOR")))
                    request.url.encodedPath.endsWith("/held-operation") -> {blocked.complete(Unit);release.await();obj("ok" to "yes")}
                    else -> {registrationHttp++;registered(body)}
                }
                respond(buildJsonObject {put("data",result);put("meta",JsonObject(emptyMap()))}.toString(),headers=headersOf(HttpHeaders.ContentType,"application/json"))
            })
            try {
                val session=Session(Api(client,mapOf("identidad" to "https://example.test","donantes" to "https://example.test")),Memory())
                session.login("synthetic","synthetic","")
                val repository=MobileRepository(session,LocalJournal(storage),"ANDROID")
                val name="command:donantes:/api/v1/donors"
                val original=buildJsonObject {put("id","original-registration");put("service","donantes");put("path","/api/v1/donors");put("method","POST");put("body",body)}
                if(recovering)repository.journal.put(name,original)
                val holding=async(start=CoroutineStart.UNDISPATCHED) {repository.execute("donantes","/api/v1/held-operation")}
                blocked.await()
                val waiting=async(start=CoroutineStart.UNDISPATCHED) {runCatching {
                    if(recovering)repository.recover(original)else registerPreliminaryDonor(repository,body)
                }}
                loginUser="another-user";session.login("synthetic-second","synthetic","");release.complete(Unit);holding.await()
                assertEquals("identity_changed",(waiting.await().exceptionOrNull() as ApiFailure).code)
                assertEquals(0,registrationHttp)
                if(recovering)assertEquals(original,LocalJournal(storage).value(name))
                else assertNull(LocalJournal(storage).value(name))
            }finally {release.complete(Unit);client.close()}
        }
    }
}
