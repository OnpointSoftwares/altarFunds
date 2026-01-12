package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.ismaeldivita.chipnavigation.ChipNavigationBar
import com.altarfunds.mobile.databinding.ActivityMainBinding
import com.altarfunds.mobile.ui.fragments.GivingFragment
import com.altarfunds.mobile.ui.fragments.ProfileFragment
import com.altarfunds.mobile.ui.fragments.HistoryFragment
import com.altarfunds.mobile.ui.fragments.ChurchFragment

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Initialize fragments
        val givingFragment = GivingFragment()
        val historyFragment = HistoryFragment()
        val churchFragment = ChurchFragment()
        val profileFragment = ProfileFragment()

        // Set default fragment
        binding.chipAppBar.setItemSelected(R.id.ic_transaction, true)
        makeCurrentFragment(givingFragment)

        // Set up bottom navigation
        binding.chipAppBar.setOnItemSelectedListener { itemId ->
            when (itemId) {
                R.id.ic_transaction -> makeCurrentFragment(givingFragment)
                R.id.ic_account -> makeCurrentFragment(profileFragment)
            }
            true
        }

        // Check if user is logged in
        if (!isUserLoggedIn()) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
        }
    }

    private fun makeCurrentFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction().apply {
            replace(R.id.fl_wrapper, fragment)
            commit()
        }
    }

    private fun isUserLoggedIn(): Boolean {
        val preferencesManager = (application as AltarFundsApp).preferencesManager
        return preferencesManager.isLoggedIn()
    }

    fun floatingActionButton(view: android.view.View) {
        startActivity(Intent(this, NewGivingActivity::class.java))
    }
}
