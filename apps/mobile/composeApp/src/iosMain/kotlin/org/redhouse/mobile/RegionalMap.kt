@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlin.ExperimentalUnsignedTypes::class, androidx.compose.ui.ExperimentalComposeUiApi::class)
package org.redhouse.mobile

import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.toComposeImageBitmap
import androidx.compose.ui.viewinterop.UIKitView
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import kotlinx.cinterop.*
import platform.CoreLocation.CLLocationCoordinate2DMake
import platform.MapKit.*
import platform.CoreCrypto.CC_SHA256
import platform.CoreCrypto.CC_SHA256_DIGEST_LENGTH
import platform.UIKit.accessibilityLabel

actual fun imageBitmap(bytes:ByteArray):ImageBitmap=org.jetbrains.skia.Image.makeFromEncoded(bytes).toComposeImageBitmap()
actual fun sha256(bytes:ByteArray):String {
    val result=UByteArray(CC_SHA256_DIGEST_LENGTH.toInt())
    bytes.usePinned {input->result.usePinned {output->CC_SHA256(if(bytes.isEmpty())null else input.addressOf(0),bytes.size.toUInt(),output.addressOf(0))}}
    return result.joinToString(""){it.toString(16).padStart(2,'0')}
}
@Composable actual fun RegionalMap(latitude:Double?,longitude:Double?,label:String) {
    UIKitView(factory={MKMapView().apply {
        setRegion(MKCoordinateRegionMake(CLLocationCoordinate2DMake(25.6,-99.9),MKCoordinateSpanMake(4.0,4.0)),false)
        showsUserLocation=false
    }},modifier=Modifier.fillMaxWidth().height(300.dp),properties=UIKitInteropProperties(isNativeAccessibilityEnabled=true),update={map->
        map.accessibilityLabel="Mapa de Nuevo León. Última ubicación: ${latitude?:"sin dato"}, ${longitude?:"sin dato"}. Fuente: $label"
        map.removeAnnotations(map.annotations)
        if(latitude!=null && longitude!=null)map.addAnnotation(MKPointAnnotation().apply {
            setCoordinate(CLLocationCoordinate2DMake(latitude,longitude));setTitle(label)
        })
    })
    Text("Cartografía Apple Maps · Nuevo León. Sin red puede faltar cartografía; el marcador procede de Transporte.")
}
