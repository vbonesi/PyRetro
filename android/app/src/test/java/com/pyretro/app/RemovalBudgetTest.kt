package com.pyretro.app

import org.junit.Assert.*
import org.junit.Test

class RemovalBudgetTest {
    @Test fun `o Drive espera menos quando so o celular sera limpo`() {
        assertTrue(RemovalRules.driveBudgetMs("local") < RemovalRules.driveBudgetMs("both"))
        assertEquals(RemovalRules.driveBudgetMs("drive"), RemovalRules.driveBudgetMs("both"))
        assertTrue(RemovalRules.driveBudgetMs("local") <= 10_000)
    }
    @Test fun `prazo vencido`() {
        assertFalse(RemovalRules.expired(999, 1000)); assertTrue(RemovalRules.expired(1000, 1000)); assertTrue(RemovalRules.expired(2000, 1000))
    }
    @Test fun `escopo local gera previa confirmavel mesmo sem consultar o Drive`() {
        val file = RemovalFile("Zool.sfc", "id", 10, "abc")
        val plan = RemovalRules.plan("local", listOf(file), null)
        assertTrue(plan.blocked.isEmpty()); assertEquals(listOf(file), plan.local); assertTrue(plan.drive.isEmpty())
        assertEquals("Remover só deste celular", plan.confirmation)
        assertTrue(plan.warnings.any { it.contains("Drive não conferida") })     // sem o Drive, avisa que pode ser a última cópia
    }
    @Test fun `escopos com o Drive continuam exigindo a consulta`() {
        assertTrue(RemovalRules.plan("both", listOf(RemovalFile("a", "i", 1, "x")), null).blocked.isNotEmpty())
        assertTrue(RemovalRules.plan("drive", emptyList(), null).blocked.isNotEmpty())
    }
}
