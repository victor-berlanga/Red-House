package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import android.graphics.BitmapFactory
import org.osmdroid.config.Configuration
import org.osmdroid.views.MapView
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.overlay.Marker
import java.io.File

actual fun imageBitmap(bytes:ByteArray):ImageBitmap = BitmapFactory.decodeByteArray(bytes,0,bytes.size).asImageBitmap()
actual fun sha256(bytes:ByteArray)=java.security.MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
@Composable actual fun RegionalMap(latitude:Double?,longitude:Double?,label:String) {
    val context=LocalContext.current
    val map=remember {
        Configuration.getInstance().apply {
            userAgentValue="org.redhouse.mobile/0.2.0"
            osmdroidBasePath=File(context.cacheDir,"cartography")
            osmdroidTileCache=File(context.cacheDir,"cartography/tiles")
            expirationExtendedDuration=7*24*60*60*1000L
        }
        MapView(context).apply {setTileSource(TileSourceFactory.MAPNIK);setMultiTouchControls(true);controller.setZoom(7.0);controller.setCenter(GeoPoint(25.6,-99.9))}
    }
    val marker=remember(map) { Marker(map).also { map.overlays.add(it) } }
    DisposableEffect(map) {map.onResume();onDispose {map.onPause();map.onDetach()} }
    Column {
        AndroidView(factory={map},modifier=Modifier.fillMaxWidth().height(280.dp),update={
            it.contentDescription="Mapa de Nuevo León. Última ubicación: ${latitude?:"sin dato"}, ${longitude?:"sin dato"}. Fuente: $label"
            marker.isEnabled=latitude!=null && longitude!=null
            if(latitude!=null && longitude!=null) {marker.position=GeoPoint(latitude,longitude);marker.title=label}
            it.invalidate()
        })
        Text("© OpenStreetMap contributors", style=androidx.compose.material3.MaterialTheme.typography.labelSmall)
    }
}
