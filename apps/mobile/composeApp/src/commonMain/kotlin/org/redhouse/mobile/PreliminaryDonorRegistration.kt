package org.redhouse.mobile

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

internal val donorBloodGroups=listOf("O-","O+","A-","A+","B-","B+","AB-","AB+")

/** Legacy registration acknowledgement is distinct from versioned documentary consent and medical eligibility. */
internal fun preliminaryDonorBody(name:String,group:String?,acknowledged:Boolean,folio:String):JsonObject {
    require(name.trim().length in 1..200) {"Escribe tu nombre (máximo 200 caracteres)."}
    require(group in donorBloodGroups) {"Selecciona tu grupo sanguíneo solo si lo conoces. Si no, acude a tu institución."}
    require(acknowledged) {"Confirma que deseas registrar tu expediente preliminar."}
    require(folio.length in 6..30 && folio.matches(Regex("[A-Za-z0-9_-]+")))
    return buildJsonObject {put("folio",folio);put("display_name",name.trim());put("blood_group",group);put("consent",true)}
}

@Serializable private data class PreliminaryDonorDto(
    val id:String,val tenant_id:String,val user_id:String,val folio:String,val display_name:String,
    val blood_group:String,val consent:Boolean,val status:String,val version:Int
)

/** Validate ownership and the creation response before the durable command is removed. */
internal fun validatePreliminaryDonorResponse(data:JsonObject,body:JsonObject,user:JsonObject) {
    try {
        val row=codec.decodeFromJsonElement<PreliminaryDonorDto>(data)
        require(row.id.matches(Regex("[0-9a-f-]{36}")) && row.version>0 && row.status=="PRELIMINARY")
        require(row.user_id==user.text("id") && row.tenant_id==user.text("tenant_id") && row.consent)
        require(row.folio==body.text("folio") && row.display_name==body.text("display_name") && row.blood_group==body.text("blood_group"))
    } catch(_:Exception) {throw ApiFailure(502,"response_contract")}
}

/** The repository owns persistence/idempotency; the form never supplies identity or a clinical decision. */
internal suspend fun registerPreliminaryDonor(repository:MobileRepository,body:JsonObject):JsonObject {
    val owner=repository.session.user
    if(owner?.text("role")!="DONOR")throw ApiFailure(401,"identity_changed")
    // Validate the exact draft again at the use-case boundary; never regenerate its folio here.
    require(preliminaryDonorBody(body.text("display_name"),body.text("blood_group"),
        (body["consent"] as? JsonPrimitive)?.booleanOrNull==true,body.text("folio"))==body)
    return repository.execute("donantes","/api/v1/donors",body,expectedIdentity=owner)
}
