package com.altarfunds.mobile

import android.app.Application
import com.altarfunds.mobile.api.ApiService
import com.altarfunds.mobile.data.AppDatabase
import com.altarfunds.mobile.data.PreferencesManager

class AltarFundsApp : Application() {
    
    lateinit var database: AppDatabase
        private set
    lateinit var preferencesManager: PreferencesManager
        private set
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize dependencies
        database = AppDatabase.getDatabase(this)
        preferencesManager = PreferencesManager(this)
        
        // Initialize API service
        ApiService.initialize(this)
    }
}
