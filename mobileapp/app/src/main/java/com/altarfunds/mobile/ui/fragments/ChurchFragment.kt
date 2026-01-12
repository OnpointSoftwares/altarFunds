package com.altarfunds.mobile.ui.fragments

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.databinding.FragmentChurchBinding
import com.bumptech.glide.Glide
import kotlinx.coroutines.launch

class ChurchFragment : Fragment() {

    private lateinit var binding: FragmentChurchBinding

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentChurchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        loadChurchInfo()
        setupClickListeners()
    }

    private fun loadChurchInfo() {
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val churchInfoResponse = com.altarfunds.mobile.api.ApiService.getApiInterface().getChurchInfo()
                
                if (churchInfoResponse.isSuccessful && churchInfoResponse.body() != null) {
                    val churchInfo = churchInfoResponse.body()!!
                    updateUIWithChurchInfo(churchInfo)
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load church information", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun updateUIWithChurchInfo(churchInfo: com.altarfunds.mobile.models.ChurchInfoResponse) {
        // Basic church info
        binding.tvChurchName.text = churchInfo.name
        binding.tvChurchCode.text = "Code: ${churchInfo.code}"
        binding.tvChurchDescription.text = churchInfo.description
        
        // Status badges
        if (churchInfo.is_verified) {
            binding.tvVerifiedBadge.visibility = View.VISIBLE
        } else {
            binding.tvVerifiedBadge.visibility = View.GONE
        }
        
        if (churchInfo.is_active) {
            binding.tvActiveBadge.visibility = View.VISIBLE
            binding.tvActiveBadge.visibility = View.GONE
        }
        
        // Load church logo
        churchInfo.logo?.let { logoUrl ->
            Glide.with(requireContext())
                .load(logoUrl)
                .placeholder(com.altarfunds.mobile.R.drawable.ic_church_placeholder)
                .error(com.altarfunds.mobile.R.drawable.ic_church_placeholder)
                .into(binding.ivChurchLogo)
        }
        
        // Contact information
        binding.tvChurchPhone.text = churchInfo.contact_info.phone
        binding.tvChurchEmail.text = churchInfo.contact_info.email
        
        // Address
        binding.tvChurchAddress.text = "${churchInfo.address.street}, ${churchInfo.address.city}"
        binding.tvChurchLocation.text = "${churchInfo.address.county}, ${churchInfo.address.country}"
        
        // Setup campus list
        setupCampusList(churchInfo.campuses)
        
        // Setup department list
        setupDepartmentList(churchInfo.departments)
        
        // Setup giving categories
        setupGivingCategories(churchInfo.giving_categories)
    }

    private fun setupCampusList(campuses: List<com.altarfunds.mobile.models.Campus>) {
        if (campuses.isEmpty()) {
            binding.tvNoCampuses.visibility = View.VISIBLE
           // binding.rvCampuses.visibility = View.GONE
            return
        }
        
        binding.tvNoCampuses.visibility = View.GONE
        //binding.rvCampuses.visibility = View.VISIBLE
        
        // Setup campus adapter (simplified for now)
        val campusNames = campuses.map { campus ->
            "${campus.name}${if (campus.is_main_campus) " (Main)" else ""}"
        }
        
        // For simplicity, show as text for now
        binding.tvCampusList.text = campusNames.joinToString("\n")
    }

    private fun setupDepartmentList(departments: List<com.altarfunds.mobile.models.Department>) {
        if (departments.isEmpty()) {
            //binding.tvNoDepartments.visibility = View.VISIBLE
            //binding.llDepartmentList.visibility = View.GONE
            return
        }
        
        //binding.tvNoDepartments.visibility = View.GONE
        //binding.rvDepartments.visibility = View.VISIBLE
        
        // Setup department adapter (simplified for now)
        val departmentInfo = departments.map { dept ->
            "${dept.name}\n${dept.description}\nLeader: ${dept.head_name}"
        }
        
        // For simplicity, show as text for now
        //binding.tvDepartmentList.text = departmentInfo.joinToString("\n\n")
    }

    private fun setupGivingCategories(categories: List<com.altarfunds.mobile.models.GivingCategory>) {
        if (categories.isEmpty()) {
           // binding.tvNoCategories.visibility = View.VISIBLE
           // binding.llCategoryList.visibility = View.GONE
            return
        }
        
       // binding.tvNoCategories.visibility = View.GONE
        //binding.llCategoryList.visibility = View.VISIBLE
        
        // Setup categories adapter (simplified for now)
        val categoryInfo = categories.map { category ->
            "${category.name}\n${category.description ?: ""}\n${if (category.is_tax_deductible) "Tax Deductible" else "Not Tax Deductible"}"
        }
        
        // For simplicity, show as text for now
        //binding.tvCategoryList.text = categoryInfo.joinToString("\n\n")
    }

    private fun setupClickListeners() {
        // Phone call
        binding.llPhone.setOnClickListener {
            val phone = binding.tvChurchPhone.text.toString()
            if (phone.isNotEmpty()) {
                val intent = Intent(Intent.ACTION_DIAL).apply {
                    data = Uri.parse("tel:$phone")
                }
                startActivity(intent)
            }
        }
        
        // Email
        binding.llEmail.setOnClickListener {
            val email = binding.tvChurchEmail.text.toString()
            if (email.isNotEmpty()) {
                val intent = Intent(Intent.ACTION_SENDTO).apply {
                    data = Uri.parse("mailto:$email")
                }
                startActivity(intent)
            }
        }
        
        // Website
        binding.llEmail.setOnClickListener {
            // Will be implemented when website is available
            Toast.makeText(requireContext(), "Website link coming soon", Toast.LENGTH_SHORT).show()
        }
        
        // Map location
        binding.llLocation.setOnClickListener {
            // Open in maps
            val address = binding.tvChurchAddress.text.toString()
            if (address.isNotEmpty()) {
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    data = Uri.parse("geo:0,0?q=$address")
                }
                startActivity(intent)
            }
        }
        
        // View all campuses
        binding.btnViewAllCampuses.setOnClickListener {
            // Navigate to campuses list
        }
        
        // View all departments
       /* binding.btnViewAllDepartments.setOnClickListener {
            // Navigate to departments list
            Toast.makeText(requireContext(), "Department details coming soon", Toast.LENGTH_SHORT).show()
        }
        
        // View all categories
        binding.btnViewAllCategories.setOnClickListener {
            // Navigate to categories list
            Toast.makeText(requireContext(), "Category details coming soon", Toast.LENGTH_SHORT).show()
        }*/
    }
}
