package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.altarfunds.mobile.adapters.TransactionAdapter
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.databinding.ActivityMemberDashboardModernBinding
import com.altarfunds.mobile.models.GivingTransaction
import com.altarfunds.mobile.utils.CurrencyUtils
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.launch

class MemberDashboardModernActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMemberDashboardModernBinding
    private lateinit var transactionAdapter: TransactionAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMemberDashboardModernBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        loadDashboardData()
        setupClickListeners()
    }

    private fun setupUI() {
        // Set toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Financial Dashboard"

        // Setup RecyclerView
        transactionAdapter = TransactionAdapter()
        binding.recyclerRecentTransactions.apply {
            layoutManager = LinearLayoutManager(this@MemberDashboardModernActivity)
            adapter = transactionAdapter
        }

        // Setup Bottom Navigation
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_dashboard -> {
                    // Already on dashboard - show dashboard content
                    showDashboardContent()
                }
                R.id.nav_giving -> {
                    // Navigate to giving activity/fragment
                    startActivity(Intent(this, NewGivingActivity::class.java))
                }
                R.id.nav_churches -> {
                    // Navigate to churches
                    startActivity(Intent(this, ChurchSearchActivity::class.java))
                }
                R.id.nav_devotionals -> {
                    // Navigate to devotionals
                    startActivity(Intent(this, DevotionalsActivity::class.java))
                }
                R.id.nav_profile -> {
                    // Navigate to profile
                    startActivity(Intent(this, EditProfileActivity::class.java))
                }
            }
            true
        }

        // View All Transactions
        binding.btnViewAll.setOnClickListener {
            startActivity(Intent(this, TransactionHistoryActivity::class.java))
        }
    }

    private fun showDashboardContent() {
        loadDashboardData()
    }

    private fun loadDashboardData() {
        binding.progressBar?.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                // Load user profile
                loadUserProfile()
                
                // Load financial summary
                loadFinancialSummary()
                
                // Load recent transactions
                loadRecentTransactions()

                binding.progressBar?.visibility = View.GONE
            } catch (e: Exception) {
                binding.progressBar?.visibility = View.GONE
                showError("Error loading data: ${e.message}")
            }
        }
    }

    private suspend fun loadUserProfile() {
        try {
            val response = ApiService.getApiInterface().getProfile()
            if (response.isSuccessful && response.body()?.success == true) {
                val user = response.body()?.data
                binding.userName?.text = "${user?.first_name} ${user?.last_name}"
                //binding.userName?.text = user?.church?.name ?: "No church"
            }
        } catch (e: Exception) {
            // Silently fail for profile load
        }
    }

    private suspend fun loadFinancialSummary() {
        try {
            val response = ApiService.getApiInterface().getFinancialSummaryBackend()
            if (response.isSuccessful && response.body()?.success == true) {
                val summary = response.body()?.data
                
                binding.totalIncome?.text = CurrencyUtils.formatCurrency(summary?.total_income ?: 0.0)
                binding.totalExpenses?.text = CurrencyUtils.formatCurrency(summary?.total_expenses ?: 0.0)
                binding.netBalance?.text = CurrencyUtils.formatCurrency(summary?.net_income ?: 0.0)
            }
        } catch (e: Exception) {
            // Show default values on error
            binding.totalIncome?.text = CurrencyUtils.formatCurrency(0.0)
            binding.totalExpenses?.text = CurrencyUtils.formatCurrency(0.0)
            binding.netBalance?.text = CurrencyUtils.formatCurrency(0.0)
        }
    }

    private suspend fun loadRecentTransactions() {
        try {
            val response = ApiService.getApiInterface().getGivingHistoryBackend()
            if (response.isSuccessful && response.body()?.success == true) {
                val history = response.body()?.data
                val transactions = history?.givings?.take(5) ?: emptyList()
                
                if (transactions.isEmpty()) {
                    binding.recyclerRecentTransactions?.visibility = View.GONE
                    binding.noTransactionsText?.visibility = View.VISIBLE
                } else {
                    binding.recyclerRecentTransactions?.visibility = View.VISIBLE
                    binding.noTransactionsText?.visibility = View.GONE
                    transactionAdapter.submitList(transactions as List<GivingTransaction?>?)
                }
            }
        } catch (e: Exception) {
            binding.recyclerRecentTransactions?.visibility = View.GONE
            binding.noTransactionsText?.visibility = View.VISIBLE
        }
    }
    
    private fun showError(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }

    private fun setupClickListeners() {
        // New Giving FAB
        binding.fabAddTransaction.setOnClickListener {
            startActivity(Intent(this, NewGivingActivity::class.java))
        }

        // New Giving Button
        binding.btnNewGiving.setOnClickListener {
            startActivity(Intent(this, NewGivingActivity::class.java))
        }

        // View Reports Button
        binding.btnViewReports.setOnClickListener {
            // Navigate to reports activity (to be created)
            Toast.makeText(this, "Reports feature coming soon", Toast.LENGTH_SHORT).show()
        }

        // View All Transactions
        binding.btnViewAll.setOnClickListener {
            startActivity(Intent(this, TransactionHistoryActivity::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        // Refresh data when activity resumes
        loadDashboardData()
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressed()
        return true
    }
}
