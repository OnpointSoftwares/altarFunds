package com.altarfunds.mobile.api

import com.altarfunds.mobile.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiInterface {
    
    // Authentication
    @POST("api/mobile/login/")
    suspend fun login(@Body loginRequest: LoginRequest): Response<LoginResponse>

    @POST("api/mobile/google-login/")
    suspend fun googleLogin(@Body googleLoginRequest: GoogleLoginRequest): Response<LoginResponse>

    @POST("api/mobile/register/")
    suspend fun register(@Body registerRequest: RegisterRequest): Response<LoginResponse>
    
    @POST("api/mobile/register-device/")
    suspend fun registerDevice(@Body deviceRequest: DeviceRegistrationRequest): Response<DeviceRegistrationResponse>
    
    // App Configuration
    @GET("api/mobile/config/")
    suspend fun getAppConfig(@Query("platform") platform: String = "android"): Response<AppConfigResponse>
    
    // User Profile
    @GET("api/mobile/profile/")
    suspend fun getUserProfile(): Response<UserProfileResponse>
    
    // Comprehensive Giving Features
    @GET("api/mobile/giving/summary/")
    suspend fun getGivingSummary(): Response<GivingSummaryResponse>
    
    @POST("api/mobile/giving/initiate/")
    suspend fun initiateGiving(@Body givingRequest: ComprehensiveGivingRequest): Response<PaymentInitiationResponse>
    
    @POST("api/mobile/giving/mpesa/")
    suspend fun initiateMpesaPayment(@Body mpesaRequest: MpesaPaymentRequest): Response<MpesaPaymentResponse>
    
    @POST("api/mobile/giving/airtel/")
    suspend fun initiateAirtelPayment(@Body airtelRequest: AirtelPaymentRequest): Response<AirtelPaymentResponse>
    
    @POST("api/mobile/giving/ussd/")
    suspend fun initiateUssdPayment(@Body ussdRequest: USSDPaymentRequest): Response<USSDPaymentResponse>
    
    @POST("api/mobile/giving/qr/")
    suspend fun generateQRCode(@Body qrRequest: QRCodeRequest): Response<QRCodeResponse>
    
    @POST("api/mobile/giving/recurring/")
    suspend fun setupRecurringGiving(@Body recurringRequest: RecurringGivingRequest): Response<RecurringGivingResponse>
    
    @GET("api/mobile/giving/recurring/")
    suspend fun getRecurringGiving(): Response<RecurringGivingListResponse>
    
    @GET("api/mobile/giving/transactions/")
    suspend fun getGivingTransactions(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("category") category: String? = null,
        @Query("date_from") dateFrom: String? = null,
        @Query("date_to") dateTo: String? = null
    ): Response<TransactionListResponse>
    
    @GET("api/mobile/giving/statements/")
    suspend fun getGivingStatements(
        @Query("month") month: Int? = null,
        @Query("year") year: Int? = null
    ): Response<GivingStatementResponse>
    
    @POST("api/giving/transactions/")
    suspend fun createGivingTransaction(@Body transactionRequest: GivingTransactionRequest): Response<GivingTransactionResponse>
    
    @POST("api/payments/requests/")
    suspend fun initiatePayment(@Body paymentRequest: PaymentRequest): Response<PaymentResponse>
    
    @POST("api/payments/requests/{request_id}/status/")
    suspend fun checkPaymentStatus(@Path("request_id") requestId: String): Response<PaymentStatusResponse>
    
    // Pledges and Vows
    @POST("api/mobile/pledges/create/")
    suspend fun createPledge(@Body pledgeRequest: PledgeRequest): Response<PledgeResponse>
    
    @GET("api/mobile/pledges/")
    suspend fun getPledges(
        @Query("status") status: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<PledgeListResponse>
    
    @POST("api/mobile/pledges/{id}/fulfill/")
    suspend fun fulfillPledge(@Path("id") pledgeId: Int, @Body fulfillmentRequest: PledgeFulfillmentRequest): Response<PledgeResponse>
    
    // Church Management
    @GET("api/mobile/church-info/")
    suspend fun getChurchInfo(): Response<ChurchInfoResponse>
    
    @GET("api/mobile/church/search/")
    suspend fun searchChurches(
        @Query("query") query: String,
        @Query("location") location: String? = null
    ): Response<ChurchSearchResponse>
    
    @POST("api/mobile/church/transfer/")
    suspend fun transferChurch(@Body transferRequest: ChurchTransferRequest): Response<ChurchTransferResponse>
    
    @POST("api/mobile/church/join/")
    suspend fun joinChurch(@Body joinRequest: ChurchJoinRequest): Response<ChurchJoinResponse>
    
    // Notifications and Reminders
    @GET("api/mobile/notifications/")
    suspend fun getNotifications(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("type") type: String? = null
    ): Response<NotificationListResponse>
    
    @POST("api/mobile/notifications/{id}/")
    suspend fun markNotificationRead(@Path("id") notificationId: Int): Response<SuccessResponse>
    
    @POST("api/mobile/notifications/reminders/setup/")
    suspend fun setupReminders(@Body reminderRequest: ReminderSetupRequest): Response<ReminderResponse>
    
    @GET("api/mobile/notifications/reminders/")
    suspend fun getReminders(): Response<ReminderListResponse>
    
    // Security and PIN System
    @POST("api/mobile/pin/create/")
    suspend fun createPIN(@Body pinRequest: PINCreateRequest): Response<PINResponse>
    
    @POST("api/mobile/pin/verify/")
    suspend fun verifyPIN(@Body pinVerifyRequest: PINVerifyRequest): Response<PINVerifyResponse>
    
    @POST("api/mobile/pin/change/")
    suspend fun changePIN(@Body pinChangeRequest: PINChangeRequest): Response<PINResponse>
    
    @GET("api/mobile/financial-reports/")
    suspend fun getFinancialReports(@Query("pin") pin: String): Response<FinancialReportsResponse>
    
    // Quick Actions
    @GET("api/mobile/quick-actions/")
    suspend fun getQuickActions(): Response<QuickActionsResponse>
    
    // Analytics
    @POST("api/mobile/analytics/track/")
    suspend fun trackAnalytics(@Body analyticsRequest: AnalyticsRequest): Response<SuccessResponse>
    
    // Feedback
    @POST("api/mobile/feedback/submit/")
    suspend fun submitFeedback(@Body feedbackRequest: FeedbackRequest): Response<FeedbackResponse>
    
    // Receipt Management
    @GET("api/mobile/receipts/")
    suspend fun getReceipts(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<ReceiptListResponse>
    
    @POST("api/mobile/receipts/{id}/resend/")
    suspend fun resendReceipt(@Path("id") receiptId: String): Response<ReceiptResendResponse>
}
