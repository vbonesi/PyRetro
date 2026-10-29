package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class CloudFeedbackTest {
    @Test fun groupFailuresAndFileFailuresCannotBecomeSuccess() {
        val feedback=CloudFeedback.batch { mapOf("retro" to Result.failure(IllegalStateException("permissão expirada")),
            "psp" to Result.success(listOf(CloudResult("a","push",true),CloudResult("b","pull",false,"checksum")))) }
        assertFalse(feedback.complete);assertTrue(feedback.message.contains("2 erro(s)"))
        assertTrue(feedback.message.contains("permissão expirada"));assertTrue(feedback.message.contains("checksum"))
        assertFalse(feedback.message.contains("Tudo em dia"))
    }
    @Test fun thrownFailureAndUnresolvedConflictStayPending() {
        assertFalse(CloudFeedback.batch { error("sem rede") }.complete)
        assertFalse(CloudFeedback.batch { mapOf("retro" to Result.success(listOf(CloudResult("a","conflict",false,conflict=mapOf("sha" to listOf("pc")))))) }.complete)
        assertFalse(CloudFeedback.resolve("Mantido") { error("Drive indisponível") }.complete)
        assertFalse(CloudFeedback.resolve("Mantido") { CloudResult("a","resolve",false,"arquivo mudou") }.complete)
    }
    @Test fun successIsOnlyReportedAfterTheActionSucceeded() {
        var called=false
        val feedback=CloudFeedback.resolve("Mantido") { called=true;CloudResult("a","resolve",true) }
        assertTrue(called);assertTrue(feedback.complete);assertEquals("Mantido",feedback.message)
        assertTrue(CloudFeedback.batch { mapOf("retro" to Result.success(listOf(CloudResult("a","push",true)))) }.complete)
    }
}
