import UIKit
import Security
import RedHouse
import UserNotifications
import BackgroundTasks
#if REDHOUSE_LAB
import CryptoKit
#endif

// Immutable host/framework guard. A mismatch aborts before any Keychain access or
// GatewayConfiguration.prepare, whose environment reset must never touch normal data.
enum AppEnvironment {
    static let bundleIdentifier: String = {
        #if REDHOUSE_LAB
        #if !DEBUG
        #error("Red House Lab must be a Debug build")
        #endif
        let expectedBundle = "org.redhouse.mobile.lab"
        let expectedVariant = "lab"
        #else
        let expectedBundle = "org.redhouse.mobile"
        let expectedVariant = "normal"
        #endif
        let bundle = Bundle.main
        guard bundle.bundleIdentifier == expectedBundle,
              let variant = bundle.object(forInfoDictionaryKey: "RedHouseVariant") as? String,
              variant == expectedVariant,
              let gateway = bundle.object(forInfoDictionaryKey: "RedHouseGateway") as? String,
              let identifiers = bundle.object(forInfoDictionaryKey: "BGTaskSchedulerPermittedIdentifiers") as? [String],
              identifiers == [expectedBundle + ".observations"],
              PlatformKt.iosHostEnvironmentMatches(bundleIdentifier: expectedBundle, variant: variant,
                  gateway: gateway, backgroundTask: expectedBundle + ".observations") else {
            preconditionFailure("Application environment mismatch; stored data was not accessed")
        }
        if expectedVariant == "normal" {
            precondition(gateway == "https://34.18.186.116", "Normal application gateway mismatch")
        }
        return expectedBundle
    }()
    static var backgroundTask: String { bundleIdentifier + ".observations" }
    #if REDHOUSE_LAB
    private static let installLabTrust: Void = {
        guard let gateway = Bundle.main.object(forInfoDictionaryKey: "RedHouseGateway") as? String,
              let expectedHash = Bundle.main.object(forInfoDictionaryKey: "RedHouseLabCASHA256") as? String,
              let url = Bundle.main.url(forResource: "redhouse-lab-ca", withExtension: "der"),
              let data = try? Data(contentsOf: url),
              SHA256.hash(data: data).map({String(format:"%02x",$0)}).joined() == expectedHash,
              let certificate = SecCertificateCreateWithData(nil, data as CFData),
              let evaluator = LabTrustEvaluator(gateway: gateway, certificate: certificate) else {
            preconditionFailure("Laboratory trust configuration unavailable")
        }
        PlatformKt.installIosLabTrustEvaluator(evaluator: evaluator)
    }()
    #endif
    static func validate() {
        _ = bundleIdentifier
        #if REDHOUSE_LAB
        _ = installLabTrust
        #endif
    }
}

#if REDHOUSE_LAB
/// Trust only the pinned lab CA for the explicitly configured HTTPS/WSS origin.
private final class LabTrustEvaluator: NSObject, IosLabTrustEvaluator {
    private let host: String
    private let port: Int
    private let certificate: SecCertificate
    init?(gateway: String, certificate: SecCertificate) {
        guard let url = URLComponents(string: gateway), url.scheme == "https",
              let host = url.host, !host.isEmpty, url.user == nil, url.password == nil,
              url.path.isEmpty, url.query == nil, url.fragment == nil else { return nil }
        self.host = host.lowercased(); self.port = url.port ?? 443; self.certificate = certificate
        super.init()
    }
    private func matches(_ url: URL?) -> Bool {
        guard let value = url.flatMap({URLComponents(url: $0, resolvingAgainstBaseURL: false)}),
              let scheme = value.scheme?.lowercased(), ["https", "wss"].contains(scheme),
              value.host?.lowercased() == host, (value.port ?? 443) == port,
              value.user == nil, value.password == nil else { return false }
        return true
    }
    func decide(task: URLSessionTask, challenge: URLAuthenticationChallenge) -> Int32 {
        let space = challenge.protectionSpace
        let original = matches(task.originalRequest?.url)
        let current = matches(task.currentRequest?.url)
        let intended = original && current
        let labChallenge = space.host.lowercased() == host && space.port == port
        if !intended { return (original || current || labChallenge) ? 2 : 0 }
        guard labChallenge, space.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let trust = space.serverTrust else { return 2 }
        guard SecTrustSetPolicies(trust, SecPolicyCreateSSL(true, host as CFString)) == errSecSuccess,
              SecTrustSetAnchorCertificates(trust, [certificate] as CFArray) == errSecSuccess,
              SecTrustSetAnchorCertificatesOnly(trust, true) == errSecSuccess,
              SecTrustEvaluateWithError(trust, nil) else { return 2 }
        return 1
    }
}
#endif

final class KeychainStore: NSObject, SecureStore {
    private let query: [String: Any]
    init(account: String) { AppEnvironment.validate(); query = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: AppEnvironment.bundleIdentifier, kSecAttrAccount as String: account]; super.init() }
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
        AppEnvironment.validate()
        BGTaskScheduler.shared.register(forTaskWithIdentifier:AppEnvironment.backgroundTask,using:nil){ task in
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
