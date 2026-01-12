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
import com.altarfunds.mobile.TransactionDetailsActivity
import com.altarfunds.mobile.databinding.FragmentHistoryBinding
import com.altarfunds.mobile.ui.adapters.TransactionHistoryAdapter
import com.altarfunds.mobile.utils.CurrencyUtils
import kotlinx.coroutines.launch

class HistoryFragment : Fragment() {

    private lateinit var binding: FragmentHistoryBinding
    private lateinit var transactionAdapter: TransactionHistoryAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentHistoryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupRecyclerView()
        setupFilters()
        loadTransactions()
    }

    private fun setupRecyclerView() {
        transactionAdapter = TransactionHistoryAdapter { transaction ->
            // Handle transaction click
            showTransactionDetails(transaction.transaction_id)
        }
        
        binding.rvTransactions.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = transactionAdapter
        }
    }

    private fun setupFilters() {
        // Setup filter chips
        binding.chipAll.setOnClickListener {
            filterTransactions("all")
        }
        
        binding.chipCompleted.setOnClickListener {
            filterTransactions("completed")
        }
        
        binding.chipPending.setOnClickListener {
            filterTransactions("pending")
        }
        
        binding.chipFailed.setOnClickListener {
            filterTransactions("failed")
        }
        
        // Setup date range filter
        binding.btnFilterDate.setOnClickListener {
            // Show date range picker
            showDateRangePicker()
        }
    }

    private fun loadTransactions() {
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val transactionsResponse = com.altarfunds.mobile.api.ApiService.getApiInterface()
                    .getGivingTransactions(page = 1, limit = 20)
                
                if (transactionsResponse.isSuccessful && transactionsResponse.body() != null) {
                    val transactions = transactionsResponse.body()!!.results
                    transactionAdapter.submitList(transactions)
                    
                    updateSummaryStats(transactions)
                    
                    if (transactions.isEmpty()) {
                        binding.tvNoTransactions.visibility = View.VISIBLE
                        binding.rvTransactions.visibility = View.GONE
                    } else {
                        binding.tvNoTransactions.visibility = View.GONE
                        binding.rvTransactions.visibility = View.VISIBLE
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load transactions", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun filterTransactions(status: String) {
        // Update UI to show selected filter
        updateFilterUI(status)
        
        // Filter transactions
        lifecycleScope.launch {
            try {
                val transactionsResponse = com.altarfunds.mobile.api.ApiService.getApiInterface()
                    .getGivingTransactions(page = 1, limit = 20)
                
                if (transactionsResponse.isSuccessful && transactionsResponse.body() != null) {
                    val allTransactions = transactionsResponse.body()!!.results
                    val filteredTransactions = if (status == "all") {
                        allTransactions
                    } else {
                        allTransactions.filter { it.status == status }
                    }
                    
                    transactionAdapter.submitList(filteredTransactions)
                    updateSummaryStats(filteredTransactions)
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to filter transactions", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun updateFilterUI(selectedStatus: String) {
        // Reset all chips
        binding.chipAll.isChecked = selectedStatus == "all"
        binding.chipCompleted.isChecked = selectedStatus == "completed"
        binding.chipPending.isChecked = selectedStatus == "pending"
        binding.chipFailed.isChecked = selectedStatus == "failed"
    }

    private fun updateSummaryStats(transactions: List<com.altarfunds.mobile.models.GivingTransactionResponse>) {
        val totalAmount = transactions
            .filter { it.status == "completed" }
            .sumOf { it.amount }
        
        val completedCount = transactions.count { it.status == "completed" }
        val pendingCount = transactions.count { it.status == "pending" }
        
        binding.tvTotalAmount.text = CurrencyUtils.formatCurrency(totalAmount)
        binding.tvCompletedCount.text = completedCount.toString()
        binding.tvPendingCount.text = pendingCount.toString()
    }

    private fun showDateRangePicker() {
        // Implement date range picker
        Toast.makeText(requireContext(), "Date range filter coming soon", Toast.LENGTH_SHORT).show()
    }

    private fun showTransactionDetails(transactionId: String) {
        val intent = Intent(requireContext(), TransactionDetailsActivity::class.java).apply {
            putExtra("transaction_id", transactionId)
        }
        startActivity(intent)
    }
}
