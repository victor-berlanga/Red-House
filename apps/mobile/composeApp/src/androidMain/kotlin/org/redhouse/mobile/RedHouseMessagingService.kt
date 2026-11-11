package org.redhouse.mobile

import android.app.*
import android.content.Intent
import android.content.pm.PackageManager
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

/** Provider payload is untrusted; only a generic notice and opaque identifier can leave this boundary. */
class RedHouseMessagingService:FirebaseMessagingService(){
    override fun onNewToken(token:String){
        AndroidSecureStore(this,"push-token").write(token)
        ObservationWorker.schedule(this)
    }
    override fun onMessageReceived(message:RemoteMessage){
        if(AndroidSecureStore(this).read()==null)return
        val id=message.data["alert_id"]?:return
        if(!id.matches(Regex("[0-9a-f-]{36}")))return
        if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return
        val manager=getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel("operational","Avisos Red House",NotificationManager.IMPORTANCE_DEFAULT).apply{lockscreenVisibility=Notification.VISIBILITY_PRIVATE})
        val intent=Intent(this,MainActivity::class.java).putExtra("alert_id",id)
        val open=PendingIntent.getActivity(this,id.hashCode(),intent,PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        manager.notify(id.hashCode(),Notification.Builder(this,"operational").setSmallIcon(R.drawable.ic_redhouse)
            .setContentTitle("Red House").setContentText("Hay un aviso en tu bandeja autorizada.").setVisibility(Notification.VISIBILITY_PRIVATE)
            .setContentIntent(open).setAutoCancel(true).build())
    }
}
