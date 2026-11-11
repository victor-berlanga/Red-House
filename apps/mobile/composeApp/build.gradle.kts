import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import java.net.URI
plugins {
    kotlin("multiplatform")
    kotlin("plugin.serialization")
    kotlin("plugin.compose")
    id("org.jetbrains.compose")
    id("com.android.application")
}
val mobileGateway = providers.gradleProperty("mobileGateway").orElse("https://34.18.186.116")
val mobileLab = providers.gradleProperty("mobileLabDirectory").isPresent
val generateMobileEnvironment by tasks.registering {
    inputs.property("gateway", mobileGateway)
    inputs.property("editableGateway", mobileLab)
    val output = layout.buildDirectory.dir("generated/mobileEnvironment")
    outputs.dir(output)
    doLast {
        val origin = URI(mobileGateway.get())
        require(origin.scheme == "https" && origin.host != null && origin.userInfo == null &&
            origin.rawQuery == null && origin.rawFragment == null && origin.path.orEmpty() in setOf("", "/")) {
            "mobileGateway must be an HTTPS origin without credentials, path, query or fragment"
        }
        val directory = output.get().asFile.apply { mkdirs() }
        directory.resolve("MobileEnvironment.kt").writeText("""
            package org.redhouse.mobile
            internal object MobileEnvironment {
                const val gateway = "${origin.toASCIIString().trimEnd('/')}"
                const val editableGateway = $mobileLab
            }
        """.trimIndent())
    }
}
kotlin {
    androidTarget { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }
    listOf(iosX64(), iosArm64(), iosSimulatorArm64()).forEach {
        it.binaries.framework { baseName = "RedHouse"; isStatic = true }
    }
    sourceSets {
        commonMain { kotlin.srcDir(generateMobileEnvironment) }
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
            implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
            implementation("org.jetbrains.kotlinx:kotlinx-datetime:0.6.2")
            implementation("io.ktor:ktor-client-core:2.3.13")
            implementation("io.ktor:ktor-client-websockets:2.3.13")
        }
        commonTest.dependencies {
            implementation(kotlin("test"))
            implementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
            implementation("io.ktor:ktor-client-mock:2.3.13")
        }
        androidMain.dependencies {
            implementation("androidx.activity:activity-compose:1.10.1")
            implementation("com.journeyapps:zxing-android-embedded:4.3.0")
            implementation("org.osmdroid:osmdroid-android:6.1.20")
            implementation("androidx.exifinterface:exifinterface:1.3.7")
            implementation("androidx.work:work-runtime-ktx:2.10.1")
            implementation("com.google.firebase:firebase-messaging:24.1.2")
            implementation("io.ktor:ktor-client-okhttp:2.3.13")
        }
        androidInstrumentedTest.dependencies {
            implementation("androidx.test:runner:1.6.2")
            implementation("androidx.test.ext:junit:1.2.1")
            implementation("androidx.compose.ui:ui-test-junit4:1.8.2")
            implementation("androidx.test.uiautomator:uiautomator:2.3.0")
        }
        iosMain.dependencies { implementation("io.ktor:ktor-client-darwin:2.3.13") }
    }
}
android {
    namespace = "org.redhouse.mobile"
    compileSdk = 35
    defaultConfig { applicationId = "org.redhouse.mobile"; minSdk = 26; targetSdk = 35; versionCode = 3; versionName = "0.3.1"; testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    buildTypes { getByName("release") { isMinifyEnabled = false } }
}

// Opt-in ephemeral TLS lab only. Release never trusts this CA or packages lab credentials.
providers.gradleProperty("mobileLabDirectory").orNull?.let { directory ->
    android.sourceSets.getByName("debug").apply {
        manifest.srcFile("$directory/AndroidManifest.xml")
        res.srcDir("$directory/res")
    }
    android.sourceSets.getByName("androidTest").assets.srcDir("$directory/assets")
}

// Firebase's public client XML resources are supplied by the authorized project owner.
providers.gradleProperty("firebaseResources").orNull?.let { android.sourceSets.getByName("main").res.srcDir(it) }

