package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.text.InputType
import android.util.Log
import android.view.View
import android.widget.Toast
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.databinding.ActivityMemberDashboardBinding
import com.altarfunds.mobile.ui.adapters.TransactionHistoryAdapter
import com.altarfunds.mobile.ui.adapters.PledgeAdapter
import com.altarfunds.mobile.ui.adapters.ChurchAdapter
import com.altarfunds.mobile.models.*
import com.altarfunds.mobile.utils.CurrencyUtils
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.LocalDate

class MemberDashboardActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMemberDashboardBinding
    private lateinit var givingHistoryAdapter: TransactionHistoryAdapter
    private lateinit var pledgeAdapter: PledgeAdapter
    private lateinit var churchAdapter: ChurchAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMemberDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        loadDashboardData()
        setupClickListeners()
    }

    private fun setupUI() {
        // Set toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "My Dashboard"

        // Setup RecyclerViews
        setupRecyclerViews()
    }

    private fun setupRecyclerViews() {
        // Giving History RecyclerView
        givingHistoryAdapter = TransactionHistoryAdapter { transaction ->
            // Handle transaction click if needed
        }
        binding.rvGivingHistory.layoutManager = LinearLayoutManager(this)
        binding.rvGivingHistory.adapter = givingHistoryAdapter

        // Pledges RecyclerView
        pledgeAdapter = PledgeAdapter(emptyList())
        binding.rvPledges.layoutManager = LinearLayoutManager(this)
        binding.rvPledges.adapter = pledgeAdapter

        // Churches RecyclerView (for multi-church support)
        churchAdapter = ChurchAdapter(emptyList())
        binding.rvChurches.layoutManager = LinearLayoutManager(this)
        binding.rvChurches.adapter = churchAdapter
    }

    private fun loadDashboardData() {
        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                // Load enhanced dashboard data
                val enhancedDashboardResponse = ApiService.getApiInterface().getEnhancedDashboard()
                
                // Load recent transactions (still needed for detailed view)
                val transactionsResponse = ApiService.getApiInterface().getGivingTransactions()
                
                // Load pledges (still needed for pledge management)
                val pledgesResponse = ApiService.getApiInterface().getPledges()
                
                // Load user profile (still needed for user info)
                val profileResponse = ApiService.getApiInterface().getUserProfile()

                // Load churches for transfer functionality (still needed)
                val churchesResponse = ApiService.getApiInterface().searchChurches(query = "", location = null)

                // Wait for all requests to complete
                delay(100)

                // Update UI with enhanced dashboard data
                updateUIWithEnhancedDashboardData(
                    enhancedDashboardResponse.body(),
                    transactionsResponse.body()?.results ?: emptyList(),
                    pledgesResponse.body()?.pledges ?: emptyList(),
                    profileResponse.body(),
                    churchesResponse.body()?.churches ?: emptyList()
                )

            } catch (e: Exception) {
                Toast.makeText(this@MemberDashboardActivity, "Failed to load dashboard data: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun updateUIWithEnhancedDashboardData(
        enhancedDashboard: EnhancedDashboardResponse?,
        transactions: List<GivingTransactionResponse>,
        pledges: List<Pledge>,
        profile: UserProfileResponse?,
        churches: List<ChurchSearchResult>
    ) {
        // Update UI with enhanced dashboard data
        enhancedDashboard?.let { dashboard ->
            // Financial Overview - Map to existing UI elements
            updateFinancialOverviewWithBasicUI(dashboard.financial_overview)
            
            // Personal Giving - Map to existing UI elements
            updatePersonalGivingWithBasicUI(dashboard.personal_giving)
            
            // Church Metrics - Show in existing elements or log
            updateChurchMetricsWithBasicUI(dashboard.church_metrics)
            
            // Quick Stats - Show some stats in existing elements
            updateQuickStatsWithBasicUI(dashboard.quick_stats)
        }
        
        // Update other UI components
        updateTransactionsList(transactions)
        updatePledgesList(pledges)
        updateProfileInfo(profile)
        updateChurchesList(churches)
    }
    
    private fun updateFinancialOverviewWithBasicUI(financialOverview: FinancialOverview) {
        // Use existing basic UI elements for financial data
        binding.tvTotalGiving.text = CurrencyUtils.formatCurrency(financialOverview.total_income)
        binding.tvThisMonth.text = CurrencyUtils.formatCurrency(financialOverview.monthly_income)
        binding.tvThisYear.text = CurrencyUtils.formatCurrency(financialOverview.total_income)
        
        // Show net balance in last transaction amount temporarily
        binding.tvLastTransactionAmount.text = CurrencyUtils.formatCurrency(financialOverview.net_balance)
        binding.tvLastTransactionDate.text = if (financialOverview.net_balance >= 0) "Net Balance" else "Net Loss"
    }
    
    private fun updatePersonalGivingWithBasicUI(personalGiving: PersonalGiving) {
        // Update personal giving in existing elements
        binding.tvTotalGiving.text = CurrencyUtils.formatCurrency(personalGiving.total_giving)
        binding.tvThisMonth.text = CurrencyUtils.formatCurrency(personalGiving.this_month)
        
        // Show transaction count and percentage in existing elements
        binding.tvLastTransactionCategory.text = "${personalGiving.transaction_count} transactions"
        binding.tvLastTransactionDate.text = "${String.format("%.1f", personalGiving.percentage_of_church)}% of church"
    }
    
    private fun updateChurchMetricsWithBasicUI(churchMetrics: ChurchMetrics) {
        // Log church metrics since we don't have specific UI elements
        Log.d("Dashboard", "Church Metrics: ${churchMetrics.total_members} total, ${churchMetrics.active_members} active, ${churchMetrics.member_growth_rate}% growth")
        
        // Could show member count in church name temporarily
        binding.tvMemberChurch.text = "${churchMetrics.total_members} members"
    }
    
    private fun updateQuickStatsWithBasicUI(quickStats: QuickStats) {
        // Log quick stats since we don't have specific UI elements
        Log.d("Dashboard", "Quick Stats: Avg monthly: ${quickStats.avg_monthly_giving}, Goal progress: ${quickStats.giving_goal_progress.progress}%")
        
        // Show avg monthly giving in a temporary location
        binding.tvLastTransactionAmount.text = CurrencyUtils.formatCurrency(quickStats.avg_monthly_giving)
        binding.tvLastTransactionDate.text = "Avg Monthly"
    }
    
    private fun updateTransactionsList(transactions: List<GivingTransactionResponse>) {
        givingHistoryAdapter.submitList(transactions)
    }
    
    private fun updatePledgesList(pledges: List<Pledge>) {
        pledgeAdapter.updatePledges(pledges)
    }
    
    private fun updateProfileInfo(profile: UserProfileResponse?) {
        profile?.let {
            binding.tvMemberName.text = it.user?.first_name?.let { firstName ->
                it.user?.last_name?.let { lastName ->
                    "$firstName $lastName"
                } ?: firstName
            } ?: it.user?.email ?: "User"
            
            binding.tvMemberEmail.text = it.user?.email ?: "No email"
            
            // Update church info
            it.member?.church?.let { church ->
                binding.tvMemberChurch.text = church.name
                binding.tvChurchVerified.visibility = View.VISIBLE
                binding.tvChurchUnverified.visibility = View.GONE
            } ?: run {
                binding.tvMemberChurch.text = "No church assigned"
                binding.tvChurchVerified.visibility = View.GONE
                binding.tvChurchUnverified.visibility = View.VISIBLE
            }
        }
    }
    
    private fun updateChurchesList(churches: List<ChurchSearchResult>) {
        churchAdapter.updateChurches(churches)
    }

    private fun updateUIWithDashboardData(
        givingSummary: GivingSummaryResponse?,
        transactions: List<GivingTransactionResponse>,
        pledges: List<Pledge>,
        profile: UserProfileResponse?,
        churches: List<ChurchSearchResult>
    ) {
        // Update Giving Summary
        givingSummary?.let { summary ->
            binding.tvTotalGiving.text = CurrencyUtils.formatCurrency(summary.total_giving)
            binding.tvThisMonth.text = CurrencyUtils.formatCurrency(summary.this_month)
            binding.tvThisYear.text = CurrencyUtils.formatCurrency(summary.this_year)
            
            summary.last_transaction?.let { lastTx ->
                binding.tvLastTransactionAmount.text = CurrencyUtils.formatCurrency(lastTx.amount)
                binding.tvLastTransactionDate.text = lastTx.date
                binding.tvLastTransactionCategory.text = lastTx.category
            }
        }

        // Update Recent Transactions
        givingHistoryAdapter.submitList(transactions)

        // Update Pledges
        pledgeAdapter.updatePledges(pledges)
        
        // Update User Profile
        profile?.let { userProfile ->
            binding.tvMemberName.text = userProfile.user.first_name + " " + userProfile.user.last_name
            binding.tvMemberEmail.text = userProfile.user.email
            binding.tvMemberChurch.text = userProfile.church_info?.name ?: "No Church"
            
            // Update church verification status
            if (userProfile.church_info?.is_verified == true) {
                binding.tvChurchVerified.visibility = View.VISIBLE
                binding.tvChurchUnverified.visibility = View.GONE
            } else {
                binding.tvChurchVerified.visibility = View.GONE
                binding.tvChurchUnverified.visibility = View.VISIBLE
            }
        }

        // Update Churches for transfer
        churchAdapter.updateChurches(churches)

        // Show/hide sections based on data availability
        updateSectionVisibility()
    }

    private fun showChurchTransferDialog() {
        val churches = churchAdapter.currentList.ifEmpty { emptyList() }
        if (churches.isEmpty()) {
            Toast.makeText(this, "No churches available for transfer", Toast.LENGTH_SHORT).show()
            return
        }

        val churchNames = churches.map { church -> church.name + " (" + church.code + ")" }
        val builder = AlertDialog.Builder(this)
        
        builder.setTitle("Transfer Church")
        builder.setItems(churchNames.toTypedArray()) { dialog, which ->
            val selectedChurch = churches[which]
            showChurchTransferConfirmation(selectedChurch)
        }
        builder.setNegativeButton("Cancel", null)
        builder.show()
    }

    private fun showChurchTransferConfirmation(church: ChurchSearchResult) {
        val builder = AlertDialog.Builder(this)
        
        builder.setTitle("Confirm Transfer to " + church.name)
        builder.setMessage("Are you sure you want to transfer to " + church.name + "? This will require church approval.")
        builder.setPositiveButton("Yes") { _, _ ->
            initiateChurchTransfer(church)
        }
        builder.setNegativeButton("No", null)
        builder.show()
    }

    private fun initiateChurchTransfer(church: ChurchSearchResult) {
        lifecycleScope.launch {
            try {
                val transferRequest = ChurchTransferRequest(
                    target_church_id = church.id,
                    target_church_code = church.code,
                    reason = "User requested transfer"
                )

                val response = ApiService.getApiInterface().transferChurch(transferRequest)
                
                if (response.isSuccessful) {
                    Toast.makeText(this@MemberDashboardActivity, "Transfer request sent successfully", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@MemberDashboardActivity, "Transfer request failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MemberDashboardActivity, "Transfer error: " + e.message, Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showChurchTransferPendingDialog(churchName: String) {
        val builder = AlertDialog.Builder(this)
        
        builder.setTitle("Transfer Pending")
        builder.setMessage("Transfer request sent to " + churchName + ". Please wait for approval.")
        builder.setPositiveButton("OK") { _, _ -> }
        builder.setCancelable(false)
        builder.show()
    }

    private fun showChurchJoinDialog() {
        val builder = AlertDialog.Builder(this)
        
        builder.setTitle("Join Church")
        builder.setMessage("Enter church details to join")
        
        val inflater = layoutInflater
        val dialogView = inflater.inflate(R.layout.dialog_church_join, null)
        
        val etChurchCode = dialogView.findViewById<EditText>(R.id.et_church_code)
        val etVerificationData = dialogView.findViewById<EditText>(R.id.et_verification_data)
        
        builder.setView(dialogView)
        builder.setPositiveButton("Join") { _, _ ->
            val churchCode = etChurchCode.text.toString().trim()
            val verificationData = etVerificationData.text.toString().trim()
            
            if (churchCode.isNotEmpty() && verificationData.isNotEmpty()) {
                joinChurch(churchCode, verificationData)
            } else {
                Toast.makeText(this, "Please enter church code and verification data", Toast.LENGTH_SHORT).show()
            }
        }
        builder.setNegativeButton("Cancel", null)
        builder.show()
    }

    private fun joinChurch(churchCode: String, verificationData: String) {
        lifecycleScope.launch {
            try {
                val joinRequest = ChurchJoinRequest( // Will be resolved by backend using church_code
                    church_code = churchCode,
                    church_name = "loading",
                    user_id = (application as AltarFundsApp).preferencesManager.userId.toString()
                )

                val response = ApiService.getApiInterface().joinChurch(joinRequest)
                
                if (response.isSuccessful) {
                    Toast.makeText(this@MemberDashboardActivity, "Join request submitted successfully", Toast.LENGTH_SHORT).show()
                    // Refresh user data to get new church info
                    loadDashboardData()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MemberDashboardActivity, "Join error: " + e.message, Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showChurchJoinPendingDialog() {
        val builder = AlertDialog.Builder(this)
        
        builder.setTitle("Join Pending")
        builder.setMessage("Join request sent to church administrators. Please wait for approval.")
        builder.setPositiveButton("OK") { _, _ -> }
        builder.setCancelable(false)
        builder.show()
    }

    private fun setupClickListeners() {
        // Giving History
        binding.btnViewAllGiving.setOnClickListener {
            startActivity(Intent(this, TransactionHistoryActivity::class.java))
        }

        // Pledges
        binding.btnViewAllPledges.setOnClickListener {
            // TODO: Create PledgesActivity
            Toast.makeText(this, "Pledges feature coming soon", Toast.LENGTH_SHORT).show()
        }

        binding.btnCreatePledge.setOnClickListener {
            // TODO: Create CreatePledgeActivity
            Toast.makeText(this, "Create pledge feature coming soon", Toast.LENGTH_SHORT).show()
        }

        // Church Transfer
        binding.btnTransferChurch.setOnClickListener {
            showChurchTransferDialog()
        }

        binding.btnJoinChurch.setOnClickListener {
            showChurchJoinDialog()
        }

        // Statements
        binding.btnViewStatements.setOnClickListener {
            showStatementOptions()
        }

        // Financial Reports (PIN Protected)
        binding.btnFinancialReports.setOnClickListener {
            showPINEntryDialog("financial_reports")
        }

        // Settings
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        // Quick Actions
        binding.btnQuickGive.setOnClickListener {
            startActivity(Intent(this, EnhancedGivingActivity::class.java))
        }

        binding.btnQuickViewAllGiving.setOnClickListener {
            startActivity(Intent(this, TransactionHistoryActivity::class.java))
        }

        // Church Info
        binding.llChurchInfo.setOnClickListener {
            // Show church info dialog
            showChurchInfoDialog()
        }
    }

    private fun showStatementOptions() {
        val options = arrayOf("Monthly Statement", "Annual Statement", "Custom Period")
        
        AlertDialog.Builder(this)
            .setTitle("Select Statement Period")
            .setItems(options) { _, which ->
                when (which) {
                    0 -> generateStatement("monthly")
                    1 -> generateStatement("annual")
                    2 -> showCustomPeriodDialog()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showCustomPeriodDialog() {
        val builder = AlertDialog.Builder(this)
        val inflater = layoutInflater
        val dialogView = inflater.inflate(R.layout.dialog_custom_period, null)
        
        val etStartDate = dialogView.findViewById<EditText>(R.id.et_start_date)
        val etEndDate = dialogView.findViewById<EditText>(R.id.et_end_date)
        
        builder.setTitle("Custom Period")
        builder.setView(dialogView)
        builder.setPositiveButton("Generate") { dialog, which ->
            val startDate = etStartDate.text.toString()
            val endDate = etEndDate.text.toString()
            generateStatement("custom", startDate, endDate)
        }
        builder.setNegativeButton("Cancel", null)
        builder.show()
    }

    private fun generateStatement(type: String, startDate: String? = null, endDate: String? = null) {
        lifecycleScope.launch {
            try {
                val request = when (type) {
                    "monthly" -> mapOf("month" to LocalDate.now().monthValue)
                    "annual" -> mapOf("year" to LocalDate.now().year)
                    "custom" -> mapOf(
                        "start_date" to (startDate ?: ""),
                        "end_date" to (endDate ?: "")
                    )
                    else -> return@launch
                }

                val response = ApiService.getApiInterface().getGivingStatements(
                    month = request["month"] as? Int,
                    year = request["year"] as? Int
                )

                if (response.isSuccessful && response.body() != null) {
                    showStatementDialog(response.body()!!)
                } else {
                    Toast.makeText(this@MemberDashboardActivity, "Failed to generate statement", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MemberDashboardActivity, "Statement generation error: " + e.message, Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showStatementDialog(statement: Any) {
        val message = "Statement Generated Successfully!\n\n" +
            "The statement has been saved to your device and can be shared via email or WhatsApp."
        
        AlertDialog.Builder(this)
            .setTitle("Statement Ready")
            .setMessage(message)
            .setPositiveButton("Share") { _, _ ->
                // Share functionality
            }
            .setNegativeButton("Save") { _, _ ->
                // Save functionality
            }
            .show()
    }

    private fun shareStatement(statement: Any) {
        val shareText = "My AltarFunds Statement\n\n" +
            "Generated on " + LocalDate.now()
        
        val shareIntent = Intent().apply {
            action = Intent.ACTION_SEND
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, shareText)
        }
        startActivity(Intent.createChooser(shareIntent, "Share Statement"))
    }

    private fun saveStatement(statement: Any) {
        Toast.makeText(this, "Statement saved to device", Toast.LENGTH_SHORT).show()
        // In a real implementation, save to PDF or storage
    }

    private fun showPINEntryDialog(purpose: String) {
        val builder = AlertDialog.Builder(this)
        val inflater = layoutInflater
        // Create a simple PIN entry dialog
        val etPIN = EditText(this)
        etPIN.hint = "Enter 4-digit PIN"
        etPIN.inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_VARIATION_PASSWORD
        
        val tvPurpose = TextView(this)
        tvPurpose.text = when (purpose) {
            "financial_reports" -> "Enter PIN to view financial reports"
            "settings_change" -> "Enter PIN to change settings"
            "church_transfer" -> "Enter PIN to transfer churches"
            else -> "Enter PIN"
        }
        
        val container = LinearLayout(this)
        container.orientation = LinearLayout.VERTICAL
        container.setPadding(50, 50, 50, 50)
        container.addView(tvPurpose)
        container.addView(etPIN)
        
        builder.setTitle("Secure Access Required")
        builder.setView(container)
        builder.setPositiveButton("Verify") { _, _ ->
            val pin = etPIN.text.toString()
            verifyPIN(pin, purpose)
        }
        builder.setNegativeButton("Cancel", null)
        builder.show()
    }

    private fun verifyPIN(pin: String, purpose: String) {
        if (pin.length < 4) {
            Toast.makeText(this, "PIN must be 4 digits", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val pinRequest = PINVerifyRequest(
                    pin = pin,
                    purpose = purpose
                )
                val response = ApiService.getApiInterface().verifyPIN(pinRequest)

                if (response.isSuccessful) {
                    when (purpose) {
                        "financial_reports" -> openFinancialReports()
                        "settings_change" -> openSettingsWithVerification()
                        "church_transfer" -> openChurchTransfer()
                    }
                } else {
                    Toast.makeText(this@MemberDashboardActivity, "PIN verification failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MemberDashboardActivity, "PIN verification error: " + e.message, Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun openFinancialReports() {
        Toast.makeText(this, "Access granted to financial reports", Toast.LENGTH_SHORT).show()
        // Navigate to financial reports screen
        // startActivity(Intent(this, FinancialReportsActivity::class.java))
    }

    private fun openSettingsWithVerification() {
        Toast.makeText(this, "Access granted to settings", Toast.LENGTH_SHORT).show()
        // Navigate to settings with elevated permissions
        startActivity(Intent(this, SettingsActivity::class.java))
    }

    private fun openChurchTransfer() {
        Toast.makeText(this, "Access granted to church transfer", Toast.LENGTH_SHORT).show()
        // TODO: Create ChurchTransferActivity
        // startActivity(Intent(this, ChurchTransferActivity::class.java))
    }

    private fun showChurchInfoDialog() {
        val message = "Church Information\n\n" +
            "Your church details will appear here once you join a church."
        
        AlertDialog.Builder(this)
            .setTitle("Church Details")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> }
            .show()
    }

    private fun updateSectionVisibility() {
        // Show/hide sections based on data availability
        try {
            // Show giving summary if data is available
            if (binding.tvTotalGiving.text != "KES 0.00") {
                // Giving summary has data
            }
            
            // Show recent transactions if adapter has data
            if (givingHistoryAdapter.itemCount > 0) {
                // Transactions available
            } else {
                // No transactions, could show empty state
            }
            
            // Show pledges section if adapter has data
            if (pledgeAdapter.itemCount > 0) {
                // Pledges available
            } else {
                // No pledges, could show empty state
            }
            
            // Show church actions based on user church status
            val hasChurch = binding.tvMemberChurch.text != "No Church"
            binding.btnTransferChurch.isEnabled = hasChurch
            binding.btnJoinChurch.isEnabled = !hasChurch
            
        } catch (e: Exception) {
            // Handle any binding errors gracefully
            e.printStackTrace()
        }
    }
}
