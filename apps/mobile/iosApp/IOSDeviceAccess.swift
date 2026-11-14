import UIKit
import AVFoundation
import CoreLocation
import RedHouse
import UserNotifications
import BackgroundTasks
import Network

final class IOSDeviceAccess: NSObject, DeviceAccess, CLLocationManagerDelegate, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
    let source = "IOS"
    func openSettings(){if let url=URL(string:UIApplication.openSettingsURLString){UIApplication.shared.open(url)}}
    var pushCallback:((String?,String?)->Void)?
    func enablePush(done:@escaping (String?,String?)->Void){
        pushCallback=done
        UNUserNotificationCenter.current().requestAuthorization(options:[.alert,.sound,.badge]){allowed,_ in
            DispatchQueue.main.async {
                if allowed {UIApplication.shared.registerForRemoteNotifications()}
                else {self.pushCallback?(nil,"Notificaciones denegadas; la bandeja sigue disponible.");self.pushCallback=nil}
            }
        }
    }
    func disablePush(){pushCallback=nil;UIApplication.shared.unregisterForRemoteNotifications();UNUserNotificationCenter.current().removeAllDeliveredNotifications()}
    func registeredPush(_ token:Data){pushCallback?("apns:"+token.map{String(format:"%02x",$0)}.joined(),nil);pushCallback=nil}
    func failedPush(){pushCallback?(nil,"APNs requiere firma, entitlement y configuración autorizados.");pushCallback=nil}
    weak var presenter: UIViewController?
    private let location = CLLocationManager()
    private let network=NWPathMonitor()
    private var position: ((PhonePosition?, String?) -> Void)?
    private var photo: ((KotlinByteArray?, String?) -> Void)?
    private var scanner: QRController?
    private weak var picker: UIImagePickerController?
    private var captureGeneration = 0
    private var deadline: DispatchWorkItem?
    override init() { super.init(); location.delegate = self; location.desiredAccuracy = kCLLocationAccuracyBest; network.pathUpdateHandler={path in Connectivity.shared.setOnline(value:path.status == .satisfied)};network.start(queue:.main) }
    func scan(done: @escaping (String?, String?) -> Void) {
        let generation = captureGeneration
        cameraPermission { allowed in
            guard generation == self.captureGeneration else { done(nil,"Captura cancelada."); return }
            guard allowed else { done(nil,"Permiso de cámara denegado."); return }
            guard self.presenter?.presentedViewController == nil else {done(nil,"Cierra la captura anterior.");return}
            let scanner = QRController(); scanner.modalPresentationStyle = .fullScreen; self.scanner = scanner
            scanner.done = { value,error in done(value,error); self.scanner = nil }
            self.presenter?.present(scanner, animated: true)
        }
    }
    func photograph(done: @escaping (KotlinByteArray?, String?) -> Void) {
        let generation = captureGeneration
        cameraPermission { allowed in
            guard generation == self.captureGeneration else { done(nil,"Captura cancelada."); return }
            guard allowed, UIImagePickerController.isSourceTypeAvailable(.camera) else { done(nil,"Cámara no disponible o permiso denegado."); return }
            guard self.presenter?.presentedViewController == nil else {done(nil,"Cierra la captura anterior.");return}
            self.photo = done
            let picker = UIImagePickerController(); picker.sourceType = .camera; picker.delegate = self
            self.picker = picker
            self.presenter?.present(picker,animated:true)
        }
    }
    private func cameraPermission(_ action: @escaping (Bool)->Void) {
        AVCaptureDevice.requestAccess(for:.video) { granted in DispatchQueue.main.async { action(granted) } }
    }
    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) { picker.dismiss(animated:true); photo?(nil,"Captura cancelada.");photo=nil }
    func imagePickerController(_ picker: UIImagePickerController,didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey:Any]) {
        defer { picker.dismiss(animated:true); photo=nil }
        guard let image=info[.originalImage] as? UIImage else { photo?(nil,"Imagen no válida.");return }
        let factor=min(1,1600/max(image.size.width,image.size.height))
        let size=CGSize(width:image.size.width*factor,height:image.size.height*factor)
        // Rendering normalizes orientation and drops EXIF, including location metadata.
        let format=UIGraphicsImageRendererFormat();format.scale=1
        let clean=UIGraphicsImageRenderer(size:size,format:format).image { _ in image.draw(in:CGRect(origin:.zero,size:size)) }
        guard let data=clean.jpegData(compressionQuality:0.85),data.count<=10_485_760 else { photo?(nil,"Imagen demasiado grande.");return }
        let bytes=KotlinByteArray(size:Int32(data.count));for (index,value) in data.enumerated(){bytes.set(index:Int32(index),value:Int8(bitPattern:value))}
        photo?(bytes,nil)
    }
    func locate(done: @escaping (PhonePosition?, String?) -> Void) {
        pauseLocation();position=done
        let timeout=DispatchWorkItem { [weak self] in self?.finish(nil,"No se obtuvo una fijación reciente.") };deadline=timeout
        DispatchQueue.main.asyncAfter(deadline:.now()+25,execute:timeout)
        switch location.authorizationStatus {
        case .notDetermined:location.requestWhenInUseAuthorization()
        case .authorizedAlways,.authorizedWhenInUse:location.requestLocation()
        default:finish(nil,"Permiso de ubicación denegado.")
        }
    }
    func locationManagerDidChangeAuthorization(_ manager:CLLocationManager) {
        guard position != nil else { return }
        switch manager.authorizationStatus {
        case .authorizedAlways,.authorizedWhenInUse:manager.requestLocation()
        case .denied,.restricted:finish(nil,"Permiso de ubicación denegado.")
        default:break
        }
    }
    func locationManager(_ manager:CLLocationManager,didUpdateLocations locations:[CLLocation]) {
        guard let value=locations.last,abs(value.timestamp.timeIntervalSinceNow)<=30,value.horizontalAccuracy>=0 else {finish(nil,"Fijación antigua o inválida.");return}
        #if targetEnvironment(simulator)
        let simulated=true
        #else
        let simulated=value.sourceInformation?.isSimulatedBySoftware ?? false
        #endif
        let formatter=ISO8601DateFormatter();formatter.formatOptions=[.withInternetDateTime,.withFractionalSeconds]
        finish(PhonePosition(latitude:value.coordinate.latitude,longitude:value.coordinate.longitude,accuracy:value.horizontalAccuracy,capturedAt:formatter.string(from:value.timestamp),simulated:simulated),nil)
    }
    func locationManager(_ manager:CLLocationManager,didFailWithError error:Error){finish(nil,"Ubicación no disponible.")}
    private func finish(_ value:PhonePosition?,_ error:String?){location.stopUpdatingLocation();deadline?.cancel();deadline=nil;let callback=position;position=nil;callback?(value,error)}
    func pauseLocation(){finish(nil,"Captura detenida al salir de primer plano.")}
    // iOS may defer this opportunity. Foreground synchronization remains available.
    func scheduleSync() {
        let request=BGAppRefreshTaskRequest(identifier:AppEnvironment.backgroundTask)
        request.earliestBeginDate=Date(timeIntervalSinceNow:30)
        try? BGTaskScheduler.shared.submit(request)
    }
    func clearWork() {BGTaskScheduler.shared.cancel(taskRequestWithIdentifier:AppEnvironment.backgroundTask);BackgroundSync.shared.cancel()}
    func cancel(){
        captureGeneration += 1
        pauseLocation();scanner?.cancelCapture();scanner=nil
        picker?.dismiss(animated:false);picker=nil
        let callback=photo;photo=nil;callback?(nil,"Captura cancelada.")
    }
}

