package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeContentTestRule

/** Follow native destinations and sub-hubs; never bypass navigation in journeys. */
fun revealDestination(compose: ComposeContentTestRule, label: String) {
    if (compose.onAllNodes(hasText(label) and hasClickAction()).fetchSemanticsNodes().isNotEmpty()) return
    fun open(text: String) {
        compose.waitUntil(90000) { compose.onAllNodes(hasText(text) and hasClickAction()).fetchSemanticsNodes().isNotEmpty() }
        val node=compose.onAllNodes(hasText(text) and hasClickAction())[0]
        try {node.performScrollTo()} catch(_:AssertionError) { /* Persistent navigation has no scroll parent. */ }
        node.performClick()
    }
    when(label) {
        "Cerrar sesión", "Mi expediente", "Privacidad y permisos", "Notificaciones" -> open("Cuenta")
        "Consultar horarios" -> {open("Campañas");open("Buscar horarios disponibles")}
        "Mis citas" -> open("Citas")
        "Escanear unidad", "Confirmar recolección", "Iniciar traslado", "Confirmar entrega física", "Registrar incidencia", "Capturar evidencia", "Cargar y verificar" -> {
            val step=compose.onAllNodes(hasText("Siguiente paso:",substring=true) and hasClickAction())[0]
            step.performScrollTo().performClick()
            if(label=="Capturar evidencia" || label=="Cargar y verificar") open("Evidencia")
        }
        "Consultar contactos y ruta de esta tarea" -> open("Contactos y ruta")
        "Autorizar ubicación durante esta tarea" -> open("Ubicación")
    }
}

fun presentationClick(compose: ComposeContentTestRule,label:String) {
    revealDestination(compose,label)
    compose.waitUntil(90000) {compose.onAllNodes(hasText(label) and hasClickAction() and isEnabled()).fetchSemanticsNodes().isNotEmpty()}
    val node=compose.onAllNodes(hasText(label) and hasClickAction())[0]
    try {node.performScrollTo()} catch(_:AssertionError) { /* Persistent navigation / dialog. */ }
    compose.onAllNodes(hasText(label) and hasClickAction())[0].performClick()
}
