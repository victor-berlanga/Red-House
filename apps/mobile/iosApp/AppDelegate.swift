import UIKit
import Security
import RedHouse
import UserNotifications
import BackgroundTasks

final class KeychainStore: NSObject, SecureStore {
    private let query: [String: Any]
    init(account: String) { query = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.redhouse.mobile", kSecAttrAccount as String: account]; super.init() }
    func read() -> String? {
        var request = query
        request[kSecReturnData as String] = true
        var result: CFTypeRef?
        guard SecItemCopyMatching(request as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    func write(value: String?) {
        guard let value = value else { SecItemDelete(query as CFDictionary); return }
        let attributes: [String: Any] = [kSecValueData as String: Data(value.utf8),
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let result = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if result == errSecItemNotFound {
            var item = query; attributes.forEach { item[$0.key] = $0.value }
            precondition(SecItemAdd(item as CFDictionary, nil) == errSecSuccess, "Secure storage unavailable")
        } else { precondition(result == errSecSuccess, "Secure storage unavailable") }
    }
}
@main
class AppDelegate: UIResponder, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    var window: UIWindow?
    private var privacy: UIView?
    private let devices = IOSDeviceAccess()
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        BGTaskScheduler.shared.register(forTaskWithIdentifier:"org.redhouse.mobile.observations",using:nil){ task in
            guard UIApplication.shared.isProtectedDataAvailable else {
                task.setTaskCompleted(success:false);self.devices.scheduleSync();return
            }
            task.expirationHandler={BackgroundSync.shared.cancel();task.setTaskCompleted(success:false)}
            BackgroundSync.shared.start(store:KeychainStore(account:"session"),queue:KeychainStore(account:"observations"),config:KeychainStore(account:"gateway")){success in
                task.setTaskCompleted(success:success.boolValue)
                if !success.boolValue {self.devices.scheduleSync()}
            }
        }
        UNUserNotificationCenter.current().delegate = self
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = PlatformKt.MainViewController(store: KeychainStore(account: "session"), localStore: KeychainStore(account: "journal"), queueStore: KeychainStore(account: "observations"), configStore: KeychainStore(account: "gateway"), devices: devices)
        window.makeKeyAndVisible(); self.window = window; devices.presenter = window.rootViewController
        return true
    }
    func application(_ application:UIApplication,didRegisterForRemoteNotificationsWithDeviceToken deviceToken:Data){devices.registeredPush(deviceToken)}
    func application(_ application:UIApplication,didFailToRegisterForRemoteNotificationsWithError error:Error){devices.failedPush()}
    func userNotificationCenter(_ center:UNUserNotificationCenter,didReceive response:UNNotificationResponse,withCompletionHandler completionHandler:@escaping ()->Void){
        if let id=response.notification.request.content.userInfo["alert_id"] as? String,UUID(uuidString:id) != nil {NoticeLink.shared.receive(id:id)}
        completionHandler()
    }
    func applicationWillResignActive(_ application: UIApplication) {
        // Permission sheets also resign active; only a real background transition cancels capture.
        MobileLifecycle.shared.active(value: false)
        privacy?.removeFromSuperview()
        let cover = UIView(frame: window?.bounds ?? .zero); cover.backgroundColor = .systemBackground
        window?.addSubview(cover); privacy = cover
    }
    func applicationDidBecomeActive(_ application: UIApplication) { privacy?.removeFromSuperview(); privacy = nil; MobileLifecycle.shared.active(value: true) }
    func applicationDidEnterBackground(_ application: UIApplication) { devices.cancel() }
    func applicationProtectedDataWillBecomeUnavailable(_ application: UIApplication) {
        BackgroundSync.shared.cancel();devices.cancel()
    }
}
