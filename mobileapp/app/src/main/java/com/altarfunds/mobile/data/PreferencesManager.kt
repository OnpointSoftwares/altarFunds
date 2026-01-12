package com.altarfunds.mobile.data

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson

class PreferencesManager(context: Context) {
    
    private val sharedPreferences: SharedPreferences = 
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()
    
    companion object {
        private const val PREFS_NAME = "altar_funds_prefs"
        
        // Keys
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_EMAIL = "user_email"
        private const val KEY_USER_NAME = "user_name"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_DEVICE_TOKEN = "device_token"
        private const val KEY_CHURCH_ID = "church_id"
        private const val KEY_CHURCH_NAME = "church_name"
        private const val KEY_MEMBER_ID = "member_id"
        private const val KEY_IS_FIRST_LAUNCH = "is_first_launch"
        private const val KEY_LAST_SYNC = "last_sync"
        private const val KEY_APP_VERSION = "app_version"
    }
    
    var authToken: String?
        get() = sharedPreferences.getString(KEY_AUTH_TOKEN, null)
        set(value) = sharedPreferences.edit().putString(KEY_AUTH_TOKEN, value).apply()
    
    var refreshToken: String?
        get() = sharedPreferences.getString(KEY_REFRESH_TOKEN, null)
        set(value) = sharedPreferences.edit().putString(KEY_REFRESH_TOKEN, value).apply()
    
    var userEmail: String?
        get() = sharedPreferences.getString(KEY_USER_EMAIL, null)
        set(value) = sharedPreferences.edit().putString(KEY_USER_EMAIL, value).apply()
    
    var userName: String?
        get() = sharedPreferences.getString(KEY_USER_NAME, null)
        set(value) = sharedPreferences.edit().putString(KEY_USER_NAME, value).apply()
    
    var userId: String?
        get() = sharedPreferences.getString(KEY_USER_ID, null)
        set(value) = sharedPreferences.edit().putString(KEY_USER_ID, value).apply()
    
    var deviceToken: String?
        get() = sharedPreferences.getString(KEY_DEVICE_TOKEN, null)
        set(value) = sharedPreferences.edit().putString(KEY_DEVICE_TOKEN, value).apply()
    
    var churchId: String?
        get() = sharedPreferences.getString(KEY_CHURCH_ID, null)
        set(value) = sharedPreferences.edit().putString(KEY_CHURCH_ID, value).apply()
    
    var churchName: String?
        get() = sharedPreferences.getString(KEY_CHURCH_NAME, null)
        set(value) = sharedPreferences.edit().putString(KEY_CHURCH_NAME, value).apply()
    
    var memberId: String?
        get() = sharedPreferences.getString(KEY_MEMBER_ID, null)
        set(value) = sharedPreferences.edit().putString(KEY_MEMBER_ID, value).apply()
    
    var isFirstLaunch: Boolean
        get() = sharedPreferences.getBoolean(KEY_IS_FIRST_LAUNCH, true)
        set(value) = sharedPreferences.edit().putBoolean(KEY_IS_FIRST_LAUNCH, value).apply()
    
    var lastSync: Long
        get() = sharedPreferences.getLong(KEY_LAST_SYNC, 0)
        set(value) = sharedPreferences.edit().putLong(KEY_LAST_SYNC, value).apply()
    
    var appVersion: String?
        get() = sharedPreferences.getString(KEY_APP_VERSION, null)
        set(value) = sharedPreferences.edit().putString(KEY_APP_VERSION, value).apply()
    
    fun clearUserData() {
        sharedPreferences.edit().apply {
            remove(KEY_AUTH_TOKEN)
            remove(KEY_REFRESH_TOKEN)
            remove(KEY_USER_EMAIL)
            remove(KEY_USER_NAME)
            remove(KEY_USER_ID)
            remove(KEY_CHURCH_ID)
            remove(KEY_CHURCH_NAME)
            remove(KEY_MEMBER_ID)
        }.apply()
    }
    
    fun saveUserSession(loginResponse: com.altarfunds.mobile.models.LoginResponse) {
        authToken = loginResponse.access_token
        refreshToken = loginResponse.refresh_token
        userId = loginResponse.user.id
        userEmail = loginResponse.user.email
        userName = "${loginResponse.user.first_name} ${loginResponse.user.last_name}"
        
        loginResponse.member?.let { member ->
            memberId = member.id
        }
        
        deviceToken = loginResponse.device.device_token
    }
    
    fun isLoggedIn(): Boolean {
        return !authToken.isNullOrEmpty()
    }
}
