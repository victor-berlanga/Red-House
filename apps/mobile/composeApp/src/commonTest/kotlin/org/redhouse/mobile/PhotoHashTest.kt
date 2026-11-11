package org.redhouse.mobile

import kotlin.test.*

class PhotoHashTest {
    @Test fun sha256MatchesKnownVectors(){
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",sha256(byteArrayOf()))
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",sha256("abc".encodeToByteArray()))
    }
}
