package org.redhouse.mobile

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity

/** Host for isolated instrumented component tests; never exported. */
class DateTimeTestActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
    }
}
