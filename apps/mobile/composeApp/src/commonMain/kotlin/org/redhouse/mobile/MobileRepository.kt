package org.redhouse.mobile

import io.ktor.http.*
import io.ktor.client.request.*
import kotlinx.serialization.json.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.datetime.Clock

fun gatewayBases(origin:String)=mapOf("identidad" to "identidad-acceso","donantes" to "donantes","transporte" to "transporte","alertas" to "alertas","inventario" to "inventario","receptores" to "receptores","documentos" to "documentos","custodia" to "custodia","compatibilidad" to "compatibilidad","geografia" to "priorizacion-geografia").mapValues { origin.trimEnd('/')+"/services/"+it.value }

/** Encrypted client journal. Critical writes are retained for explicit recovery, never auto-synchronized. */
class LocalJournal(private val store:SecureStore) {
    private var data:JsonObject=store.read()?.let { runCatching {codec.parseToJsonElement(it).jsonObject}.getOrNull() }?: JsonObject(emptyMap())
    private fun save()=store.write(data.toString())
    fun bind(identity:String) { if(data.text("identity")!=identity) {data=obj("identity" to identity);save()} }
    fun value(name:String)=data[name]
    fun pendingCommands()=data.filterKeys {it.startsWith("command:")}
    fun put(name:String,value:JsonElement) {data=JsonObject(data+(name to value));save()}
    fun remove(name:String) {data=JsonObject(data-name);save()}
    fun clear() {data=JsonObject(emptyMap());store.write(null)}
    fun deviceId():String=data.text("device_id").ifBlank {newId().also {put("device_id",JsonPrimitive(it))}}
    fun sequence():Long {val next=(data["sequence"]?.jsonPrimitive?.longOrNull?:0)+1;put("sequence",JsonPrimitive(next));return next}
}
class MobileRepository(val session:Session,val journal:LocalJournal,val source:String) {
    private val mutation=Mutex()
    suspend fun execute(service:String,path:String,body:JsonObject=JsonObject(emptyMap())):JsonObject=mutation.withLock {
        val name="command:$service:$path"
        val old=journal.value(name)?.jsonObject
        if(old!=null && old["body"]!=body) throw ApiFailure(409,"pending_operation")
        val command=old?:buildJsonObject {put("id",newId());put("service",service);put("path",path);put("body",body);put("captured_at",Clock.System.now().toString())}.also{journal.put(name,it)}
        try {
            val result=session.request(service,path,HttpMethod.Post,command["body"]!!.jsonObject,command.text("id"))
            journal.remove(name);result
        } catch(e:ApiFailure){if(e.status in setOf(400,403,409,422))journal.remove(name);throw e}
    }
    suspend fun recover(command:JsonObject)=execute(command.text("service"),command.text("path"),command["body"]!!.jsonObject)
    suspend fun registerPush(token:String) {
        require(token.length in 10..1000)
        val old=journal.value("push")?.jsonObject
        if(old?.text("token")==token)return
        if(old!=null)session.request("alertas","/api/v1/alert-subscriptions/${old.text("id")}/revoke",HttpMethod.Post,buildJsonObject{put("human_confirmation",true);put("reason","Rotación de registro push del teléfono")},newId())
        val row=execute("alertas","/api/v1/alert-subscriptions",obj("channel" to "PUSH","push_destination" to token))
        journal.put("push",obj("id" to row.text("id"),"token" to token))
    }
    suspend fun revokePush(){
        val old=journal.value("push")?.jsonObject?:return
        session.request("alertas","/api/v1/alert-subscriptions/${old.text("id")}/revoke",HttpMethod.Post,buildJsonObject{put("human_confirmation",true);put("reason","Desactivar avisos del teléfono")},newId())
        journal.remove("push")
    }
    suspend fun device():JsonObject {
        val result=session.request("identidad","/api/v1/mobile/devices",HttpMethod.Post,
            obj("id" to journal.deviceId(),"source" to source,"label" to "Red House $source"),journal.deviceId())
        journal.put("device",result);return result
    }
    suspend fun revokeDevice(){
        val row=journal.value("device")?.jsonObject?:return
        session.request("identidad","/api/v1/mobile/devices/${row.text("id")}/revoke",HttpMethod.Post,buildJsonObject{put("version",row.getValue("version"));put("reason","Cierre de sesión en este teléfono");put("human_confirmation",true)},newId())
    }
    suspend fun shipment(id:String)=session.request("transporte","/api/v1/shipments/$id")
    suspend fun scan(id:String,code:String):JsonObject {
        require(code.matches(Regex("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"))) {"El código debe contener únicamente el UUID de la unidad."}
        return session.request("transporte","/api/v1/shipments/$id/scan",HttpMethod.Post,obj("scanned_resource_id" to code),newId())
    }
    suspend fun startTracking(row:JsonObject):JsonObject {
        device()
        return session.request("transporte","/api/v1/shipments/${row.text("id")}/tracking/mobile-session",HttpMethod.Post,trackingCommand(row),newId())
    }
    suspend fun stopTracking(row:JsonObject)=session.request("transporte","/api/v1/shipments/${row.text("id")}/tracking/mobile-session/stop",HttpMethod.Post,trackingCommand(row),newId())
    private fun trackingCommand(row:JsonObject)=buildJsonObject {put("device_id",journal.deviceId());put("version",row.getValue("version"));put("human_confirmation",true);put("reason","Consentimiento explícito de ubicación durante tarea propia")}
    suspend fun transition(id:String,body:JsonObject):JsonObject=mutation.withLock {
        val name="transition:$id"
        val old=journal.value(name)?.jsonObject
        if(old!=null && old.getValue("body")!=body) throw ApiFailure(409,"pending_operation")
        val command=old?:buildJsonObject {put("id",newId());put("body",body);put("captured_at",Clock.System.now().toString())}.also {journal.put(name,it)}
        try {
            val result=session.request("transporte","/api/v1/shipments/$id/transitions",HttpMethod.Post,command.getValue("body").jsonObject,command.text("id"))
            journal.remove(name);result
        } catch(e:ApiFailure) { if(e.status in setOf(400,403,409,422)) journal.remove(name);throw e }
    }
    suspend fun recoverTransition(id:String):JsonObject {
        val old=journal.value("transition:$id")?.jsonObject?:throw ApiFailure(404,"no_pending")
        return transition(id,old.getValue("body").jsonObject)
    }
    suspend fun uploadPhoto(shipment:String,bytes:ByteArray):JsonObject {
        require(bytes.size in 1..10485760)
        val digest=sha256(bytes)
        val name="photo:$shipment:$digest"
        val key=journal.value(name)?.jsonPrimitive?.content ?:newId().also {journal.put(name,JsonPrimitive(it))}
        val prepared=session.request("documentos","/api/v1/shipments/$shipment/files",HttpMethod.Post,buildJsonObject {
            put("mime_type","image/jpeg");put("size",bytes.size);put("sha256",digest)
        },key)
        val url=Url(prepared.text("upload_url"))
        require(url.protocol==URLProtocol.HTTPS && (url.host=="storage.googleapis.com" || url.host.endsWith(".storage.googleapis.com"))) {"Almacenamiento firmado no autorizado."}
        val result=session.api.client.put(url) {
            prepared["upload_headers"]!!.jsonObject.forEach {(k,v)->header(k,v.jsonPrimitive.content)}
            setBody(bytes)
        }
        // GCS precondition 412 can mean the previous PUT succeeded but its response was lost.
        if(!result.status.isSuccess() && result.status.value!=412) throw ApiFailure(503,"upload")
        val file=prepared.getValue("file").jsonObject
        return session.request("documentos","/api/v1/files/${file.text("id")}/verify",HttpMethod.Post,key=key)
    }
}
