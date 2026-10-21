package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class StatusRulesTest {
    private val root=GrantIdentity("local.provider","primary:Jogos",true)
    @Test fun missingSelectionAndRevokedGrantAreDifferent() {
        assertEquals(FolderAccess.UNSELECTED,StatusRules.access(null,emptyList()))
        assertEquals(FolderAccess.RESELECT,StatusRules.access(root,emptyList()))
        assertEquals(FolderAccess.RESELECT,StatusRules.access(root,listOf(SavedGrant(root,false,true))))
    }
    @Test fun readOnlyDoesNotPromiseDownloadOrSyncWrites() {
        assertEquals(FolderAccess.READ_ONLY,StatusRules.access(root,listOf(SavedGrant(root,true,false))))
        assertEquals(FolderAccess.READ_WRITE,StatusRules.access(root,listOf(SavedGrant(root,true,true))))
    }
    @Test fun opaqueIdsDoNotGrantSiblingsOrOtherProviders() {
        val grant=listOf(SavedGrant(root,true,true))
        for(target in listOf(root.copy(authority="other.provider"),root.copy(id="primary:Jogos-backup"),root.copy(id="primary:Jogos/FC"),root.copy(tree=false)))
            assertEquals(FolderAccess.RESELECT,StatusRules.access(target,grant))
    }
    @Test fun unrelatedGrantsCannotSupplyMissingWritePermission() {
        assertEquals(FolderAccess.READ_ONLY,StatusRules.access(root,listOf(SavedGrant(root,true,false),SavedGrant(root.copy(id="elsewhere"),true,true))))
    }
    @Test fun fileSyncObservationIsInvalidatedByEitherEndpointChange() {
        assertTrue(StatusRules.currentObservation("https://pc","tree-a","https://pc","tree-a"))
        assertFalse(StatusRules.currentObservation("https://old","tree-a","https://pc","tree-a"))
        assertFalse(StatusRules.currentObservation("https://pc","tree-a","https://pc","tree-b"))
        assertFalse(StatusRules.currentObservation("","tree-a","","tree-a"))
    }
    @Test fun conflictBadgeOnlyAppliesToThePayloadActuallyCompared() {
        assertTrue(StatusRules.conflictStillApplies("old-progress","old-progress"))
        assertFalse(StatusRules.conflictStillApplies("edited-progress","old-progress"))
        assertFalse(StatusRules.conflictStillApplies("old-progress",null))
    }
}
