package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.databinding.ActivityNewGivingBinding
import com.altarfunds.mobile.models.GivingCategory
import com.altarfunds.mobile.utils.CurrencyUtils
import com.altarfunds.mobile.utils.ValidationUtils
import kotlinx.coroutines.launch

class NewGivingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityNewGivingBinding
    private var selectedCategoryId: Int? = null
    private var selectedCategoryName: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNewGivingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Get category from intent if provided
        intent?.let {
            selectedCategoryId = it.getIntExtra("category_id", -1).takeIf { id -> id > 0 }
            selectedCategoryName = it.getStringExtra("category_name")
        }

        setupUI()
        loadGivingCategories()
        setupClickListeners()
    }

    private fun setupUI() {
        // Set toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "New Giving"

        // Set selected category if provided
        selectedCategoryName?.let { name ->
            binding.tvSelectedCategory.text = name
            binding.llSelectCategory.visibility = View.GONE
            binding.llSelectedCategory.visibility = View.VISIBLE
        }

        // Setup amount input
        binding.etAmount.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                updateAmountPreview()
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
    }

    private fun loadGivingCategories() {
        if (selectedCategoryId != null) return // Category already selected

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val response = com.altarfunds.mobile.api.ApiService.getApiInterface().getGivingCategories()

                if (response.isSuccessful) {
                    val responseBody = response.body()
                    if (responseBody?.success == true) {
                        val categories = responseBody.data ?: emptyList()
                        setupCategorySpinner(categories)
                        
                        // Debug: Log the categories
                        android.util.Log.d("NewGivingActivity", "Loaded ${categories.size} categories")
                        categories.forEach { category ->
                            android.util.Log.d("NewGivingActivity", "Category: ${category.name} (ID: ${category.id})")
                        }
                    } else {
                        val errorMessage = responseBody?.message ?: "Unknown error"
                        android.util.Log.e("NewGivingActivity", "API returned success=false: $errorMessage")
                        Toast.makeText(this@NewGivingActivity, "Failed to load categories: $errorMessage", Toast.LENGTH_LONG).show()
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    android.util.Log.e("NewGivingActivity", "HTTP error: ${response.code()} - $errorBody")
                    Toast.makeText(this@NewGivingActivity, "Failed to load categories: ${response.message()}", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                android.util.Log.e("NewGivingActivity", "Exception loading categories", e)
                Toast.makeText(this@NewGivingActivity, "Failed to load categories: ${e.message}", Toast.LENGTH_LONG).show()
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
        binding.btnSelectCategory.setOnClickListener {
            binding.llSelectCategory.visibility = View.GONE
            binding.llSelectedCategory.visibility = View.GONE
            binding.spinnerCategory.visibility = View.VISIBLE
        }

        binding.btnChangeCategory.setOnClickListener {
            binding.llSelectCategory.visibility = View.VISIBLE
            binding.llSelectedCategory.visibility = View.GONE
            binding.spinnerCategory.visibility = View.GONE
        }

        binding.btnProceedToPayment.setOnClickListener {
            proceedToPayment()
        }

        binding.btnCancel.setOnClickListener {
            finish()
        }
    }

    private fun updateAmountPreview() {
        val amountText = binding.etAmount.text.toString()
        if (amountText.isNotEmpty()) {
            try {
                val amount = amountText.toDouble()
                binding.tvAmountPreview.text = CurrencyUtils.formatCurrency(amount)
                binding.tvAmountPreview.visibility = View.VISIBLE
            } catch (e: NumberFormatException) {
                binding.tvAmountPreview.visibility = View.GONE
            }
        } else {
            binding.tvAmountPreview.visibility = View.GONE
        }
    }

    private fun proceedToPayment() {
        // Validate inputs
        val amountText = binding.etAmount.text.toString()
        val note = binding.etNote.text.toString().trim()

        if (!validateInputs(amountText)) {
            return
        }

        if (selectedCategoryId == null) {
            Toast.makeText(this, "Please select a giving category", Toast.LENGTH_SHORT).show()
            return
        }

        val amount = amountText.toDouble()

        // Create giving transaction
        createGivingTransaction(amount, note)
    }

    private fun validateInputs(amountText: String): Boolean {
        if (amountText.isEmpty()) {
            binding.etAmount.error = "Amount is required"
            return false
        }

        if (!ValidationUtils.isValidAmount(amountText)) {
            binding.etAmount.error = "Please enter a valid amount"
            return false
        }

        val amount = amountText.toDouble()
        if (amount <= 0) {
            binding.etAmount.error = "Amount must be greater than 0"
            return false
        }

        if (amount > 1000000) { // 1 million KES limit
            binding.etAmount.error = "Amount exceeds maximum limit"
            return false
        }

        return true
    }

    private fun createGivingTransaction(amount: Double, note: String) {
        binding.progressBar.visibility = View.VISIBLE
        binding.btnProceedToPayment.isEnabled = false

        lifecycleScope.launch {
            try {
                val transactionRequest = com.altarfunds.mobile.models.GivingTransactionRequest(
                    category = selectedCategoryId!!,
                    amount = amount,
                    payment_method = "mpesa",
                    note = note.ifEmpty { null },
                    is_anonymous = binding.switchAnonymous.isChecked
                )

                val response = com.altarfunds.mobile.api.ApiService.getApiInterface()
                    .createGivingTransaction(transactionRequest)

                if (response.isSuccessful) {
                    val responseBody = response.body()
                    if (responseBody?.success == true) {
                        val transaction = responseBody.data
                        if (transaction != null) {
                            // Initiate payment
                            initiatePayment(transaction.transaction_id, amount)
                        } else {
                            Toast.makeText(
                                this@NewGivingActivity,
                                "Transaction creation failed: No data returned",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    } else {
                        Toast.makeText(
                            this@NewGivingActivity,
                            "Transaction creation failed: ${responseBody?.message}",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    android.util.Log.e("NewGivingActivity", "Transaction creation error: ${response.code()} - $errorBody")
                    Toast.makeText(
                        this@NewGivingActivity,
                        "Failed to create transaction: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@NewGivingActivity,
                    "Failed to create transaction: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            } finally {
                binding.progressBar.visibility = View.GONE
                binding.btnProceedToPayment.isEnabled = true
            }
        }
    }

    private fun initiatePayment(transactionId: String, amount: Double) {
        lifecycleScope.launch {
            try {
                val paymentRequest = com.altarfunds.mobile.models.PaymentRequest(
                    giving_transaction_id = transactionId,
                    payment_method = "mpesa"
                )

                val response = com.altarfunds.mobile.api.ApiService.getApiInterface()
                    .initiatePayment(paymentRequest)

                if (response.isSuccessful && response.body() != null) {
                    val paymentResponse = response.body()!!
                    
                    // Navigate to payment processing activity
                    val intent = Intent(
                        this@NewGivingActivity,
                        PaymentProcessingActivity::class.java
                    ).apply {
                        putExtra("transaction_id", transactionId)
                        putExtra("amount", amount)
                        putExtra("payment_request_id", paymentResponse.payment_request.request_id)
                    }
                    startActivity(intent)
                    finish()
                } else {
                    Toast.makeText(
                        this@NewGivingActivity,
                        "Failed to initiate payment: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@NewGivingActivity,
                    "Failed to initiate payment: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
