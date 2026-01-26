package com.altarfunds.mobile.api

import com.altarfunds.mobile.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiInterface {
    
    // Web Backend Authentication Endpoints
    @POST("mobile/login/")
    suspend fun login(@Body loginRequest: LoginRequest): Response<LoginResponse>

    @POST("accounts/logout/")
    suspend fun logout(): Response<Void>

    @POST("accounts/register/")
    suspend fun register(@Body registerRequest: RegisterRequest): Response<LoginResponse>

    @GET("accounts/profile/")
    suspend fun getCurrentUser(): Response<User>

    // Web Backend Dashboard Endpoints
    @GET("dashboard/financial-summary/")
    suspend fun getFinancialSummary(): Response<FinancialSummary>

    @GET("dashboard/monthly-trend/")
    suspend fun getMonthlyTrend(): Response<List<ChartData>>

    @GET("dashboard/income-breakdown/")
    suspend fun getIncomeBreakdown(): Response<List<ChartData>>

    @GET("dashboard/expense-breakdown/")
    suspend fun getExpenseBreakdown(): Response<List<ChartData>>

    // Web Backend Donations Endpoints
    @GET("donations/")
    suspend fun getDonations(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("type") type: String? = null,
        @Query("date_from") dateFrom: String? = null,
        @Query("date_to") dateTo: String? = null
    ): Response<DonationListResponse>

    @POST("donations/")
    suspend fun createDonation(@Body donation: Donation): Response<Donation>

    @PUT("donations/{id}/")
    suspend fun updateDonation(@Path("id") id: String, @Body donation: Donation): Response<Donation>

    @DELETE("donations/{id}/")
    suspend fun deleteDonation(@Path("id") id: String): Response<Void>

    // Web Backend Expenses Endpoints
    @GET("expenses/")
    suspend fun getExpenses(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("category") category: String? = null,
        @Query("status") status: String? = null,
        @Query("date_from") dateFrom: String? = null,
        @Query("date_to") dateTo: String? = null
    ): Response<ExpenseListResponse>

    @POST("expenses/")
    suspend fun createExpense(@Body expense: Expense): Response<Expense>

    @PUT("expenses/{id}/")
    suspend fun updateExpense(@Path("id") id: String, @Body expense: Expense): Response<Expense>

    @POST("expenses/{id}/approve/")
    suspend fun approveExpense(@Path("id") id: String): Response<Expense>

    @POST("expenses/{id}/reject/")
    suspend fun rejectExpense(@Path("id") id: String, @Body reason: RejectReasonRequest): Response<Expense>

    // Web Backend Budgets Endpoints
    @GET("budgets/")
    suspend fun getBudgets(
        @Query("year") year: Int? = null,
        @Query("department") department: String? = null
    ): Response<BudgetListResponse>

    @POST("budgets/")
    suspend fun createBudget(@Body budget: Budget): Response<Budget>

    @PUT("budgets/{id}/")
    suspend fun updateBudget(@Path("id") id: String, @Body budget: Budget): Response<Budget>

    // Web Backend Members Endpoints
    @GET("members/")
    suspend fun getMembers(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("search") search: String? = null
    ): Response<MemberListResponse>

    // Mobile-specific endpoints (keep existing ones for backward compatibility)
    @POST("mobile/login/")
    suspend fun mobileLogin(@Body loginRequest: LoginRequest): Response<LoginResponse>

    @POST("mobile/google-login/")
    suspend fun googleLogin(@Body googleLoginRequest: GoogleLoginRequest): Response<LoginResponse>

    @POST("mobile/register/")
    suspend fun mobileRegister(@Body registerRequest: RegisterRequest): Response<LoginResponse>
    
    @POST("mobile/register-device/")
    suspend fun registerDevice(@Body deviceRequest: DeviceRegistrationRequest): Response<DeviceRegistrationResponse>
    
    // App Configuration
    @GET("mobile/config/")
    suspend fun getAppConfig(@Query("platform") platform: String = "android"): Response<AppConfigResponse>
    
    // User Profile
    @GET("mobile/profile/")
    suspend fun getUserProfile(): Response<UserProfileResponse>
    
    // Comprehensive Giving Features
    @GET("mobile/giving-summary/")
    suspend fun getGivingSummary(): Response<GivingSummaryResponse>
    
    // Enhanced Dashboard
    @GET("mobile/dashboard/")
    suspend fun getEnhancedDashboard(): Response<EnhancedDashboardResponse>
    
    @POST("mobile/giving/initiate/")
    suspend fun initiateGiving(@Body givingRequest: ComprehensiveGivingRequest): Response<PaymentInitiationResponse>
    
    @POST("mobile/giving/mpesa/")
    suspend fun initiateMpesaPayment(@Body mpesaRequest: MpesaPaymentRequest): Response<MpesaPaymentResponse>
    
    @POST("mobile/giving/airtel/")
    suspend fun initiateAirtelPayment(@Body airtelRequest: AirtelPaymentRequest): Response<AirtelPaymentResponse>
    
    @POST("mobile/giving/ussd/")
    suspend fun initiateUssdPayment(@Body ussdRequest: USSDPaymentRequest): Response<USSDPaymentResponse>
    
    @POST("mobile/giving/qr/")
    suspend fun generateQRCode(@Body qrRequest: QRCodeRequest): Response<QRCodeResponse>
    
    @POST("mobile/giving/recurring/")
    suspend fun setupRecurringGiving(@Body recurringRequest: RecurringGivingRequest): Response<RecurringGivingResponse>
    
    @GET("mobile/giving/recurring/")
    suspend fun getRecurringGiving(): Response<RecurringGivingListResponse>
    
    @GET("mobile/giving/transactions/")
    suspend fun getGivingTransactions(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("category") category: String? = null,
        @Query("date_from") dateFrom: String? = null,
        @Query("date_to") dateTo: String? = null
    ): Response<TransactionListResponse>
    
    @GET("mobile/giving/statements/")
    suspend fun getGivingStatements(
        @Query("month") month: Int? = null,
        @Query("year") year: Int? = null
    ): Response<GivingStatementResponse>
    
    @POST("giving/transactions/")
    suspend fun createGivingTransaction(@Body transactionRequest: GivingTransactionRequest): Response<ApiResponse<GivingTransactionResponse>>
    
    @POST("payments/requests/")
    suspend fun initiatePayment(@Body paymentRequest: PaymentRequest): Response<PaymentResponse>
    
    @POST("payments/requests/{request_id}/status/")
    suspend fun checkPaymentStatus(@Path("request_id") requestId: String): Response<PaymentStatusResponse>
    
    // Pledges and Vows
    @POST("mobile/pledges/create/")
    suspend fun createPledge(@Body pledgeRequest: PledgeRequest): Response<PledgeResponse>
    
    @GET("mobile/pledges/")
    suspend fun getPledges(
        @Query("status") status: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<PledgeListResponse>
    
    @POST("mobile/pledges/{id}/fulfill/")
    suspend fun fulfillPledge(@Path("id") pledgeId: Int, @Body fulfillmentRequest: PledgeFulfillmentRequest): Response<PledgeResponse>
    
    // Church Management
    @GET("mobile/church-info/")
    suspend fun getChurchInfo(): Response<ChurchInfoResponse>
    
    @GET("churches/")
    suspend fun searchChurches(
        @Query("search") query: String,
        @Query("location") location: String? = null
    ): Response<ChurchSearchResponse>
    
    @POST("mobile/church/transfer/")
    suspend fun transferChurch(@Body transferRequest: ChurchTransferRequest): Response<ChurchTransferResponse>
    
    @POST("mobile/church/join/")
    suspend fun joinChurch(@Body joinRequest: ChurchJoinRequest): Response<ChurchJoinResponse>
    
    // Notifications and Reminders
    @GET("mobile/notifications/")
    suspend fun getNotifications(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("type") type: String? = null
    ): Response<NotificationListResponse>
    
    @POST("mobile/notifications/{id}/")
    suspend fun markNotificationRead(@Path("id") notificationId: Int): Response<SuccessResponse>
    
    @POST("mobile/notifications/reminders/setup/")
    suspend fun setupReminders(@Body reminderRequest: ReminderSetupRequest): Response<ReminderResponse>
    
    @GET("mobile/notifications/reminders/")
    suspend fun getReminders(): Response<ReminderListResponse>
    
    // Security and PIN System
    @POST("mobile/pin/create/")
    suspend fun createPIN(@Body pinRequest: PINCreateRequest): Response<PINResponse>
    
    @POST("mobile/pin/verify/")
    suspend fun verifyPIN(@Body pinVerifyRequest: PINVerifyRequest): Response<PINVerifyResponse>
    
    @POST("mobile/pin/change/")
    suspend fun changePIN(@Body pinChangeRequest: PINChangeRequest): Response<PINResponse>
    
    @GET("mobile/financial-reports/")
    suspend fun getFinancialReports(@Query("pin") pin: String): Response<FinancialReportsResponse>
    
    // Quick Actions
    @GET("mobile/quick-actions/")
    suspend fun getQuickActions(): Response<QuickActionsResponse>
    
    // Analytics
    @POST("mobile/analytics/track/")
    suspend fun trackAnalytics(@Body analyticsRequest: AnalyticsRequest): Response<SuccessResponse>
    
    // Feedback
    @POST("mobile/feedback/submit/")
    suspend fun submitFeedback(@Body feedbackRequest: FeedbackRequest): Response<FeedbackResponse>
    
    // Receipt Management
    @GET("mobile/receipts/")
    suspend fun getReceipts(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): Response<ReceiptListResponse>
    
    @POST("mobile/receipts/{id}/resend/")
    suspend fun resendReceipt(@Path("id") receiptId: String): Response<ReceiptResendResponse>
    
    // ============ NEW BACKEND API ENDPOINTS ============
    
    // Authentication
    @POST("auth/token/")
    suspend fun loginBackend(@Body credentials: LoginCredentials): Response<TokenResponse>
    
    @POST("auth/token/refresh/")
    suspend fun refreshToken(@Body refresh: RefreshToken): Response<AccessTokenResponse>
    
    @GET("accounts/profile/")
    suspend fun getProfile(): Response<ApiResponse<UserProfile>>
    
    @PUT("accounts/profile/")
    suspend fun updateProfile(@Body profile: ProfileUpdate): Response<ApiResponse<UserProfile>>
    
    // Churches
    @GET("churches/")
    suspend fun getChurches(
        @Query("search") search: String? = null,
        @Query("page") page: Int? = null
    ): Response<ApiResponse<ChurchList>>
    
    @GET("churches/{id}/")
    suspend fun getChurchDetails(@Path("id") churchId: Int): Response<ApiResponse<Church>>
    
    @POST("churches/{id}/join/")
    suspend fun joinChurchBackend(@Path("id") churchId: Int): Response<ApiResponse<JoinChurchResponse>>
    
    @POST("churches/transfer/")
    suspend fun transferChurchBackend(@Body transfer: TransferChurchRequest): Response<ApiResponse<TransferChurchResponse>>
    
    @GET("churches/pending-approval/")
    suspend fun getPendingChurches(): Response<ApiResponse<ChurchList>>
    
    @POST("churches/{id}/approve/")
    suspend fun approveChurch(@Path("id") churchId: Int): Response<ApiResponse<Church>>
    
    @POST("churches/{id}/reject/")
    suspend fun rejectChurch(@Path("id") churchId: Int, @Body reason: RejectReason): Response<ApiResponse<Church>>
    
    @GET("churches/{id}/members/")
    suspend fun getChurchMembers(@Path("id") churchId: Int): Response<ApiResponse<MemberList>>
    
    // Giving
    @GET("giving/transactions/history/")
    suspend fun getGivingHistoryBackend(
        @Query("start_date") startDate: String? = null,
        @Query("end_date") endDate: String? = null
    ): Response<ApiResponse<GivingHistory>>
    
    @GET("giving/transactions/summary/")
    suspend fun getGivingSummaryBackend(): Response<ApiResponse<GivingSummary>>
    
    @POST("giving/transactions/")
    suspend fun createGivingBackend(@Body giving: CreateGiving): Response<ApiResponse<GivingTransaction>>
    
    @GET("giving/categories/")
    suspend fun getGivingCategories(): Response<ApiResponse<List<GivingCategory>>>
    
    @GET("giving/church/{id}/")
    suspend fun getChurchGivings(@Path("id") churchId: Int): Response<ApiResponse<GivingHistory>>
    
    // Payments
    @POST("payments/payments/initialize_paystack/")
    suspend fun initializePaystack(@Body payment: PaystackInitRequest): Response<ApiResponse<PaystackInitResponse>>
    
    @GET("payments/payments/verify_payment/")
    suspend fun verifyPaystackPayment(@Query("reference") reference: String): Response<ApiResponse<PaymentVerification>>
    
    // Reports
    @GET("reports/financial-summary/")
    suspend fun getFinancialSummaryBackend(): Response<ApiResponse<FinancialSummaryReport>>
    
    @GET("reports/giving-trends/")
    suspend fun getGivingTrends(@Query("period") period: String = "monthly"): Response<ApiResponse<GivingTrends>>
    
    @GET("reports/member-statistics/")
    suspend fun getMemberStatistics(): Response<ApiResponse<MemberStatistics>>
    
    @GET("reports/church-performance/")
    suspend fun getChurchPerformance(): Response<ApiResponse<ChurchPerformance>>
    
    @GET("reports/system-overview/")
    suspend fun getSystemOverview(): Response<ApiResponse<SystemOverview>>
}
