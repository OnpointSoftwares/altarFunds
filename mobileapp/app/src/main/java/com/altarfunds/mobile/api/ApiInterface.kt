package com.altarfunds.mobile.api

import com.altarfunds.mobile.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiInterface {
    
    // Authentication
    @POST("mobile/login/")
    suspend fun login(@Body loginRequest: LoginRequest): Response<LoginResponse>

    @POST("mobile/google-login/")
    suspend fun googleLogin(@Body googleLoginRequest: GoogleLoginRequest): Response<LoginResponse>

    @POST("mobile/register/")
    suspend fun register(@Body registerRequest: RegisterRequest): Response<LoginResponse>
    
    @POST("mobile/register-device/")
    suspend fun registerDevice(@Body deviceRequest: DeviceRegistrationRequest): Response<DeviceRegistrationResponse>
    
    // App Configuration
    @GET("mobile/config/")
    suspend fun getAppConfig(@Query("platform") platform: String = "android"): Response<AppConfigResponse>
    
    // User Profile
    @GET("mobile/profile/")
    suspend fun getUserProfile(): Response<UserProfileResponse>
    
    // Giving
    @GET("mobile/giving-summary/")
    suspend fun getGivingSummary(): Response<GivingSummaryResponse>
    
    @POST("giving/transactions/")
    suspend fun createGivingTransaction(@Body transactionRequest: GivingTransactionRequest): Response<GivingTransactionResponse>
    
    @GET("giving/transactions/")
    suspend fun getGivingTransactions(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<TransactionListResponse>
    
    @POST("payments/requests/")
    suspend fun initiatePayment(@Body paymentRequest: PaymentRequest): Response<PaymentResponse>
    
    @POST("payments/requests/{request_id}/status/")
    suspend fun checkPaymentStatus(@Path("request_id") requestId: String): Response<PaymentStatusResponse>
    
    // Church Information
    @GET("mobile/church-info/")
    suspend fun getChurchInfo(): Response<ChurchInfoResponse>
    
    @GET("mobile/quick-actions/")
    suspend fun getQuickActions(): Response<QuickActionsResponse>
    
    // Notifications
    @GET("mobile/notifications/")
    suspend fun getNotifications(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<NotificationListResponse>
    
    @POST("mobile/notifications/{id}/")
    suspend fun markNotificationRead(@Path("id") notificationId: Int): Response<SuccessResponse>
    
    // Analytics
    @POST("mobile/analytics/track/")
    suspend fun trackAnalytics(@Body analyticsRequest: AnalyticsRequest): Response<SuccessResponse>
    
    // Feedback
    @POST("mobile/feedback/submit/")
    suspend fun submitFeedback(@Body feedbackRequest: FeedbackRequest): Response<FeedbackResponse>
}
