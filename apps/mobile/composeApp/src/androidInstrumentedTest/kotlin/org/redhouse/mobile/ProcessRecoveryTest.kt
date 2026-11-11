package org.redhouse.mobile

import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*

/** Run phases separately, with adb shell am force-stop org.redhouse.mobile between them. */
@RunWith(AndroidJUnit4::class)
class ProcessRecoveryTest {
    @Test fun persistBeforeProcessDeath()=runBlocking {
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val context=instrumentation.targetContext
        val lab=codec.parseToJsonElement(instrumentation.context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        ActivityScenario.launch(MainActivity::class.java).use {
            val client=platformClient()
            try {
                val session=Session(Api(client,gatewayBases(lab.text("android_gateway"))),AndroidSecureStore(context))
                session.login("transport1",lab.text("password"),"")
                AndroidSecureStore(context,"gateway").write(lab.text("android_gateway"))
                val journal=LocalJournal(AndroidSecureStore(context,"journal"));journal.bind(session.user!!.text("id"))
                val repository=MobileRepository(session,journal,"ANDROID");repository.device()
                val task=repository.shipment(lab.text("shipment_id"))
                val queue=ObservationQueue(AndroidSecureStore(context,"observations"),session)
                queue.clear()
                val id=queue.enqueue(task.text("id"),journal.deviceId(),task["version"]!!.jsonPrimitive.int,"Observación sintética persistida antes de morir el proceso")
                journal.put("recovery_probe",JsonPrimitive(id))
                assertEquals("PENDING",queue.entries().single().text("state"))
            }finally{client.close()}
        }
    }
    @Test fun recoverAfterProcessDeath()=runBlocking {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val gateway=AndroidSecureStore(context,"gateway").read()
        assertNotNull("Execute persistBeforeProcessDeath first, then force-stop without clearing data",gateway)
        val client=platformClient()
        try {
            val session=Session(Api(client,gatewayBases(gateway!!)),AndroidSecureStore(context));session.restore()
            val journal=LocalJournal(AndroidSecureStore(context,"journal"))
            val queue=ObservationQueue(AndroidSecureStore(context,"observations"),session)
            assertEquals(journal.value("recovery_probe")!!.jsonPrimitive.content,queue.entries().single()["command"]!!.jsonObject.text("id"))
            queue.synchronize();queue.synchronize()
            assertEquals("RECORDED",queue.entries().single().text("state"))
            MobileRepository(session,journal,"ANDROID").revokeDevice()
            assertTrue(session.logout());queue.clear();journal.clear();AndroidSecureStore(context,"gateway").write(null)
        }finally{client.close()}
    }
    @Test fun workManagerSynchronizesWithoutForegroundUi()=runBlocking {
        persistBeforeProcessDeath()
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val client=platformClient()
        val manager=androidx.work.WorkManager.getInstance(context)
        try {
            val session=Session(Api(client,gatewayBases(AndroidSecureStore(context,"gateway").read()!!)),AndroidSecureStore(context))
            session.restore()
            val queue=ObservationQueue(AndroidSecureStore(context,"observations"),session)
            manager.cancelUniqueWork("redhouse-observations").result.get(10,java.util.concurrent.TimeUnit.SECONDS)
            ObservationWorker.schedule(context)
            kotlinx.coroutines.withTimeout(60000){
                while(queue.entries().single().text("state")!="RECORDED")kotlinx.coroutines.delay(500)
                while(manager.getWorkInfosForUniqueWork("redhouse-observations").get().none{it.state==androidx.work.WorkInfo.State.SUCCEEDED})kotlinx.coroutines.delay(500)
            }
            val journal=LocalJournal(AndroidSecureStore(context,"journal"))
            assertEquals(journal.value("recovery_probe")!!.jsonPrimitive.content,queue.entries().single()["command"]!!.jsonObject.text("id"))
            MobileRepository(session,journal,"ANDROID").revokeDevice()
            assertTrue(session.logout());queue.clear();journal.clear();AndroidSecureStore(context,"gateway").write(null)
        }finally{manager.cancelUniqueWork("redhouse-observations");client.close()}
    }
}
