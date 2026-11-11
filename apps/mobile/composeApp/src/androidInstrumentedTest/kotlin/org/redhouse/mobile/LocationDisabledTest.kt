package org.redhouse.mobile

import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Run separately from denial tests; this case grants location and restores the system switch. */
@RunWith(AndroidJUnit4::class)
class LocationDisabledTest {
    @Test fun disabledLocationReturnsWithoutFix(){
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.ACCESS_FINE_LOCATION")
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.ACCESS_COARSE_LOCATION")
        val previous=device.executeShellCommand("settings get secure location_mode").trim().toIntOrNull() ?: 3
        device.executeShellCommand("settings put secure location_mode 0")
        try{
            ActivityScenario.launch(MainActivity::class.java).use{scenario->
                val returned=CountDownLatch(1);var point:PhonePosition?=null;var failure:String?=null
                scenario.onActivity{it.deviceAccess.locate{value,error->point=value;failure=error;returned.countDown()}}
                assertTrue(returned.await(15,TimeUnit.SECONDS));assertNull(point)
                assertEquals("Ubicación desactivada.",failure)
            }
        }finally{device.executeShellCommand("settings put secure location_mode $previous")}
    }
}