final class QRController:UIViewController,AVCaptureMetadataOutputObjectsDelegate {
    var done:((String?,String?)->Void)?
    private let session=AVCaptureSession()
    private let captureQueue=DispatchQueue(label:"org.redhouse.mobile.qr")
    private var preview:AVCaptureVideoPreviewLayer?
    override func viewDidLoad(){
        super.viewDidLoad();view.backgroundColor = .black
        guard let camera=AVCaptureDevice.default(for:.video),let input=try? AVCaptureDeviceInput(device:camera),session.canAddInput(input) else {finish(nil,"Cámara no disponible.");return}
        session.addInput(input);let output=AVCaptureMetadataOutput()
        guard session.canAddOutput(output) else {finish(nil,"Lector no disponible.");return}
        session.addOutput(output);output.setMetadataObjectsDelegate(self,queue:.main)
        output.metadataObjectTypes=[.qr,.code128,.ean13,.dataMatrix].filter{output.availableMetadataObjectTypes.contains($0)}
        let layer=AVCaptureVideoPreviewLayer(session:session);layer.videoGravity = .resizeAspectFill;view.layer.addSublayer(layer);preview=layer
        let cancel=UIButton(type:.system);cancel.setTitle("Cancelar",for:.normal);cancel.addTarget(self,action:#selector(cancelScan),for:.touchUpInside);cancel.frame=CGRect(x:20,y:60,width:120,height:50);view.addSubview(cancel)
        captureQueue.async{self.session.startRunning()}
    }
    override func viewDidLayoutSubviews(){super.viewDidLayoutSubviews();preview?.frame=view.bounds}
    override func viewDidDisappear(_ animated:Bool){super.viewDidDisappear(animated);stop()}
    func metadataOutput(_ output:AVCaptureMetadataOutput,didOutput objects:[AVMetadataObject],from connection:AVCaptureConnection){if let code=objects.first as? AVMetadataMachineReadableCodeObject,let value=code.stringValue {finish(value,nil)}}
    @objc private func cancelScan(){finish(nil,"Escaneo cancelado.")}
    func cancelCapture(){finish(nil,"Escaneo cancelado.")}
    func stop(){captureQueue.async{self.session.stopRunning()}}
    private func finish(_ value:String?,_ error:String?){stop();let callback=done;done=nil;dismiss(animated:true){callback?(value,error)}}
}
