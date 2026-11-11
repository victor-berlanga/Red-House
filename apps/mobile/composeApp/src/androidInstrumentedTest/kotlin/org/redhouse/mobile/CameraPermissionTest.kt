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

/** Real camera activities in the emulator. Does not claim optical QR decoding or a physical lens. */
@RunWith(AndroidJUnit4::class)
class CameraPermissionTest {
    @Test fun qrOpensCameraAndCancellationReturnsToApp(){
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.CAMERA")
        ActivityScenario.launch(MainActivity::class.java).use{scenario->
            val returned=CountDownLatch(1)
            scenario.onActivity{it.deviceAccess.scan{value,_->assertNull(value);returned.countDown()}}
            assertTrue(device.wait(Until.hasObject(By.textContains("Escanea el identificador")),30000))
            device.pressBack();assertTrue(returned.await(30,TimeUnit.SECONDS))
        }
    }
    @Test fun systemCameraReturnsRealJpeg(){
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        device.executeShellCommand("pm grant org.redhouse.mobile android.permission.CAMERA")
        ActivityScenario.launch(MainActivity::class.java).use{scenario->
            val returned=CountDownLatch(1);var image:ByteArray?=null;var failure:String?=null
            scenario.onActivity{it.deviceAccess.photograph{bytes,error->image=bytes;failure=error;returned.countDown()}}
            val shutter=device.wait(Until.findObject(By.res("com.android.camera2","shutter_button")),30000)
                ?:device.findObject(By.desc("Shutter"))
            assertNotNull("System camera shutter unavailable",shutter)
            // Camera2 exposes the shutter before its sensor is ready on a cold emulator.
            var done:UiObject2?=null
            repeat(3){
                if(done==null){
                    device.findObject(By.res("com.android.camera2","shutter_button"))?.click()
                    done=device.wait(Until.findObject(By.res("com.android.camera2","done_button")),8000)
                        ?:device.findObject(By.desc("Done"))
                }
            }
            assertNotNull("Camera never entered capture review",done);done!!.click()
            assertTrue("Camera did not return",returned.await(30,TimeUnit.SECONDS))
            assertNotNull(failure,image);assertTrue(image!!.size in 1..10485760)
            assertEquals(0xff,image!![0].toInt() and 0xff);assertEquals(0xd8,image!![1].toInt() and 0xff)
            assertFalse(java.io.File(InstrumentationRegistry.getInstrumentation().targetContext.cacheDir,"capture").listFiles().orEmpty().any())
        }
    }
}
