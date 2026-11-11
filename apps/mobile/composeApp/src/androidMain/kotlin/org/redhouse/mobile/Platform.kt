package org.redhouse.mobile

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import io.ktor.client.*
import io.ktor.client.engine.okhttp.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.websocket.*

actual fun newId() = java.util.UUID.randomUUID().toString()
actual fun platformClient() = HttpClient(OkHttp) {
    followRedirects = false
    install(HttpTimeout) { requestTimeoutMillis = 15000; connectTimeoutMillis = 10000; socketTimeoutMillis = 20000 }
    install(WebSockets)
}
class AndroidSecureStore(context: Context, name: String = "session") : SecureStore {
    private val file = AtomicFile(File(context.noBackupFilesDir, "$name.gcm"))
    private val alias = "redhouse.$name.v1"
    private val keys = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
    private fun key(): SecretKey {
        (keys.getKey(alias, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build())
        }.generateKey()
    }
    override fun read(): String? {
        if (!file.baseFile.exists()) return null
        return try {
            val bytes = file.readFully()
            require(bytes.size > 28)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes.copyOfRange(0, 12)))
            cipher.doFinal(bytes.copyOfRange(12, bytes.size)).decodeToString()
        } catch (_: Exception) { write(null); null }
    }
    override fun write(value: String?) {
        if (value == null) { file.delete(); keys.deleteEntry(alias); return }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val bytes = cipher.iv + cipher.doFinal(value.encodeToByteArray())
        val stream = file.startWrite()
        try { stream.write(bytes); file.finishWrite(stream) }
        catch (error: Exception) { file.failWrite(stream); throw error }
    }
}
