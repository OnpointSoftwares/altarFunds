package com.altarfunds.mobile.models

data class FinancialSummary(
    val totalIncome: Double,
    val totalExpenses: Double,
    val netIncome: Double,
    val totalDonations: Double,
    val budgetUtilization: Double,
    val period: String,
    val currency: String = "KES"
)
