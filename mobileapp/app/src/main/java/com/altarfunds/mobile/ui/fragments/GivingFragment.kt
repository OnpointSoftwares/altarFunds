package com.altarfunds.mobile.ui.fragments

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.altarfunds.mobile.NewGivingActivity
import com.altarfunds.mobile.RecurringGivingActivity
import com.altarfunds.mobile.TransactionDetailsActivity
import com.altarfunds.mobile.TransactionHistoryActivity
import com.altarfunds.mobile.databinding.FragmentGivingBinding
import com.altarfunds.mobile.ui.adapters.GivingCategoryAdapter
import com.altarfunds.mobile.ui.adapters.RecentTransactionAdapter
import com.altarfunds.mobile.utils.CurrencyUtils
import kotlinx.coroutines.launch

class GivingFragment : Fragment() {

    private lateinit var binding: FragmentGivingBinding
    private lateinit var categoryAdapter: GivingCategoryAdapter
    private lateinit var recentTransactionAdapter: RecentTransactionAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentGivingBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupRecyclerViews()
        loadGivingData()
        setupClickListeners()
    }

    private fun setupRecyclerViews() {
        // Setup categories recycler view
        categoryAdapter = GivingCategoryAdapter { category ->
            // Handle category click - start giving flow
            startGivingFlow(category.id, category.name)
        }
        
        binding.rvCategories.apply {
            layoutManager = LinearLayoutManager(context, LinearLayoutManager.HORIZONTAL, false)
            adapter = categoryAdapter
        }

        // Setup recent transactions recycler view
        recentTransactionAdapter = RecentTransactionAdapter { transaction ->
            // Handle transaction click - show details
            showTransactionDetails(transaction.transaction_id)
        }
        
        binding.rvRecentTransactions.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = recentTransactionAdapter
        }
    }

    private fun loadGivingData() {
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                // Load giving summary
                val givingSummaryResponse = com.altarfunds.mobile.api.ApiService.getApiInterface().getGivingSummary()
                
                if (givingSummaryResponse.isSuccessful && givingSummaryResponse.body() != null) {
                    val summary = givingSummaryResponse.body()!!
                    updateUIWithSummary(summary)
                }
                
                // Load giving categories
                loadGivingCategories()
                
                // Load recent transactions
                loadRecentTransactions()
                
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load giving data", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun updateUIWithSummary(summary: com.altarfunds.mobile.models.GivingSummaryResponse) {
        binding.tvTotalGiving.text = CurrencyUtils.formatCurrency(summary.total_giving)
        binding.tvThisMonth.text = CurrencyUtils.formatCurrency(summary.this_month)
        binding.tvThisYear.text = CurrencyUtils.formatCurrency(summary.this_year)
        
        // Show last transaction if available
        summary.last_transaction?.let { lastTx ->
            binding.tvLastTransactionAmount.text = CurrencyUtils.formatCurrency(lastTx.amount)
            binding.tvLastTransactionCategory.text = lastTx.category
            binding.tvLastTransactionDate.text = formatDate(lastTx.date)
            binding.llLastTransaction.visibility = View.VISIBLE
        } ?: run {
            binding.llLastTransaction.visibility = View.GONE
        }
    }

    private fun loadGivingCategories() {
        lifecycleScope.launch {
            try {
                val churchInfoResponse = com.altarfunds.mobile.api.ApiService.getApiInterface().getChurchInfo()
                
                if (churchInfoResponse.isSuccessful && churchInfoResponse.body() != null) {
                    val categories = churchInfoResponse.body()!!.giving_categories
                    categoryAdapter.submitList(categories)
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load categories", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadRecentTransactions() {
        lifecycleScope.launch {
            try {
                val transactionsResponse = com.altarfunds.mobile.api.ApiService.getApiInterface()
                    .getGivingTransactions(page = 1, limit = 5)
                
                if (transactionsResponse.isSuccessful && transactionsResponse.body() != null) {
                    val transactions = transactionsResponse.body()!!.results
                    recentTransactionAdapter.submitList(transactions)
                    
                    if (transactions.isEmpty()) {
                        binding.tvNoTransactions.visibility = View.VISIBLE
                        binding.rvRecentTransactions.visibility = View.GONE
                    } else {
                        binding.tvNoTransactions.visibility = View.GONE
                        binding.rvRecentTransactions.visibility = View.VISIBLE
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load transactions", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupClickListeners() {
        binding.btnGiveNow.setOnClickListener {
            // Navigate to new giving activity
            startActivity(Intent(requireContext(), NewGivingActivity::class.java))
        }

        binding.btnRecurringGiving.setOnClickListener {
            // Navigate to recurring giving setup
            startActivity(Intent(requireContext(), RecurringGivingActivity::class.java))
        }

        binding.btnViewAllTransactions.setOnClickListener {
            // Navigate to transaction history
            startActivity(Intent(requireContext(), TransactionHistoryActivity::class.java))
        }
    }

    private fun startGivingFlow(categoryId: Int, categoryName: String) {
        val intent = Intent(requireContext(), NewGivingActivity::class.java).apply {
            putExtra("category_id", categoryId)
            putExtra("category_name", categoryName)
        }
        startActivity(intent)
    }

    private fun showTransactionDetails(transactionId: String) {
        val intent = Intent(requireContext(), TransactionDetailsActivity::class.java).apply {
            putExtra("transaction_id", transactionId)
        }
        startActivity(intent)
    }

    private fun formatDate(dateString: String): String {
        // Format date for display
        return try {
            val inputFormat = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.getDefault())
            val outputFormat = java.text.SimpleDateFormat("MMM dd, yyyy", java.util.Locale.getDefault())
            val date = inputFormat.parse(dateString)
            date?.let { outputFormat.format(it) } ?: dateString
        } catch (e: Exception) {
            dateString
        }
    }
}
