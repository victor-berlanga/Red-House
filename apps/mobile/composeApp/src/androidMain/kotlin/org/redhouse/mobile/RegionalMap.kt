package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import android.graphics.BitmapFactory
import android.view.ViewOutlineProvider
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.Button
import android.graphics.drawable.GradientDrawable
import androidx.compose.ui.graphics.toArgb
import androidx.compose.material3.MaterialTheme
import org.osmdroid.config.Configuration
import org.osmdroid.views.MapView
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.overlay.Marker
import java.io.File

actual fun imageBitmap(bytes:ByteArray):ImageBitmap = BitmapFactory.decodeByteArray(bytes,0,bytes.size).asImageBitmap()
actual fun sha256(bytes:ByteArray)=java.security.MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
@Composable actual fun RegionalMap(latitude:Double?,longitude:Double?,label:String,height:Dp) {
    val context=LocalContext.current
    val map=remember {
        Configuration.getInstance().apply {
            userAgentValue="org.redhouse.mobile/0.2.0"
            osmdroidBasePath=File(context.cacheDir,"cartography")
            osmdroidTileCache=File(context.cacheDir,"cartography/tiles")
            expirationExtendedDuration=7*24*60*60*1000L
        }
        MapView(context).apply {outlineProvider=ViewOutlineProvider.BOUNDS;clipToOutline=true;setTileSource(TileSourceFactory.MAPNIK);setMultiTouchControls(true);controller.setZoom(7.0);controller.setCenter(GeoPoint(25.6,-99.9))}
    }
    val marker=remember(map) { Marker(map).also {
        it.icon=context.getDrawable(R.drawable.map_location_pin)
        it.setAnchor(Marker.ANCHOR_CENTER,Marker.ANCHOR_BOTTOM)
        map.overlays.add(it)
    } }
    val centered=remember(map) {object {var firstFix=false}}
    val primary=MaterialTheme.colorScheme.primary.toArgb()
    val button=remember(map) {Button(context).apply {
        text="◎";textSize=22f;setAllCaps(false);minWidth=0;minHeight=0;setPadding(0,0,0,0)
        contentDescription="Centrar última ubicación"
        background=GradientDrawable().apply {setColor(android.graphics.Color.WHITE);cornerRadius=8f*context.resources.displayMetrics.density}
        setOnClickListener {if(marker.isEnabled) map.controller.animateTo(marker.position)}
    }}
    val container=remember(map,button) {FrameLayout(context).apply {
        addView(map,FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT,FrameLayout.LayoutParams.MATCH_PARENT))
        val unit=context.resources.displayMetrics.density
        addView(button,FrameLayout.LayoutParams((48*unit).toInt(),(48*unit).toInt(),Gravity.TOP or Gravity.START).apply {setMargins((8*unit).toInt(),(8*unit).toInt(),0,0)})
    }}
    DisposableEffect(map) {map.onResume();onDispose {map.onPause();map.onDetach()} }
    Column {
        AndroidView(factory={container},modifier=Modifier.fillMaxWidth().height(height),update={
            map.contentDescription=if(latitude==null || longitude==null) "Mapa del traslado sin ubicación confirmada." else "Mapa del traslado. $label: $latitude, $longitude."
            marker.isEnabled=latitude!=null && longitude!=null
            button.visibility=if(marker.isEnabled) View.VISIBLE else View.GONE;button.setTextColor(primary)
            if(latitude!=null && longitude!=null) {
                marker.position=GeoPoint(latitude,longitude);marker.title=label
                if(!centered.firstFix) {map.controller.setZoom(12.0);map.controller.setCenter(marker.position);centered.firstFix=true}
            }
            map.invalidate()
        })
        Text("© OpenStreetMap contributors", style=androidx.compose.material3.MaterialTheme.typography.labelSmall)
    }
}
