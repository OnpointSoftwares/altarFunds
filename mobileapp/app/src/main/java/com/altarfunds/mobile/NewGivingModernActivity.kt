package com.altarfunds.mobile

import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.data.PreferencesManager
import com.altarfunds.mobile.databinding.ActivityNewGivingBinding
import com.altarfunds.mobile.services.PaystackPaymentService
import com.altarfunds.mobile.utils.CurrencyUtils
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.launch

class NewGivingModernActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityNewGivingBinding
    private lateinit var paymentService: PaystackPaymentService
    private lateinit var preferencesManager: PreferencesManager
    
    private val givingTypes = listOf("tithe", "offering", "donation", "building_fund", "mission")
    private val givingTypeNames = listOf("Tithe", "Offering", "Donation", "Building Fund", "Mission")
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNewGivingBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        preferencesManager = PreferencesManager(this)
        paymentService = PaystackPaymentService(this)
        
        setupUI()
        loadGivingCategories()
    }
    
    private fun setupUI() {
        // Setup toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Make a Giving"
        
        // Setup giving type dropdown
        val adapter = ArrayAdapter(this, android.R.layout.simple_dropdown_item_1line, givingTypeNames)
        binding.spinnerCategory?.setAdapter(adapter)
        
        // Setup submit button
        binding.btnProceedToPayment?.setOnClickListener {
            processPayment()
        }
        
        binding.btnCancel?.setOnClickListener {
            finish()
        }
    }
    
    private fun loadGivingCategories() {
        binding.progressBar?.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val response = ApiService.getApiInterface().getGivingCategories()
                if (response.isSuccessful && response.body()?.success == true) {
                    val categories = response.body()?.data ?: emptyList()
                    val categoryNames = categories.map { it.name }
                    
                    val adapter = ArrayAdapter(
                        this@NewGivingModernActivity,
                        android.R.layout.simple_dropdown_item_1line,
                        categoryNames
                    )
                    // Update to use correct view ID
                    binding.spinnerCategory?.setAdapter(adapter)
                }
            } catch (e: Exception) {
                // Use default categories if API fails
            } finally {
                binding.progressBar?.visibility = View.GONE
            }
        }
    }
    
    private fun processPayment() {
        val amountStr = binding.etAmount?.text?.toString() ?: ""
        val givingTypeText = binding.tvSelectedCategory?.text?.toString() ?: ""
        val givingTypeIndex = givingTypeNames.indexOf(givingTypeText)
        val givingType = if (givingTypeIndex >= 0) givingTypes[givingTypeIndex] else "offering"
        val note = binding.etNote?.text?.toString() ?: ""
        
        // Validation
        if (amountStr.isEmpty()) {
            binding.etAmount?.error = "Please enter amount"
            return
        }
        
        val amount = amountStr.toDoubleOrNull()
        if (amount == null || amount <= 0) {
            binding.etAmount?.error = "Please enter valid amount"
            return
        }
        
        if (givingTypeText.isEmpty()) {
            Toast.makeText(this, "Please select giving type", Toast.LENGTH_SHORT).show()
            return
        }
        
        // Get church ID from preferences
        val churchId = getChurchId()
        if (churchId == 0) {
            showNoChurchDialog()
            return
        }
        
        // Show confirmation dialog
        showConfirmationDialog(amount, givingType, churchId, note)
    }
    
    private fun getChurchId(): Int {
        // Try to get church ID from preferences or user profile
        // For now, return a default value - you should implement proper church ID retrieval
        return try {
            preferencesManager.churchId
        } catch (e: Exception) {
            1 // Default church ID for testing
        } as Int
    }
    
    private fun showConfirmationDialog(amount: Double, givingType: String, churchId: Int, note: String?) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Confirm Payment")
            .setMessage("You are about to give ${CurrencyUtils.formatCurrency(amount)} as ${givingType.replace("_", " ").replaceFirstChar { it.uppercase() }}")
            .setPositiveButton("Proceed") { _, _ ->
                initiatePayment(amount, givingType, churchId, note)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun initiatePayment(amount: Double, givingType: String, churchId: Int, note: String?) {
        binding.progressBar?.visibility = View.VISIBLE
        binding.btnProceedToPayment?.isEnabled = false
        
        paymentService.initiatePayment(
            amount = amount,
            givingType = givingType,
            churchId = churchId,
            onSuccess = { reference ->
                runOnUiThread {
                    binding.progressBar?.visibility = View.GONE
                    binding.btnProceedToPayment?.isEnabled = true
                    
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Payment Successful!")
                        .setMessage("Your giving of ${CurrencyUtils.formatCurrency(amount)} has been received.\n\nReference: $reference")
                        .setPositiveButton("OK") { _, _ ->
                            finish()
                        }
                        .setCancelable(false)
                        .show()
                }
            },
            onError = { error ->
                runOnUiThread {
                    binding.progressBar?.visibility = View.GONE
                    binding.btnProceedToPayment?.isEnabled = true
                    
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Payment Failed")
                        .setMessage(error)
                        .setPositiveButton("OK", null)
                        .show()
                }
            }
        )
    }
    
    private fun showNoChurchDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle("No Church")
            .setMessage("You need to join a church before you can make a giving.")
            .setPositiveButton("Find Church") { _, _ ->
                startActivity(android.content.Intent(this, ChurchSearchActivity::class.java))
                finish()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
    
    override fun onDestroy() {
        super.onDestroy()
        paymentService.cancelVerification()
    }
}
