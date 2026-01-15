package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.altarfunds.mobile.data.PreferencesManager
import com.altarfunds.mobile.databinding.ActivitySettingsBinding
import com.altarfunds.mobile.models.ChurchInfo
import com.altarfunds.mobile.ui.adapters.ChurchInfoAdapter
import kotlinx.coroutines.launch

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var preferencesManager: PreferencesManager
    private lateinit var churchAdapter: ChurchInfoAdapter
    private var availableChurches: List<ChurchInfo> = emptyList()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        preferencesManager = (application as AltarFundsApp).preferencesManager
        
        setupToolbar()
        setupRecyclerView()
        loadSettings()
        setupClickListeners()
    }

    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            setDisplayShowHomeEnabled(true)
            title = "Settings"
        }
        binding.toolbar.setNavigationOnClickListener {
            onBackPressed()
        }
    }

    private fun setupRecyclerView() {
        churchAdapter = ChurchInfoAdapter { church ->
            selectChurch(church)
        }
        
        binding.rvChurches.apply {
            layoutManager = LinearLayoutManager(this@SettingsActivity)
            adapter = churchAdapter
        }
    }

    private fun loadSettings() {
        loadCurrentChurch()
        loadAvailableChurches()
        loadNotificationSettings()
        loadPaymentSettings()
    }

    private fun loadCurrentChurch() {
        val currentChurch = preferencesManager.getCurrentChurch()
        currentChurch?.let {
            binding.tvCurrentChurchName.text = it.name
            binding.tvCurrentChurchCode.text = it.code
        }
        
        // Test method call to verify PreferencesManager is working
        android.util.Log.d("SettingsActivity", "PreferencesManager test: ${preferencesManager.testMethod()}")
    }

    private fun loadAvailableChurches() {
        binding.progressBar.visibility = android.view.View.VISIBLE
        
        lifecycleScope.launch {
            try {
                // For demo, we'll create some sample churches
                // In real app, this would come from API
                availableChurches = listOf(
                    ChurchInfo(
                        id = "1",
                        name = "Grace Community Church",
                        code = "GCC001",
                        description = "A vibrant community of believers",
                        logo = null,
                        is_verified = true,
                        is_active = true
                    ),
                    ChurchInfo(
                        id = "2", 
                        name = "Victory Chapel",
                        code = "VCH002",
                        description = "Where faith meets action",
                        logo = null,
                        is_verified = true,
                        is_active = true
                    ),
                    ChurchInfo(
                        id = "3",
                        name = "Living Waters Church",
                        code = "LWC003", 
                        description = "Flowing in the spirit",
                        logo = null,
                        is_verified = true,
                        is_active = true
                    )
                )
                
                churchAdapter.submitList(availableChurches)
                
            } catch (e: Exception) {
                Toast.makeText(this@SettingsActivity, "Failed to load churches", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = android.view.View.GONE
            }
        }
    }

    private fun loadNotificationSettings() {
        binding.switchNotifications.isChecked = preferencesManager.getNotificationsEnabled()
        binding.switchEmailNotifications.isChecked = preferencesManager.getEmailNotificationsEnabled()
        binding.switchPushNotifications.isChecked = preferencesManager.getPushNotificationsEnabled()
    }

    private fun loadPaymentSettings() {
        binding.switchSavePaymentMethod.isChecked = preferencesManager.getSavePaymentMethodEnabled()
        binding.switchBiometricAuth.isChecked = preferencesManager.getBiometricAuthEnabled()
    }

    private fun setupClickListeners() {
        // Church switching
        binding.btnSwitchChurch.setOnClickListener {
            toggleChurchSelection()
        }

        // Notification settings
        binding.switchNotifications.setOnCheckedChangeListener { _, isChecked ->
            preferencesManager.setNotificationsEnabled(isChecked)
            binding.llNotificationOptions.visibility = if (isChecked) android.view.View.VISIBLE else android.view.View.GONE
        }

        binding.switchEmailNotifications.setOnCheckedChangeListener { _, isChecked ->
            preferencesManager.setEmailNotificationsEnabled(isChecked)
        }

        binding.switchPushNotifications.setOnCheckedChangeListener { _, isChecked ->
            preferencesManager.setPushNotificationsEnabled(isChecked)
        }

        // Payment settings
        binding.switchSavePaymentMethod.setOnCheckedChangeListener { _, isChecked ->
            preferencesManager.setSavePaymentMethodEnabled(isChecked)
        }

        binding.switchBiometricAuth.setOnCheckedChangeListener { _, isChecked ->
            preferencesManager.setBiometricAuthEnabled(isChecked)
            if (isChecked) {
                setupBiometricAuth()
            }
        }

        // Other settings
        binding.btnLanguage.setOnClickListener {
            showLanguageDialog()
        }

        binding.btnCurrency.setOnClickListener {
            showCurrencyDialog()
        }

        binding.btnPrivacyPolicy.setOnClickListener {
            openPrivacyPolicy()
        }

        binding.btnTermsOfService.setOnClickListener {
            openTermsOfService()
        }

        binding.btnAbout.setOnClickListener {
            showAboutDialog()
        }

        binding.btnClearCache.setOnClickListener {
            clearCache()
        }

        binding.btnExportData.setOnClickListener {
            exportData()
        }
    }

    private fun toggleChurchSelection() {
        if (binding.rvChurches.visibility == android.view.View.GONE) {
            binding.rvChurches.visibility = android.view.View.VISIBLE
            binding.btnSwitchChurch.text = "Hide Churches"
        } else {
            binding.rvChurches.visibility = android.view.View.GONE
            binding.btnSwitchChurch.text = "Switch Church"
        }
    }

    private fun selectChurch(church: ChurchInfo) {
        preferencesManager.setCurrentChurch(church)
        loadCurrentChurch()
        
        Toast.makeText(this, "Switched to ${church.name}", Toast.LENGTH_SHORT).show()
        
        // Hide church selection after selection
        binding.rvChurches.visibility = android.view.View.GONE
        binding.btnSwitchChurch.text = "Switch Church"
        
        // Optionally restart app to refresh data
        restartApp()
    }

    private fun setupBiometricAuth() {
        // Implementation for biometric authentication setup
        Toast.makeText(this, "Biometric authentication setup coming soon", Toast.LENGTH_SHORT).show()
    }

    private fun showLanguageDialog() {
        val languages = arrayOf("English", "Spanish", "French", "Portuguese")
        val currentLanguage = preferencesManager.getLanguage()
        val currentIndex = languages.indexOf(currentLanguage).takeIf { it >= 0 } ?: 0
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Select Language")
            .setSingleChoiceItems(languages, currentIndex) { dialog, which ->
                preferencesManager.setLanguage(languages[which])
                dialog.dismiss()
                restartApp()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showCurrencyDialog() {
        val currencies = arrayOf("KES", "USD", "EUR", "GBP")
        val currentCurrency = preferencesManager.getCurrency()
        val currentIndex = currencies.indexOf(currentCurrency).takeIf { it >= 0 } ?: 0
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Select Currency")
            .setSingleChoiceItems(currencies, currentIndex) { dialog, which ->
                preferencesManager.setCurrency(currencies[which])
                dialog.dismiss()
                Toast.makeText(this, "Currency changed to ${currencies[which]}", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun openPrivacyPolicy() {
        val intent = Intent(this, WebViewActivity::class.java).apply {
            putExtra("title", "Privacy Policy")
            putExtra("url", "https://altarfunds.com/privacy")
        }
        startActivity(intent)
    }

    private fun openTermsOfService() {
        val intent = Intent(this, WebViewActivity::class.java).apply {
            putExtra("title", "Terms of Service")
            putExtra("url", "https://altarfunds.com/terms")
        }
        startActivity(intent)
    }

    private fun showAboutDialog() {
        val aboutText = """
            AltarFunds Mobile App
            Version: 1.0.0
            
            Church Giving Made Simple
            
            © 2024 AltarFunds
            All rights reserved
        """.trimIndent()
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("About AltarFunds")
            .setMessage(aboutText)
            .setPositiveButton("OK", null)
            .show()
    }

    private fun clearCache() {
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Clear Cache")
            .setMessage("This will clear all cached data. Are you sure?")
            .setPositiveButton("Clear") { _, _ ->
                try {
                    cacheDir.deleteRecursively()
                    Toast.makeText(this, "Cache cleared successfully", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(this, "Failed to clear cache", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun exportData() {
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Export Data")
            .setMessage("Export your giving history and personal data?")
            .setPositiveButton("Export") { _, _ ->
                // Implementation for data export
                Toast.makeText(this, "Data export coming soon", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun restartApp() {
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressed()
        return true
    }
}
