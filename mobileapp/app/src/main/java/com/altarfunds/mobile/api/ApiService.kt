package com.altarfunds.mobile.api

import com.altarfunds.mobile.AltarFundsApp
import com.altarfunds.mobile.data.PreferencesManager
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiService {
    private const val BASE_URL = "https://altarfunds.pythonanywhere.com"
    
    private lateinit var retrofit: Retrofit
    private lateinit var apiInterface: ApiInterface
    private var preferencesManager: PreferencesManager? = null
    
    fun initialize(app: AltarFundsApp? = null) {
        preferencesManager = app?.preferencesManager
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        val authInterceptor = Interceptor { chain ->
            val requestBuilder = chain.request().newBuilder()
            
            // Add auth token if available
            preferencesManager?.authToken?.let { token ->
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }
            
            // Add device token if available
            preferencesManager?.deviceToken?.let { deviceToken ->
                requestBuilder.addHeader("X-Device-Token", deviceToken)
            }
            
            chain.proceed(requestBuilder.build())
        }
        
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .addInterceptor(authInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
        
        retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        apiInterface = retrofit.create(ApiInterface::class.java)
    }
    
    fun getApiInterface(): ApiInterface {
        if (!::apiInterface.isInitialized) {
            initialize(null)
        }
        return apiInterface
    }
}
