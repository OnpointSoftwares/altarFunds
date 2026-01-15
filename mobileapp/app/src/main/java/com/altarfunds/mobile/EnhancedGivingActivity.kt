package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.tabs.TabLayout
import com.altarfunds.mobile.databinding.ActivityEnhancedGivingBinding
import com.altarfunds.mobile.utils.CurrencyUtils
import com.altarfunds.mobile.utils.ValidationUtils
import com.altarfunds.mobile.ui.adapters.TransactionHistoryAdapter
import com.altarfunds.mobile.ui.adapters.GivingCategoryAdapter
import com.altarfunds.mobile.ui.adapters.RecurringGivingAdapter
import com.altarfunds.mobile.models.*
import kotlinx.coroutines.launch

class EnhancedGivingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityEnhancedGivingBinding
    private var selectedCategoryId: Int? = null
    private var selectedCategoryName: String? = null
    private lateinit var givingHistoryAdapter: TransactionHistoryAdapter
    private lateinit var givingCategoryAdapter: GivingCategoryAdapter
    private lateinit var recurringGivingAdapter: RecurringGivingAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityEnhancedGivingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Get category from intent if provided
        intent?.let {
            selectedCategoryId = it.getIntExtra("category_id", -1).takeIf { id -> id > 0 }
            selectedCategoryName = it.getStringExtra("category_name")
        }

        setupUI()
        loadGivingCategories()
        setupClickListeners()
        loadRecentTransactions()
        loadRecurringGiving()
    }

    private fun setupUI() {
        // Set toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Give"

        // Set selected category if provided
        selectedCategoryName?.let { name ->
            binding.tvSelectedCategory.text = name
            binding.llSelectCategory.visibility = View.GONE
            binding.llSelectedCategory.visibility = View.VISIBLE
        }

        // Setup amount input with currency formatting
        binding.etAmount.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                updateAmountPreview()
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })

        // Setup payment method tabs
        setupPaymentMethodTabs()
    }

    private fun setupPaymentMethodTabs() {
        binding.tabPaymentMethod.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                tab?.let {
                    when (it.position) {
                        0 -> showMpesaPayment()
                        1 -> showAirtelPayment()
                        2 -> showCardPayment()
                        3 -> showUSSDPayment()
                        4 -> showQRPayment()
                    }
                }
            }
            override fun onTabUnselected(tab: TabLayout.Tab?) {}
            override fun onTabReselected(tab: TabLayout.Tab?) {}
        })
    }

    private fun loadGivingCategories() {
        if (selectedCategoryId != null) return // Category already selected

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val churchInfoResponse = com.altarfunds.mobile.api.ApiService.getApiInterface().getChurchInfo()
                
                if (churchInfoResponse.isSuccessful && churchInfoResponse.body() != null) {
                    val categories = churchInfoResponse.body()!!.giving_categories
                    setupCategorySpinner(categories)
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "Failed to load categories", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun setupCategorySpinner(categories: List<GivingCategory>) {
        val categoryNames = categories.map { it.name }
        val adapter = android.widget.ArrayAdapter(
            this,
            android.R.layout.simple_spinner_item,
            categoryNames
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerCategory.adapter = adapter

        binding.spinnerCategory.onItemSelectedListener = object :
            android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                selectedCategoryId = categories[position].id
                selectedCategoryName = categories[position].name
            }

            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        }
    }

    private fun setupClickListeners() {
        // Amount quick select buttons
        binding.btnAmount100.setOnClickListener { setAmount(100) }
        binding.btnAmount200.setOnClickListener { setAmount(200) }
        binding.btnAmount500.setOnClickListener { setAmount(500) }
        binding.btnAmount1000.setOnClickListener { setAmount(1000) }
        binding.btnAmount2000.setOnClickListener { setAmount(2000) }
        binding.btnAmount5000.setOnClickListener { setAmount(5000) }

        // Payment method buttons
        binding.btnInitiatePayment.setOnClickListener { initiatePayment() }
        binding.btnGenerateqr.setOnClickListener { generateQRCode() }
        binding.btnSetupRecurring.setOnClickListener { setupRecurringGiving() }

        // Anonymous giving toggle
        binding.switchAnonymous.setOnCheckedChangeListener { _, isChecked ->
            binding.tvAnonymousNote.visibility = if (isChecked) View.VISIBLE else View.GONE
        }

        // Recurring giving toggle
        binding.switchRecurring.setOnCheckedChangeListener { _, isChecked ->
            binding.llRecurringOptions.visibility = if (isChecked) View.VISIBLE else View.GONE
        }
    }

    private fun setAmount(amount: Int) {
        binding.etAmount.setText(amount.toString())
        updateAmountPreview()
    }

    private fun updateAmountPreview() {
        val amountStr = binding.etAmount.text.toString()
        if (amountStr.isNotEmpty()) {
            val amount = amountStr.toDoubleOrNull() ?: 0.0
            binding.tvAmountPreview.text = "KES %.2f".format(amount)
        }
    }

    private fun showMpesaPayment() {
        binding.llMpesaOptions.visibility = View.VISIBLE
        binding.llAirtelOptions.visibility = View.GONE
        binding.llCardOptions.visibility = View.GONE
        binding.llUssdOptions.visibility = View.GONE
        binding.llQrOptions.visibility = View.GONE
    }

    private fun showAirtelPayment() {
        binding.llMpesaOptions.visibility = View.GONE
        binding.llAirtelOptions.visibility = View.VISIBLE
        binding.llCardOptions.visibility = View.GONE
        binding.llUssdOptions.visibility = View.GONE
        binding.llQrOptions.visibility = View.GONE
    }

    private fun showCardPayment() {
        binding.llMpesaOptions.visibility = View.GONE
        binding.llAirtelOptions.visibility = View.GONE
        binding.llCardOptions.visibility = View.VISIBLE
        binding.llUssdOptions.visibility = View.GONE
        binding.llQrOptions.visibility = View.GONE
    }

    private fun showUSSDPayment() {
        binding.llMpesaOptions.visibility = View.GONE
        binding.llAirtelOptions.visibility = View.GONE
        binding.llCardOptions.visibility = View.GONE
        binding.llUssdOptions.visibility = View.VISIBLE
        binding.llQrOptions.visibility = View.GONE
    }

    private fun showQRPayment() {
        binding.llMpesaOptions.visibility = View.GONE
        binding.llAirtelOptions.visibility = View.GONE
        binding.llCardOptions.visibility = View.GONE
        binding.llUssdOptions.visibility = View.GONE
        binding.llQrOptions.visibility = View.VISIBLE
    }

    private fun initiatePayment() {
        val amount = getAmount()
        val paymentMethod = getSelectedPaymentMethod()
        val isAnonymous = binding.switchAnonymous.isChecked
        val isRecurring = binding.switchRecurring.isChecked

        if (!validateInput(amount)) return

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val givingRequest = ComprehensiveGivingRequest(
                    amount = amount,
                    category_id = selectedCategoryId ?: return@launch,
                    payment_method = paymentMethod,
                    phone_number = if (paymentMethod in listOf("mpesa", "airtel")) binding.etPhoneNumber.text.toString() else null,
                    is_anonymous = isAnonymous,
                    is_recurring = isRecurring,
                    recurring_frequency = if (isRecurring) getSelectedFrequency() else null,
                    recurring_start_date = if (isRecurring) getCurrentDateString() else null,
                    notes = binding.etNotes.text.toString().takeIf { it.isNotEmpty() }
                )

                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().initiateGiving(givingRequest)
                
                if (response.isSuccessful && response.body() != null) {
                    val paymentResponse = response.body()!!
                    handlePaymentInitiationSuccess(paymentResponse)
                } else {
                    Toast.makeText(this@EnhancedGivingActivity, "Payment initiation failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "Payment error: " + e.message, Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun generateQRCode() {
        val amount = getAmount()
        if (!validateInput(amount)) return

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val qrRequest = QRCodeRequest(
                    amount = amount,
                    category_id = selectedCategoryId ?: return@launch,
                    expires_in_hours = 24,
                    single_use = true,
                    notes = binding.etNotes.text.toString().takeIf { it.isNotEmpty() }
                )

                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().generateQRCode(qrRequest)
                
                if (response.isSuccessful && response.body() != null) {
                    val qrResponse = response.body()!!
                    showQRCodeDialog(qrResponse)
                } else {
                    Toast.makeText(this@EnhancedGivingActivity, "QR code generation failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "QR code error: " + e.message, Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun setupRecurringGiving() {
        val amount = getAmount()
        if (!validateInput(amount)) return

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val recurringRequest = RecurringGivingRequest(
                    amount = amount,
                    category_id = selectedCategoryId ?: return@launch,
                    frequency = getSelectedFrequency(),
                    start_date = getCurrentDateString(),
                    payment_method = "mpesa", // Default to MPesa for recurring
                    phone_number = binding.etPhoneNumber.text.toString().takeIf { it.isNotEmpty() },
                    is_anonymous = binding.switchAnonymous.isChecked
                )

                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().setupRecurringGiving(recurringRequest)
                
                if (response.isSuccessful && response.body() != null) {
                    val recurringResponse = response.body()!!
                    Toast.makeText(this@EnhancedGivingActivity, "Recurring giving setup successful", Toast.LENGTH_SHORT).show()
                    loadRecurringGiving() // Refresh the list
                } else {
                    Toast.makeText(this@EnhancedGivingActivity, "Recurring setup failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "Recurring setup error: " + e.message, Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun getAmount(): Double {
        return binding.etAmount.text.toString().toDoubleOrNull() ?: 0.0
    }

    private fun getSelectedPaymentMethod(): String {
        return when (binding.tabPaymentMethod.selectedTabPosition) {
            0 -> "mpesa"
            1 -> "airtel"
            2 -> "card"
            3 -> "ussd"
            4 -> "qr"
            else -> "mpesa"
        }
    }

    private fun getSelectedFrequency(): String {
        return when (binding.spinnerFrequency.selectedItemPosition) {
            0 -> "weekly"
            1 -> "monthly"
            2 -> "annual"
            else -> "monthly"
        }
    }

    private fun getCurrentDateString(): String {
        val dateFormat = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
        return dateFormat.format(java.util.Date())
    }

    private fun validateInput(amount: Double): Boolean {
        return when {
            amount <= 0 -> {
                Toast.makeText(this, "Please enter a valid amount", Toast.LENGTH_SHORT).show()
                false
            }
            selectedCategoryId == null -> {
                Toast.makeText(this, "Please select a category", Toast.LENGTH_SHORT).show()
                false
            }
            else -> true
        }
    }

    private fun handlePaymentInitiationSuccess(paymentResponse: PaymentInitiationResponse) {
        when (paymentResponse.payment_instructions?.method) {
            "mpesa" -> showMpesaInstructions(paymentResponse.payment_instructions)
            "airtel" -> showAirtelInstructions(paymentResponse.payment_instructions)
            "ussd" -> showUSSDInstructions(paymentResponse.payment_instructions)
            else -> {
                Toast.makeText(this, "Payment initiated successfully", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }

    private fun showMpesaInstructions(instructions: PaymentInstructions?) {
        val message = "M-Pesa Payment Instructions:\n" +
            "1. Go to M-Pesa menu\n" +
            "2. Select Lipa Na M-Pesa\n" +
            "3. Enter Paybill: " + (instructions?.reference_number ?: "123456") + "\n" +
            "4. Enter Account: " + (instructions?.reference_number ?: "ALTARFUNDS") + "\n" +
            "5. Enter Amount: KES " + binding.etAmount.text + "\n" +
            "6. Enter your M-Pesa PIN\n" +
            "7. Confirm transaction\n\n" +
            "Reference: " + instructions?.reference_number + "\n" +
            "Expires: " + instructions?.expires_at
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("M-Pesa Payment")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> }
            .show()
    }

    private fun showAirtelInstructions(instructions: PaymentInstructions?) {
        val message = "Airtel Money Payment:\n" +
            "1. Go to Airtel Money menu\n" +
            "2. Select Make Payment\n" +
            "3. Enter Business Number: " + (instructions?.reference_number ?: "123456") + "\n" +
            "4. Enter Amount: KES " + binding.etAmount.text + "\n" +
            "5. Enter your Airtel Money PIN\n" +
            "6. Confirm transaction\n\n" +
            "Reference: " + instructions?.reference_number + "\n" +
            "Expires: " + instructions?.expires_at
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Airtel Money Payment")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> }
            .show()
    }

    private fun showUSSDInstructions(instructions: PaymentInstructions?) {
        val message = "USSD Payment:\n" +
            "Dial: " + (instructions?.instructions ?: "*123456#") + "\n\n" +
            "Or follow these steps:\n" +
            "1. Dial *123456#\n" +
            "2. Select option 1 (Give)\n" +
            "3. Enter Amount: KES " + binding.etAmount.text + "\n" +
            "4. Enter your PIN\n" +
            "5. Confirm transaction\n\n" +
            "Confirmation Code: " + (instructions?.reference_number ?: "Check SMS")
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("USSD Payment")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> }
            .show()
    }

    private fun showQRCodeDialog(qrResponse: QRCodeResponse) {
        val message = "QR Code Generated Successfully!\n\n" +
            "Amount: KES " + binding.etAmount.text + "\n" +
            "Category: " + (selectedCategoryName ?: "General") + "\n" +
            "Expires: " + qrResponse.expires_at + "\n\n" +
            "Share this QR code or save it for later use."
        
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("QR Code Ready")
            .setMessage(message)
            .setPositiveButton("Share") { _, _ ->
                shareQRCode(qrResponse.qr_code_url ?: "")
            }
            .setNegativeButton("Save") { _, _ ->
                saveQRCode(qrResponse.qr_code_url ?: "")
            }
            .show()
    }

    private fun shareQRCode(qrCodeUrl: String) {
        val shareIntent = Intent().apply {
            action = Intent.ACTION_SEND
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, "Scan this QR code to give: $qrCodeUrl")
        }
        startActivity(Intent.createChooser(shareIntent, "Share QR Code"))
    }

    private fun saveQRCode(qrCodeUrl: String) {
        // Save QR code to device storage
        Toast.makeText(this, "QR code saved", Toast.LENGTH_SHORT).show()
    }

    private fun loadRecentTransactions() {
        lifecycleScope.launch {
            try {
                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().getGivingTransactions()
                
                if (response.isSuccessful && response.body() != null) {
                    val transactions = response.body()!!.results
                    setupRecyclerView(transactions)
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "Failed to load transactions", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadRecurringGiving() {
        lifecycleScope.launch {
            try {
                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().getRecurringGiving()
                
                if (response.isSuccessful && response.body() != null) {
                    val recurringGivings = response.body()!!.recurring_givings
                    setupRecurringRecyclerView(recurringGivings)
                }
            } catch (e: Exception) {
                Toast.makeText(this@EnhancedGivingActivity, "Failed to load recurring giving", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupRecyclerView(transactions: List<GivingTransactionResponse>) {
        givingHistoryAdapter = TransactionHistoryAdapter { transaction ->
            // Handle transaction click if needed
        }
        givingHistoryAdapter.submitList(transactions)
        binding.rvRecentTransactions.layoutManager = LinearLayoutManager(this)
        binding.rvRecentTransactions.adapter = givingHistoryAdapter
    }

    private fun setupRecurringRecyclerView(recurringGivings: List<RecurringGiving>) {
        recurringGivingAdapter = RecurringGivingAdapter(recurringGivings)
        binding.rvRecurringGiving.layoutManager = LinearLayoutManager(this)
        binding.rvRecurringGiving.adapter = recurringGivingAdapter
    }
}
