package com.altarfunds.mobile.ui.fragments

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.HelpActivity
import com.altarfunds.mobile.RecurringGivingActivity
import com.altarfunds.mobile.SettingsActivity
import com.altarfunds.mobile.TransactionHistoryActivity
import com.altarfunds.mobile.databinding.FragmentProfileBinding
import com.altarfunds.mobile.utils.DeviceUtils
import com.bumptech.glide.Glide
import kotlinx.coroutines.launch

class ProfileFragment : Fragment() {

    private lateinit var binding: FragmentProfileBinding

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        loadUserProfile()
        setupClickListeners()
    }

    private fun loadUserProfile() {
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val profileResponse = com.altarfunds.mobile.api.ApiService.getApiInterface().getUserProfile()
                
                if (profileResponse.isSuccessful && profileResponse.body() != null) {
                    val profile = profileResponse.body()!!
                    updateUIWithProfile(profile)
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load profile", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun updateUIWithProfile(profile: com.altarfunds.mobile.models.UserProfileResponse) {
        // User information
        binding.tvUserName.text = "${profile.user.first_name} ${profile.user.last_name}"
        binding.tvUserEmail.text = profile.user.email
        binding.tvUserRole.text = profile.user.role.replace("_", " ").capitalize()
        
        // Member information
        profile.member?.let { member ->
            binding.tvMembershipNumber.text = member.membership_number
            binding.tvMemberType.text = member.member_type.replace("_", " ").capitalize()
            binding.tvJoinDate.text = formatDate(member.join_date)
            
            if (member.is_active) {
                binding.tvMemberStatus.text = "Active"
                binding.tvMemberStatus.setTextColor(com.altarfunds.mobile.R.color.green)
            } else {
                binding.tvMemberStatus.text = "Inactive"
                binding.tvMemberStatus.setTextColor(com.altarfunds.mobile.R.color.red)
            }
            
            binding.llMemberInfo.visibility = View.VISIBLE
        } ?: run {
            binding.llMemberInfo.visibility = View.GONE
        }
        /*
        // Church information
        profile.church_info?.let { church ->
            binding.tvChurchName.text = church.name
            binding.tvChurchCode.text = church.code
            
            if (church.is_verified) {
                binding.tvChurchVerified.text = "Verified"
                binding.tvChurchVerified.setTextColor(com.altarfunds.mobile.R.color.green)
            } else {
                binding.tvChurchVerified.text = "Not Verified"
                binding.tvChurchVerified.setTextColor(com.altarfunds.mobile.R.color.orange)
            }
            
            binding.llChurchInfo.visibility = View.VISIBLE
        } ?: run {
            binding.llChurchInfo.visibility = View.GONE
        }
        
        // Device information
        if (profile.devices.isNotEmpty()) {
            val device = profile.devices.first()
            binding.tvDeviceType.text = device.device_type.capitalize()
            binding.tvAppVersion.text = device.app_version ?: "Unknown"
            binding.tvLastSeen.text = formatDate(device.last_seen ?: "")
            binding.llDeviceInfo.visibility = View.VISIBLE
        } else {
            binding.llDeviceInfo.visibility = View.GONE
        }
        
        // Permissions
        if (profile.permissions.isNotEmpty()) {
            binding.tvPermissions.text = profile.permissions.joinToString(", ")
            binding.llPermissions.visibility = View.VISIBLE
        } else {
            binding.llPermissions.visibility = View.GONE
        }*/
    }

    private fun setupClickListeners() {
        // Edit profile
        binding.btnEditProfile.setOnClickListener {
            Toast.makeText(requireContext(), "Profile editing coming soon", Toast.LENGTH_SHORT).show()
        }
        
        // Giving history
        binding.btnGivingHistory.setOnClickListener {
            startActivity(Intent(requireContext(), TransactionHistoryActivity::class.java))
        }
        
        // Recurring giving
        binding.btnRecurringGiving.setOnClickListener {
            startActivity(Intent(requireContext(), RecurringGivingActivity::class.java))
        }
        
        // Pledges
        binding.btnPledges.setOnClickListener {
            Toast.makeText(requireContext(), "Pledges coming soon", Toast.LENGTH_SHORT).show()
        }
        
        // Settings
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(requireContext(), SettingsActivity::class.java))
        }
        
        // Help & Support
        binding.btnHelpSupport.setOnClickListener {
            startActivity(Intent(requireContext(), HelpActivity::class.java))
        }
        
        // Logout
        binding.btnLogout.setOnClickListener {
            logoutUser()
        }
        
        // App info
        binding.btnAppInfo.setOnClickListener {
            showAppInfo()
        }
    }

    private fun logoutUser() {
        lifecycleScope.launch {
            try {
                // Clear local data
                val preferencesManager = (requireActivity().application as com.altarfunds.mobile.AltarFundsApp).preferencesManager
                preferencesManager.clearUserData()
                
                // Navigate to login
                val intent = Intent(requireContext(), com.altarfunds.mobile.LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
                requireActivity().finish()
                
                Toast.makeText(requireContext(), "Logged out successfully", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to logout", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showAppInfo() {
        val deviceInfo = DeviceUtils.getDeviceInfo(requireContext())
        val appInfo = """
            AltarFunds Mobile App
            Version: ${deviceInfo.appVersion}
            Platform: ${deviceInfo.osVersion}
            Device: ${deviceInfo.deviceId}
            
            © 2024 AltarFunds
            Church Giving Made Simple
        """.trimIndent()
        
        androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle("App Information")
            .setMessage(appInfo)
            .setPositiveButton("OK") { dialog, _ -> dialog.dismiss() }
            .show()
    }

    private fun formatDate(dateString: String): String {
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
