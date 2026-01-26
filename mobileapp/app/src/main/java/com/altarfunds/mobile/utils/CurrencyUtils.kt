package com.altarfunds.mobile.utils

import java.text.NumberFormat
import java.util.*

object CurrencyUtils {
    
    private const val CURRENCY_CODE = "KES"
    private const val LOCALE_COUNTRY = "KE"
    
    fun formatCurrency(amount: Double): String {
        val format = NumberFormat.getCurrencyInstance(Locale(LOCALE_COUNTRY))
        format.currency = Currency.getInstance(CURRENCY_CODE)
        return format.format(amount)
    }
    
    fun formatCurrencyWithoutSymbol(amount: Double): String {
        return String.format(Locale.US, "%,.2f", amount)
    }
    
    fun parseCurrencyAmount(amountString: String): Double? {
        return try {
            // Remove currency symbols and commas
            val cleanAmount = amountString.replace(Regex("[^0-9.]"), "")
            cleanAmount.toDouble()
        } catch (e: NumberFormatException) {
            null
        }
    }
    
    fun getCurrencySymbol(): String {
        return Currency.getInstance(CURRENCY_CODE).symbol
    }
    
    fun isValidAmount(amount: String): Boolean {
        return try {
            val cleanAmount = amount.replace(Regex("[^0-9.]"), "")
            val value = cleanAmount.toDouble()
            value > 0 && value <= 1000000 // 1 million KES limit
        } catch (e: NumberFormatException) {
            false
        }
    }
}
