package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class SaveReviewTextTest {
    @Test fun responseAndFailedAttemptBothRetainDriveOrigin() {
        val success=SaveReviewText.forComparison(listOf("drive:fixture"),false,true)
        assertEquals("Iguais no celular e no Drive.",success.equal)
        assertNull(success.warning)
        for(configured in listOf(false,true)) {
            val failure=SaveReviewText.forComparison(null,true,configured)
            assertTrue(failure.drive)
            assertTrue(failure.warning!!.contains("Drive"))
            assertFalse((failure.notice+failure.warning).contains("notebook",ignoreCase=true))
        }
    }
    @Test fun notebookFailuresRemainActionableAndEmptyDrivePlanStaysDrive() {
        assertEquals("Iguais no celular e no notebook.",SaveReviewText.forComparison(listOf("pc-root"),false,true).equal)
        assertEquals("Configure o notebook para comparar.",SaveReviewText.forComparison(null,false,false).warning)
        assertTrue(SaveReviewText.forComparison(null,false,true).warning!!.startsWith("Notebook offline"))
        assertEquals("Iguais no celular e no Drive.",SaveReviewText.forComparison(emptyList(),true,false).equal)
    }
}
