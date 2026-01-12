package com.altarfunds.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.databinding.ActivitySignUpBinding
import com.altarfunds.mobile.models.GoogleLoginRequest
import com.altarfunds.mobile.models.RegisterRequest
import com.altarfunds.mobile.utils.DeviceUtils
import com.altarfunds.mobile.utils.ValidationUtils
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import kotlinx.coroutines.launch

class SignUpActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySignUpBinding
    private lateinit var googleSignInClient: GoogleSignInClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySignUpBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupGoogleSignIn()
        setupClickListeners()
    }

    private fun setupClickListeners() {
        binding.signupBtn.setOnClickListener {
            performRegister()
        }

        binding.haveAccount.setOnClickListener {
            finish()
        }

        binding.googleSignInBtn.setOnClickListener {
            googleSignInClient.signOut()
            startActivityForResult(googleSignInClient.signInIntent, RC_SIGN_IN)
        }
    }

    private fun performRegister() {
        val email = binding.email.text.toString().trim()
        val password = binding.password.text.toString().trim()
        val passwordConfirm = binding.passwordRetype.text.toString().trim()

        if (!ValidationUtils.isValidEmail(email)) {
            binding.email.error = "Invalid email address"
            return
        }

        if (password.isEmpty()) {
            binding.password.error = "Password is required"
            return
        }

        if (passwordConfirm.isEmpty()) {
            binding.passwordRetype.error = "Please confirm password"
            return
        }

        if (password != passwordConfirm) {
            binding.passwordRetype.error = "Passwords do not match"
            return
        }

        setLoading(true)

        lifecycleScope.launch {
            try {
                val deviceInfo = DeviceUtils.getDeviceInfo(this@SignUpActivity)
                val req = RegisterRequest(
                    email = email,
                    password = password,
                    password_confirm = passwordConfirm,
                    device_token = deviceInfo.deviceToken,
                    device_type = "android",
                    device_id = deviceInfo.deviceId,
                    app_version = deviceInfo.appVersion,
                    os_version = deviceInfo.osVersion
                )

                val response = ApiService.getApiInterface().register(req)
                if (response.isSuccessful && response.body() != null) {
                    val loginResponse = response.body()!!
                    (application as AltarFundsApp).preferencesManager.saveUserSession(loginResponse)
                    startActivity(Intent(this@SignUpActivity, MainActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(
                        this@SignUpActivity,
                        "Sign up failed: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@SignUpActivity,
                    "Sign up failed: ${e.message}",
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
                val deviceInfo = DeviceUtils.getDeviceInfo(this@SignUpActivity)
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
                    (application as AltarFundsApp).preferencesManager.saveUserSession(loginResponse)
                    startActivity(Intent(this@SignUpActivity, MainActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(
                        this@SignUpActivity,
                        "Google login failed: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@SignUpActivity,
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
        binding.signupBtn.isEnabled = !isLoading
        binding.googleSignInBtn.isEnabled = !isLoading
    }

    companion object {
        private const val RC_SIGN_IN = 1001
    }
}
