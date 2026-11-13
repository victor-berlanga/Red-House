package org.redhouse.mobile

import io.ktor.client.*
import io.ktor.client.engine.mock.*
import io.ktor.http.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import java.lang.management.ManagementFactory
import java.util.concurrent.Executors
import java.io.File
import kotlin.test.*

/** JVM CPU comparison with a synthetic response; not a device fluency benchmark. */
class ParsingCostTest {
    @Test fun parsingKeepsResultsAndReducesCallerCpu() {
        val raw=buildJsonObject {
            put("meta",obj("service" to "test"))
            put("data",buildJsonObject {
                put("id","synthetic");put("tenant_id","synthetic");put("role","DONOR")
                put("items",buildJsonArray {repeat(18000){add(obj("label" to "Synthetic result $it", "value" to "$it"))}})
            })
        }.toString()
        val cpu=ManagementFactory.getThreadMXBean()
        val results=mapOf("before" to mutableListOf<Double>(), "after" to mutableListOf<Double>())
        Executors.newSingleThreadExecutor { task -> Thread(task,"synthetic-ui") }.asCoroutineDispatcher().use { ui ->
            HttpClient(MockEngine {respond(raw,headers=headersOf(HttpHeaders.ContentType,"application/json"))}).use { http ->
                val variants=listOf("before" to Api(http,mapOf("identidad" to "https://example.com"),ui),
                    "after" to Api(http,mapOf("identidad" to "https://example.com"),Dispatchers.Default))
                runBlocking(ui) {
                    repeat(22){index->
                        // Alternate order to avoid giving only the second variant a warm JVM.
                        for ((name,api) in if(index%2==0) variants else variants.reversed()) {
                            val start=cpu.currentThreadCpuTime
                            val data=api.call("identidad","/api/v1/auth/me")
                            val elapsed=(cpu.currentThreadCpuTime-start)/1_000_000.0
                            assertEquals(18000,data.getValue("items").jsonArray.size)
                            if(index>=2)results.getValue(name).add(elapsed)
                        }
                    }
                }
            }
        }
        fun median(name:String)=results.getValue(name).sorted().let {(it[9]+it[10])/2}
        assertTrue(median("after")<median("before"),results.toString())
        System.getenv("OPTIMIZATION_MOBILE_EVIDENCE")?.let { path ->
            File(path,"parsing-cpu.json").writeText(buildJsonObject {
                put("environment","JVM synthetic UI thread, MockEngine; no physical device")
                put("order","interleaved AB/BA; same HttpClient and payload")
                put("bytes",raw.encodeToByteArray().size);put("warmup",2);put("repetitions",20)
                results.forEach {(key,value)->put(key,buildJsonObject {put("median_cpu_ms",median(key));put("cpu_ms",JsonArray(value.map(::JsonPrimitive)))})}
            }.toString())
        }
    }
}
