package org.redhouse.mobile

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.FileProvider
import androidx.exifinterface.media.ExifInterface
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import java.io.ByteArrayOutputStream
import java.io.File
import java.time.Instant

class AndroidDeviceAccess(private val activity: ComponentActivity) : DeviceAccess {
    override val source = "ANDROID"
    override fun openSettings(){activity.startActivity(android.content.Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,android.net.Uri.parse("package:"+activity.packageName)))}
    private val connectivity=activity.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
    private val networkCallback=object:android.net.ConnectivityManager.NetworkCallback(){
        override fun onCapabilitiesChanged(network:android.net.Network,capabilities:android.net.NetworkCapabilities){Connectivity.setOnline(capabilities.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_VALIDATED))}
        override fun onLost(network:android.net.Network){Connectivity.setOnline(false)}
    }
    init {connectivity.registerDefaultNetworkCallback(networkCallback)}
    fun destroy(){cancel();connectivity.unregisterNetworkCallback(networkCallback)}
    private var pushCallback:((String?,String?)->Unit)?=null
    private val notificationPermission=activity.registerForActivityResult(ActivityResultContracts.RequestPermission()){allowed->
        if(allowed)requestPushToken() else {pushCallback?.invoke(null,"Notificaciones denegadas; la bandeja interna sigue disponible.");pushCallback=null}
    }
    override fun enablePush(done:(String?,String?)->Unit){
        pushCallback=done
        if(android.os.Build.VERSION.SDK_INT>=33 && activity.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        else requestPushToken()
    }
    private fun requestPushToken(){
        if(com.google.firebase.FirebaseApp.getApps(activity).isEmpty()){
            pushCallback?.invoke(null,"Falta configurar Firebase para org.redhouse.mobile.");pushCallback=null;return
        }
        val messaging=com.google.firebase.messaging.FirebaseMessaging.getInstance();messaging.isAutoInitEnabled=true
        messaging.token.addOnCompleteListener {task->
            if(task.isSuccessful){AndroidSecureStore(activity,"push-token").write(task.result);pushCallback?.invoke(task.result,null)}
            else pushCallback?.invoke(null,"Proveedor push no disponible.")
            pushCallback=null
        }
    }
    override fun disablePush(){
        pushCallback=null;AndroidSecureStore(activity,"push-token").write(null)
        if(com.google.firebase.FirebaseApp.getApps(activity).isNotEmpty())com.google.firebase.messaging.FirebaseMessaging.getInstance().apply{isAutoInitEnabled=false;deleteToken()}
        (activity.getSystemService(Context.NOTIFICATION_SERVICE) as android.app.NotificationManager).cancelAll()
    }
    private var scanned: ((String?, String?) -> Unit)? = null
    private var photographed: ((ByteArray?, String?) -> Unit)? = null
    private var located: ((PhonePosition?, String?) -> Unit)? = null
    private var pending: (() -> Unit)? = null
    private var image: File? = null
    private val manager = activity.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val handler = Handler(Looper.getMainLooper())
    private val timeout = Runnable { finishLocation(null,"No se obtuvo una fijación reciente. Revisa GPS y permiso.") }
    private val listener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            if (System.currentTimeMillis() - location.time > 30000) return
            finishLocation(PhonePosition(location.latitude,location.longitude,location.accuracy.toDouble(),
                Instant.ofEpochMilli(location.time).toString(),(location.isFromMockProvider || android.os.Build.FINGERPRINT.contains("generic") || android.os.Build.MODEL.contains("sdk_gphone") || android.os.Build.HARDWARE in setOf("goldfish","ranchu"))),null)
        }
        override fun onProviderDisabled(provider: String) { finishLocation(null,"GPS desactivado.") }
        override fun onProviderEnabled(provider: String) {}
        override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    }
    private val permission = activity.registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { grants ->
        val next = pending; pending = null
        if (grants.values.any { it }) next?.invoke() else {
            scanned?.invoke(null,"Permiso de cámara denegado."); scanned=null
            photographed?.invoke(null,"Permiso de cámara denegado."); photographed=null
            finishLocation(null,"Permiso de ubicación denegado.")
        }
    }
    private val scanner = activity.registerForActivityResult(ScanContract()) { result ->
        scanned?.invoke(result.contents, if (result.contents == null) "Escaneo cancelado." else null); scanned=null
    }
    private val camera = activity.registerForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        val file=image
        val completion=photographed;photographed=null
        var result:ByteArray?=null
        var failure:String?=null
        try {
            if (!success || file==null) failure="Captura cancelada."
            else {
                val bounds=BitmapFactory.Options().apply { inJustDecodeBounds=true }
                BitmapFactory.decodeFile(file.path,bounds)
                var sample=1
                while (maxOf(bounds.outWidth,bounds.outHeight)/sample>1600) sample*=2
                val bitmap=BitmapFactory.decodeFile(file.path,BitmapFactory.Options().apply { inSampleSize=sample })
                    ?: error("Imagen inválida")
                val orientation=ExifInterface(file).getAttributeInt(ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL)
                val matrix=Matrix().apply { when(orientation) {
                    ExifInterface.ORIENTATION_ROTATE_90 -> postRotate(90f)
                    ExifInterface.ORIENTATION_ROTATE_180 -> postRotate(180f)
                    ExifInterface.ORIENTATION_ROTATE_270 -> postRotate(270f)
                } }
                val normalized=Bitmap.createBitmap(bitmap,0,0,bitmap.width,bitmap.height,matrix,true)
                val bytes=ByteArrayOutputStream().use { normalized.compress(Bitmap.CompressFormat.JPEG,85,it);it.toByteArray() }
                require(bytes.size<=10485760)
                result=bytes
                if(normalized!==bitmap) normalized.recycle(); bitmap.recycle()
            }
        } catch (_: Exception) {result=null;failure="No se pudo procesar la fotografía."}
        finally {file?.delete();image=null}
        // Completion means the private source file has already been removed.
        completion?.invoke(result,failure)
    }
    private fun cameraPermission(action: () -> Unit) {
        if(activity.checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED) action()
        else {pending=action;permission.launch(arrayOf(Manifest.permission.CAMERA))}
    }
    override fun scan(done: (String?,String?) -> Unit) {
        scanned=done;cameraPermission { scanner.launch(ScanOptions().setDesiredBarcodeFormats(ScanOptions.ALL_CODE_TYPES).setPrompt("Escanea el identificador de la unidad").setBeepEnabled(false).setBarcodeImageEnabled(false)) }
    }
    override fun photograph(done: (ByteArray?,String?) -> Unit) {
        photographed=done;cameraPermission {
            val dir=File(activity.cacheDir,"capture").apply { mkdirs() }
            dir.listFiles()?.forEach { it.delete() }
            image=File.createTempFile("evidence-",".jpg",dir)
            try {camera.launch(FileProvider.getUriForFile(activity,activity.packageName+".capture",image!!))}
            catch(_:android.content.ActivityNotFoundException){image?.delete();image=null;photographed?.invoke(null,"No hay aplicación de cámara disponible.");photographed=null}
        }
    }
    override fun locate(done: (PhonePosition?,String?) -> Unit) {
        located=done
        val start: () -> Unit = {
            try {
                val fine=activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED
                val provider=if(fine && manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) LocationManager.GPS_PROVIDER else LocationManager.NETWORK_PROVIDER
                if(!manager.isProviderEnabled(provider)) finishLocation(null,"Ubicación desactivada.")
                else {manager.requestLocationUpdates(provider,1000L,0f,listener,Looper.getMainLooper());handler.postDelayed(timeout,25000)}
            } catch (_: SecurityException) {finishLocation(null,"Permiso de ubicación revocado.")}
        }
        if(activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED || activity.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED) start()
        else {pending=start;permission.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION))}
    }
    private fun finishLocation(point:PhonePosition?,error:String?) {
        manager.removeUpdates(listener);handler.removeCallbacks(timeout)
        val callback=located;located=null;callback?.invoke(point,error)
    }
    /** Activity pause cancels location; camera/QR return through their dedicated activity results. */
    fun pauseLocation() {
        // The system permission dialog pauses this activity before its result arrives.
        // Keep that pending callback; no location listener exists until consent returns.
        if(pending==null) finishLocation(null,"Captura interrumpida al salir de primer plano.")
    }
    override fun scheduleSync() {ObservationWorker.schedule(activity)}
    override fun clearWork() {ObservationWorker.cancel(activity)}
    override fun cancel() {pending=null;scanned=null;photographed=null;image?.delete();image=null;finishLocation(null,"Captura detenida.")}
}
