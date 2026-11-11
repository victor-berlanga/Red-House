package org.redhouse.mobile

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent

class MainActivity : ComponentActivity() {
    private lateinit var devices:AndroidDeviceAccess
    internal val deviceAccess get()=devices
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(WindowManager.LayoutParams.FLAG_SECURE,WindowManager.LayoutParams.FLAG_SECURE)
        intent.getStringExtra("alert_id")?.let {NoticeLink.pending.value=it}
        devices=AndroidDeviceAccess(this)
        val store=AndroidSecureStore(this)
        val local=AndroidSecureStore(this,"journal")
        val queue=AndroidSecureStore(this,"observations")
        val config=AndroidSecureStore(this,"gateway")
        setContent {RedHouseApp(store,local,queue,config,devices)}
    }
    override fun onResume(){super.onResume();MobileLifecycle.active(true)}
    override fun onPause(){MobileLifecycle.active(false);if(::devices.isInitialized)devices.pauseLocation();super.onPause()}
    override fun onDestroy(){if(::devices.isInitialized)devices.destroy();super.onDestroy()}
}
