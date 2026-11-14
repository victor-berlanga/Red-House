@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlin.ExperimentalUnsignedTypes::class, androidx.compose.ui.ExperimentalComposeUiApi::class)
package org.redhouse.mobile

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.toComposeImageBitmap
import androidx.compose.ui.viewinterop.UIKitView
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import kotlinx.cinterop.*
import platform.CoreLocation.CLLocationCoordinate2DMake
import platform.CoreGraphics.CGRectMake
import platform.MapKit.*
import platform.CoreCrypto.CC_SHA256
import platform.CoreCrypto.CC_SHA256_DIGEST_LENGTH
import platform.Foundation.NSSelectorFromString
import platform.UIKit.*

private class CenterMapButton:UIButton(frame=CGRectMake(8.0,8.0,48.0,48.0)) {
    var latitude:Double?=null
    var longitude:Double?=null
    init {
        setTitle("◎",forState=UIControlStateNormal)
        titleLabel?.font=UIFont.systemFontOfSize(22.0)
        backgroundColor=UIColor(red=1.0,green=1.0,blue=1.0,alpha=1.0)
        layer.cornerRadius=8.0
        accessibilityLabel="Centrar última ubicación"
        addTarget(this,action=NSSelectorFromString("centerLastLocation"),forControlEvents=UIControlEventTouchUpInside)
    }
    @ObjCAction fun centerLastLocation() {
        val lat=latitude;val lon=longitude
        if(lat!=null && lon!=null) (superview as? MKMapView)?.setCenterCoordinate(CLLocationCoordinate2DMake(lat,lon),animated=true)
    }
}

actual fun imageBitmap(bytes:ByteArray):ImageBitmap=org.jetbrains.skia.Image.makeFromEncoded(bytes).toComposeImageBitmap()
actual fun sha256(bytes:ByteArray):String {
    val result=UByteArray(CC_SHA256_DIGEST_LENGTH.toInt())
    bytes.usePinned {input->result.usePinned {output->CC_SHA256(if(bytes.isEmpty())null else input.addressOf(0),bytes.size.toUInt(),output.addressOf(0))}}
    return result.joinToString(""){it.toString(16).padStart(2,'0')}
}
@Composable actual fun RegionalMap(latitude:Double?,longitude:Double?,label:String,height:Dp) {
    val map=remember {MKMapView().apply {
        setRegion(MKCoordinateRegionMake(CLLocationCoordinate2DMake(25.6,-99.9),MKCoordinateSpanMake(4.0,4.0)),false)
        showsUserLocation=false
    }}
    val button=remember(map) {CenterMapButton().also {map.addSubview(it)}}
    val centered=remember(map) {object {var firstFix=false}}
    val primary=MaterialTheme.colorScheme.primary
    UIKitView(factory={map},modifier=Modifier.fillMaxWidth().height(height),properties=UIKitInteropProperties(isNativeAccessibilityEnabled=true),update={map->
        map.accessibilityLabel=if(latitude==null || longitude==null) "Mapa del traslado sin ubicación confirmada." else "Mapa del traslado. $label: $latitude, $longitude."
        button.latitude=latitude;button.longitude=longitude;button.hidden=latitude==null || longitude==null
        button.setTitleColor(UIColor(red=primary.red.toDouble(),green=primary.green.toDouble(),blue=primary.blue.toDouble(),alpha=primary.alpha.toDouble()),forState=UIControlStateNormal)
        map.bringSubviewToFront(button)
        map.removeAnnotations(map.annotations)
        if(latitude!=null && longitude!=null)map.addAnnotation(MKPointAnnotation().apply {
            setCoordinate(CLLocationCoordinate2DMake(latitude,longitude));setTitle(label)
        })
        if(latitude!=null && longitude!=null && !centered.firstFix) {
            map.setRegion(MKCoordinateRegionMake(CLLocationCoordinate2DMake(latitude,longitude),MKCoordinateSpanMake(0.08,0.08)),false);centered.firstFix=true
        }
    })
    Text("Cartografía Apple Maps", style=androidx.compose.material3.MaterialTheme.typography.labelSmall)
}
