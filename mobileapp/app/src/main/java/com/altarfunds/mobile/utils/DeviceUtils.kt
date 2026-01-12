package com.altarfunds.mobile.utils

import android.content.Context
import android.provider.Settings
import android.os.Build
import android.telephony.TelephonyManager
import com.google.android.gms.tasks.Task

object DeviceUtils {
    
    data class DeviceInfo(
        val deviceToken: String?,
        val deviceId: String,
        val appVersion: String,
        val osVersion: String
    )
    
    fun getDeviceInfo(context: Context): DeviceInfo {
        val deviceId = getDeviceId(context)
        val appVersion = getAppVersion(context)
        val osVersion = "Android ${Build.VERSION.RELEASE}"
        
        return DeviceInfo(
            deviceToken = null, // Will be set when Firebase token is available
            deviceId = deviceId,
            appVersion = appVersion,
            osVersion = osVersion
        )
    }
    
    private fun getDeviceId(context: Context): String {
        return try {
            // Try to get unique device identifier
            Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ANDROID_ID
            ) ?: "unknown_device"
        } catch (e: Exception) {
            "unknown_device"
        }
    }
    
    private fun getAppVersion(context: Context): String {
        return try {
            val packageManager = context.packageManager
            val packageInfo = packageManager.getPackageInfo(context.packageName, 0)
            packageInfo.versionName ?: "1.0.0"
        } catch (e: Exception) {
            "1.0.0"
        }
    }

    
    fun getPhoneNumber(context: Context): String? {
        return try {
            val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
            telephonyManager.line1Number
        } catch (e: Exception) {
            null
        }
    }
    
    fun getDeviceModel(): String {
        return "${Build.MANUFACTURER} ${Build.MODEL}"
    }
    
    fun getDeviceLanguage(context: Context): String {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            context.resources.configuration.locales[0].language
        } else {
            @Suppress("DEPRECATION")
            context.resources.configuration.locale.language
        }
    }
}
