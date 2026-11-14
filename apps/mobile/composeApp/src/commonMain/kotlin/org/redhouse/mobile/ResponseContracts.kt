package org.redhouse.mobile

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable internal data class ProfileDto(val id:String,val tenant_id:String,val role:String)
@Serializable internal data class TokenDto(val access_token:String,val refresh_token:String,val user:ProfileDto?=null)
@Serializable internal data class DonorPersonalDto(val id:String,val display_name:String,val version:Int)
@Serializable internal data class PublicCampaignDto(val title:String,val starts_at:String,val ends_at:String,val venue:String,val information:String)
@Serializable internal data class PublicCampaignPageDto(val items:List<PublicCampaignDto>,val page:Int,val page_size:Int,val total:Int)
@Serializable internal data class NextAppointmentDto(val id:String,val title:String,val starts_at:String,val ends_at:String,val status:String,val schedule_version:Int)
@Serializable internal data class ShipmentDto(val id:String,val origin_id:String,val destination_id:String,val status:String,val version:Int)
@Serializable internal data class DeviceDto(val id:String,val user_id:String,val tenant_id:String,val source:String,val active:Boolean,val version:Int,val expires_at:String)
@Serializable internal data class ScanDto(val shipment_id:String,val resource_id:String,val origin_id:String,val destination_id:String,val version:Int,val status:String,val verified:Boolean)
@Serializable internal data class SyncDto(val command_id:String,val status:String,val cursor:Long,val shipment_version:Int)
@Serializable internal data class ContactDto(val id:String,val name:String,val value:String,val version:Int)
@Serializable internal data class HandoverDto(val id:String,val name:String)
@Serializable internal data class InstitutionOperationsDto(val id:String,val name:String,val contacts:List<ContactDto>,val operators:List<HandoverDto>)
@Serializable internal data class PlannedRouteDto(val id:String,val reserved_version:Int,val current_version:Int,val changed:Boolean,val distance_km:Double,val travel_minutes:Int,val source:String,val updated_at:String)
@Serializable internal data class OperationalContextDto(val shipment_id:String,val shipment_version:Int,val origin:InstitutionOperationsDto,val destination:InstitutionOperationsDto,val route:PlannedRouteDto,val transport_user_id:String,val consulted_at:String)

/** Reject malformed critical responses before they can update session, custody or synchronization state. */
internal fun validateResponse(service:String,path:String,data:JsonObject) {
    val route=path.substringBefore('?')
    try {
        when {
            service=="identidad" && route in setOf("/api/v1/auth/login","/api/v1/auth/refresh") -> {
                val dto=codec.decodeFromJsonElement<TokenDto>(data);require(dto.access_token.isNotBlank() && dto.refresh_token.isNotBlank())
                if(route.endsWith("login"))require(dto.user!=null)
            }
            service=="identidad" && route=="/api/v1/auth/me" -> {val dto=codec.decodeFromJsonElement<ProfileDto>(data);require(dto.id.isNotBlank() && dto.tenant_id.isNotBlank() && dto.role in setOf("ADMIN","OPERATOR","MEDICAL","COORDINATOR","TRANSPORT","AUDITOR","DONOR"))}
            service=="identidad" && route.startsWith("/api/v1/mobile/devices") -> {val dto=codec.decodeFromJsonElement<DeviceDto>(data);require(dto.version>0 && dto.source in setOf("ANDROID","IOS"))}
            service=="donantes" && route.matches(Regex("/api/v1/donors/[0-9a-f-]{36}/personal")) -> {
                val dto=codec.decodeFromJsonElement<DonorPersonalDto>(data)
                require(dto.id==route.split('/')[4] && dto.display_name.isNotBlank() && dto.version>0)
            }
            service=="donantes" && route=="/api/v1/public/campaign-feed" -> {
                val dto=codec.decodeFromJsonElement<PublicCampaignPageDto>(data)
                require(dto.page>0 && dto.page_size in 1..100 && dto.total>=0 && dto.items.size<=dto.page_size)
                require(dto.items.all { it.title.isNotBlank() && it.starts_at.isNotBlank() && it.ends_at.isNotBlank() })
            }
            service=="donantes" && route=="/api/v1/appointments/next" -> {
                val value=data["appointment"] ?: error("missing appointment")
                if(value !is JsonNull) {
                    val dto=codec.decodeFromJsonElement<NextAppointmentDto>(value)
                    require(dto.id.isNotBlank() && dto.title.isNotBlank() && dto.starts_at.isNotBlank() && dto.ends_at.isNotBlank() && dto.status=="BOOKED" && dto.schedule_version>0)
                }
            }
            service=="transporte" && route.endsWith("/scan") -> {val dto=codec.decodeFromJsonElement<ScanDto>(data);require(dto.version>0 && dto.verified)}
            service=="transporte" && route.endsWith("/operational-context") -> {
                val dto=codec.decodeFromJsonElement<OperationalContextDto>(data)
                require(dto.shipment_version>0 && dto.route.reserved_version>0 && dto.route.current_version>0)
                require(dto.route.changed==(dto.route.reserved_version!=dto.route.current_version))
                require(dto.route.distance_km.isFinite() && dto.route.distance_km>=0 && dto.route.travel_minutes>=0)
            }
            service=="transporte" && route.startsWith("/api/v1/sync/commands") -> {val dto=codec.decodeFromJsonElement<SyncDto>(data);require(dto.status=="RECORDED" && dto.cursor>=0 && dto.shipment_version>0)}
            service=="transporte" && (route.matches(Regex("/api/v1/shipments/[0-9a-f-]{36}")) || route.endsWith("/transitions")) -> {val dto=codec.decodeFromJsonElement<ShipmentDto>(data);require(dto.version>0 && dto.status in setOf("PLANNED","PREPARED","COLLECTED","IN_TRANSIT","DELIVERED","ACCEPTED","INCIDENT","CANCELLED","REJECTED"))}
        }
        data["items"]?.let{value->require(value is JsonArray && value.all{it is JsonObject})}
    } catch(_:Exception){throw ApiFailure(502,"response_contract")}
}
