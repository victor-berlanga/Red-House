package org.redhouse.mobile

import android.view.View
import android.view.ViewGroup
import android.widget.Button
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import kotlin.math.abs

/** Component test: synthetic positions, no GPS permission or backend mutation. */
@RunWith(AndroidJUnit4::class)
class MapFocusTest {
    @get:Rule val compose=createAndroidComposeRule<DateTimeTestActivity>()
    private fun descendants(view:View):List<View> = listOf(view) +
        if(view is ViewGroup) (0 until view.childCount).flatMap {descendants(view.getChildAt(it))} else emptyList()

    @Test fun firstFixCentersAndUserCanRecenterAfterPanning() {
        var point by mutableStateOf<Pair<Double,Double>?>(null)
        compose.activityRule.scenario.onActivity {activity ->
            activity.setContent {MaterialTheme(colorScheme=redHouseColors) {RegionalMap(point?.first,point?.second,"Ubicación simulada",280.dp)}}
        }
        lateinit var map:MapView
        lateinit var button:Button
        compose.waitUntil(15000) {
            var ready=false
            compose.activityRule.scenario.onActivity {activity->
                val views=descendants(activity.findViewById(android.R.id.content))
                val found=views.filterIsInstance<MapView>().firstOrNull()
                val control=views.filterIsInstance<Button>().firstOrNull {it.contentDescription=="Centrar última ubicación"}
                if(found!=null && control!=null) {map=found;button=control;ready=true}
            }
            ready
        }
        fun near(lat:Double,lon:Double):Boolean {
            var result=false
            compose.activityRule.scenario.onActivity {result=abs(map.mapCenter.latitude-lat)<0.1 && abs(map.mapCenter.longitude-lon)<0.1}
            return result
        }
        compose.runOnIdle {assertEquals(View.GONE,button.visibility);point=51.5 to -0.12}
        compose.waitUntil(15000) {near(51.5,-0.12)}
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        compose.runOnIdle {assertEquals(12.0,map.zoomLevelDouble,0.01)}
        device.takeScreenshot(java.io.File(compose.activity.cacheDir,"map-first-fix.png"))
        android.util.Log.i("MapFocusVisual","first-fix-synthetic")
        Thread.sleep(12000)
        compose.runOnIdle {assertEquals(View.VISIBLE,button.visibility);map.controller.setZoom(9.0);map.controller.setCenter(GeoPoint(40.0,-74.0));point=52.0 to 1.0}
        compose.waitForIdle()
        assertTrue(near(40.0,-74.0))
        val control=device.wait(Until.findObject(By.desc("Centrar última ubicación")),15000)
        device.dumpWindowHierarchy(java.io.File(compose.activity.cacheDir,"map-focus-hierarchy.xml"))
        device.takeScreenshot(java.io.File(compose.activity.cacheDir,"map-before-click.png"))
        android.util.Log.i("MapFocusVisual",if(control==null) "control-missing" else "control-before-click")
        // Pause only the instrumentation thread so the host can capture this exact state.
        Thread.sleep(12000)
        assertNotNull(control);control.click()
        compose.waitUntil(15000) {near(52.0,1.0)}
        compose.runOnIdle {assertEquals(9.0,map.zoomLevelDouble,0.01)}
        device.takeScreenshot(java.io.File(compose.activity.cacheDir,"map-recentered.png"))
        android.util.Log.i("MapFocusVisual","recentered-synthetic")
        Thread.sleep(12000)
    }
}
