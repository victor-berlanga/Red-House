package org.redhouse.mobile

import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.*
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Run after pm clear: a system permission denial must reach the caller without starting GPS. */
@RunWith(AndroidJUnit4::class)
class PermissionDenialTest {
    @Test fun cameraDenialReturnsWithoutOpeningScanner(){
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        ActivityScenario.launch(MainActivity::class.java).use{scenario->
            val returned=CountDownLatch(1);var code:String?=null;var failure:String?=null
            scenario.onActivity{it.deviceAccess.scan{value,error->code=value;failure=error;returned.countDown()}}
            val deny=device.wait(Until.findObject(By.res("com.android.permissioncontroller","permission_deny_button")),30000)
            assertNotNull("Run this case with no camera grant",deny);deny!!.click()
            assertTrue(returned.await(15,TimeUnit.SECONDS));assertNull(code)
            assertEquals("Permiso de cámara denegado.",failure)
        }
    }
    @Test fun locationDenialReturnsWithoutCapture(){
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        ActivityScenario.launch(MainActivity::class.java).use{scenario->
            val returned=CountDownLatch(1);var point:PhonePosition?=null;var failure:String?=null
            scenario.onActivity{it.deviceAccess.locate{value,error->point=value;failure=error;returned.countDown()}}
            val deny=device.wait(Until.findObject(By.res("com.android.permissioncontroller","permission_deny_button")),30000)
            assertNotNull("Run this case on an app with no location grant",deny)
            deny!!.click()
            assertTrue(returned.await(15,TimeUnit.SECONDS));assertNull(point)
            assertEquals("Permiso de ubicación denegado.",failure)
        }
    }
}
