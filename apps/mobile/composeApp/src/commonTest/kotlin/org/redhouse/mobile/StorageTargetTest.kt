package org.redhouse.mobile

import kotlin.test.*

class StorageTargetTest {
    private val gateway="https://gateway.example:8443/services/documentos"
    @Test fun localCapabilityMustMatchOriginAndPath() {
        assertTrue(storageTarget("https://gateway.example:8443/storage/v1/objects/abc_123-==",gateway))
        listOf("http://gateway.example:8443/storage/v1/objects/abc", "https://gateway.example/storage/v1/objects/abc", "https://sub.gateway.example:8443/storage/v1/objects/abc", "https://user@gateway.example:8443/storage/v1/objects/abc", "https://gateway.example:8443/storage/v1/objects/abc?x=1", "https://gateway.example:8443/storage/v1/objects/abc#fragment", "https://gateway.example:8443/public/abc", "https://gateway.example:8443/storage/v1/objects/abc/extra").forEach { assertFails { storageTarget(it,gateway) } }
    }
    @Test fun gcsAndHeadersAreRestricted() {
        assertFalse(storageTarget("https://storage.googleapis.com/bucket/key?signature=abc",gateway,"bucket"))
        assertFalse(storageTarget("https://bucket.storage.googleapis.com/key?signature=abc",gateway,"bucket"))
        assertFails { storageTarget("https://storage.googleapis.com/bucket/key?signature=abc",gateway,"") }
        assertFails { storageTarget("https://attacker.storage.googleapis.com/key?signature=abc",gateway,"bucket") }
        assertFails { storageTarget("https://storage.googleapis.com/attacker/key?signature=abc",gateway,"bucket") }
        assertFails { storageTarget("https://bucket.storage.googleapis.com:444/key",gateway,"bucket") }
        assertFails { storageTarget("https://storage.googleapis.com/bucket/%2e%2e/attacker/key",gateway,"bucket") }
        assertFails { storageTarget("https://storage.googleapis.com/bucket%2fattacker/key",gateway,"bucket") }
        assertFails { storageTarget("https://storage.googleapis.com.evil.test/key",gateway) }
        storageHeaders(obj("Content-Type" to "image/jpeg"),true)
        storageHeaders(obj("Content-Type" to "image/jpeg","x-goog-if-generation-match" to "0"),false)
        assertFails { storageHeaders(obj("Content-Type" to "image/jpeg","Authorization" to "secret"),true) }
    }
}
