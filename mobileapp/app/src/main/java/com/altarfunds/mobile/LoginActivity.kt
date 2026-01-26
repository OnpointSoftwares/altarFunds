package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.databinding.ActivityLoginBinding
import com.altarfunds.mobile.models.GoogleLoginRequest
import com.altarfunds.mobile.models.LoginCredentials
import com.altarfunds.mobile.models.LoginRequest
import com.altarfunds.mobile.utils.DeviceUtils
import com.altarfunds.mobile.utils.ValidationUtils
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private lateinit var googleSignInClient: GoogleSignInClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Check if already logged in
        if (isUserLoggedIn()) {
            startActivity(Intent(this, MemberDashboardModernActivity::class.java))
            finish()
            return
        }

        setupGoogleSignIn()
        setupClickListeners()
    }

    private fun setupClickListeners() {
        binding.loginBtn.setOnClickListener {
            performLogin()
        }

        binding.forgotPassword.setOnClickListener {
            // Handle forgot password
            Toast.makeText(this, "Forgot password feature coming soon", Toast.LENGTH_SHORT).show()
        }

        binding.createAccount.setOnClickListener {
            startActivity(Intent(this, SignUpActivity::class.java))
        }

        binding.googleSignInBtn.setOnClickListener {
            googleSignInClient.signOut()
            startActivityForResult(googleSignInClient.signInIntent, RC_SIGN_IN)
        }
    }

    private fun performLogin() {
        val email = binding.email.text.toString().trim()
        val password = binding.password.text.toString().trim()

        // Validate inputs
        if (!ValidationUtils.isValidEmail(email)) {
            binding.email.error = "Invalid email address"
            return
        }

        if (password.isEmpty()) {
            binding.password.error = "Password is required"
            return
        }

        setLoading(true)

        // Perform login
        lifecycleScope.launch {
            try {
                val credentials = LoginCredentials(
                    email = email,
                    password = password
                )

                val response = ApiService.getApiInterface().loginBackend(credentials)

                if (response.isSuccessful && response.body() != null) {
                    val tokenResponse = response.body()!!

                    val preferencesManager = (application as AltarFundsApp).preferencesManager
                    preferencesManager.authToken = tokenResponse.access
                    preferencesManager.refreshToken = tokenResponse.refresh
                    preferencesManager.userEmail = email

                    startActivity(Intent(this@LoginActivity, MemberDashboardModernActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(
                        this@LoginActivity,
                        "Login failed: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@LoginActivity,
                    "Login failed: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private fun setupGoogleSignIn() {
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(getString(R.string.webclientid))
            .requestEmail()
            .build()

        googleSignInClient = GoogleSignIn.getClient(this, gso)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode != RC_SIGN_IN) return

        val task = GoogleSignIn.getSignedInAccountFromIntent(data)
        try {
            val account = task.getResult(ApiException::class.java) ?: return
            val idToken = account.idToken
            if (idToken.isNullOrEmpty()) {
                Toast.makeText(this, "Google sign-in failed", Toast.LENGTH_LONG).show()
                return
            }
            performGoogleLogin(idToken)
        } catch (e: ApiException) {
            Toast.makeText(this, "Google sign-in failed", Toast.LENGTH_LONG).show()
        }
    }

    private fun performGoogleLogin(idToken: String) {
        setLoading(true)

        lifecycleScope.launch {
            try {
                val deviceInfo = DeviceUtils.getDeviceInfo(this@LoginActivity)
                val req = GoogleLoginRequest(
                    firebase_token = idToken,
                    device_token = deviceInfo.deviceToken,
                    device_type = "android",
                    device_id = deviceInfo.deviceId,
                    app_version = deviceInfo.appVersion,
                    os_version = deviceInfo.osVersion
                )

                val response = ApiService.getApiInterface().googleLogin(req)
                if (response.isSuccessful && response.body() != null) {
                    val loginResponse = response.body()!!
                    val preferencesManager = (application as AltarFundsApp).preferencesManager
                    preferencesManager.saveUserSession(loginResponse)
                    startActivity(Intent(this@LoginActivity, MemberDashboardActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(
                        this@LoginActivity,
                        "Google login failed: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@LoginActivity,
                    "Google login failed: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private fun setLoading(isLoading: Boolean) {
        binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        binding.loginBtn.isEnabled = !isLoading
        binding.googleSignInBtn.isEnabled = !isLoading
    }

    private fun isUserLoggedIn(): Boolean {
        val preferencesManager = (application as AltarFundsApp).preferencesManager
        return preferencesManager.isLoggedIn()
    }

    companion object {
        private const val RC_SIGN_IN = 1001
    }
}
