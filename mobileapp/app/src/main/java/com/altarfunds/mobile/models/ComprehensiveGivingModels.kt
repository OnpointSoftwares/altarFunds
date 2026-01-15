package com.altarfunds.mobile.models

// Comprehensive Giving Request Models
data class ComprehensiveGivingRequest(
    val amount: Double,
    val category_id: Int,
    val payment_method: String, // "mpesa", "airtel", "card", "ussd", "qr"
    val phone_number: String? = null,
    val card_token: String? = null,
    val is_anonymous: Boolean = false,
    val is_recurring: Boolean = false,
    val recurring_frequency: String? = null, // "weekly", "monthly", "annual"
    val recurring_start_date: String? = null,
    val notes: String? = null
)

data class MpesaPaymentRequest(
    val amount: Double,
    val phone_number: String,
    val category_id: Int,
    val is_anonymous: Boolean = false,
    val notes: String? = null
)

data class AirtelPaymentRequest(
    val amount: Double,
    val phone_number: String,
    val category_id: Int,
    val is_anonymous: Boolean = false,
    val notes: String? = null
)

data class USSDPaymentRequest(
    val amount: Double,
    val ussd_code: String,
    val category_id: Int,
    val is_anonymous: Boolean = false,
    val notes: String? = null
)

data class QRCodeRequest(
    val amount: Double,
    val category_id: Int,
    val expires_in_hours: Int = 24,
    val single_use: Boolean = true,
    val notes: String? = null
)

data class RecurringGivingRequest(
    val amount: Double,
    val category_id: Int,
    val frequency: String, // "weekly", "monthly", "annual"
    val start_date: String,
    val end_date: String? = null,
    val payment_method: String,
    val phone_number: String? = null,
    val card_token: String? = null,
    val is_anonymous: Boolean = false
)

// Response Models
data class PaymentInitiationResponse(
    val success: Boolean,
    val message: String,
    val payment_request_id: String? = null,
    val payment_instructions: PaymentInstructions? = null
)

data class PaymentInstructions(
    val method: String,
    val instructions: String,
    val reference_number: String? = null,
    val expires_at: String? = null
)

data class MpesaPaymentResponse(
    val success: Boolean,
    val message: String,
    val mpesa_reference: String? = null,
    val merchant_request_id: String? = null,
    val checkout_request_id: String? = null
)

data class AirtelPaymentResponse(
    val success: Boolean,
    val message: String,
    val airtel_reference: String? = null,
    val transaction_id: String? = null
)

data class USSDPaymentResponse(
    val success: Boolean,
    val message: String,
    val ussd_code: String,
    val confirmation_code: String? = null
)

data class QRCodeResponse(
    val success: Boolean,
    val message: String,
    val qr_code_url: String? = null,
    val qr_code_data: String? = null,
    val expires_at: String? = null
)

data class RecurringGivingResponse(
    val success: Boolean,
    val message: String,
    val recurring_giving_id: String? = null,
    val next_payment_date: String? = null
)

data class RecurringGivingListResponse(
    val success: Boolean,
    val message: String,
    val recurring_givings: List<RecurringGiving>
)

data class RecurringGiving(
    val id: String,
    val amount: Double,
    val frequency: String,
    val category_name: String,
    val next_payment_date: String,
    val status: String, // "active", "paused", "completed"
    val start_date: String,
    val total_given: Double,
    val remaining_amount: Double
)

data class GivingStatementResponse(
    val success: Boolean,
    val message: String,
    val period: String,
    val total_giving: Double,
    val total_tithe: Double,
    val total_offering: Double,
    val total_missions: Double,
    val transactions: List<GivingTransaction>
)

// Pledge Models
data class PledgeRequest(
    val amount: Double,
    val pledge_type: String, // "general", "building", "missions", "welfare"
    val description: String,
    val target_date: String? = null,
    val is_public: Boolean = false,
    val payment_method: String? = null
)

data class PledgeResponse(
    val success: Boolean,
    val message: String,
    val pledge_id: String? = null
)

data class PledgeListResponse(
    val success: Boolean,
    val message: String,
    val pledges: List<Pledge>
)

data class Pledge(
    val id: String,
    val amount: Double,
    val pledge_type: String,
    val description: String,
    val target_date: String,
    val status: String, // "pending", "partial", "fulfilled"
    val amount_paid: Double,
    val remaining_amount: Double,
    val created_at: String,
    val is_public: Boolean
)

data class PledgeFulfillmentRequest(
    val amount: Double,
    val payment_method: String,
    val transaction_reference: String? = null,
    val notes: String? = null
)

// Church Management Models
data class ChurchTransferRequest(
    val target_church_id: Int,
    val target_church_code: String,
    val reason: String,
    val verification_code: String? = null
)

data class ChurchTransferResponse(
    val success: Boolean,
    val message: String,
    val transfer_id: String? = null,
    val verification_required: Boolean,
    val verification_method: String? = null
)

data class ChurchSearchResponse(
    val success: Boolean,
    val message: String,
    val churches: List<ChurchSearchResult>
)

data class ChurchSearchResult(
    val id: Int,
    val name: String,
    val code: String,
    val location: String,
    val distance: Double? = null,
    val member_count: Int,
    val is_verified: Boolean
)

data class ChurchJoinRequest(
    val church_id: Int,
    val church_code: String,
    val verification_method: String, // "code", "phone", "id"
    val verification_data: String
)

data class ChurchJoinResponse(
    val success: Boolean,
    val message: String,
    val requires_approval: Boolean,
    val approval_method: String? = null
)

// PIN System Models
data class PINCreateRequest(
    val pin: String,
    val confirm_pin: String,
    val security_question: String,
    val security_answer: String
)

data class PINVerifyRequest(
    val pin: String,
    val purpose: String // "financial_reports", "settings_change", etc.
)

data class PINChangeRequest(
    val current_pin: String,
    val new_pin: String,
    val confirm_new_pin: String
)

data class PINResponse(
    val success: Boolean,
    val message: String,
    val attempts_remaining: Int? = null
)

data class PINVerifyResponse(
    val success: Boolean,
    val message: String,
    val access_granted: Boolean,
    val expires_at: String? = null
)

data class FinancialReportsResponse(
    val success: Boolean,
    val message: String,
    val reports: FinancialReports
)

data class FinancialReports(
    val giving_summary: GivingSummaryResponse,
    val income_statement: IncomeStatement,
    val expense_summary: ExpenseSummary,
    val member_contributions: List<MemberContribution>
)

data class IncomeStatement(
    val period: String,
    val total_income: Double,
    val income_by_category: Map<String, Double>,
    val growth_rate: Double
)

data class ExpenseSummary(
    val period: String,
    val total_expenses: Double,
    val expenses_by_category: Map<String, Double>,
    val budget_utilization: Map<String, Double>
)

data class MemberContribution(
    val member_name: String,
    val total_contribution: Double,
    val contribution_rank: Int,
    val last_contribution_date: String
)

// Reminder Models
data class ReminderSetupRequest(
    val giving_reminders: Boolean = true,
    val reminder_frequency: String, // "daily", "weekly", "monthly"
    val reminder_time: String, // "09:00"
    val pledge_reminders: Boolean = true,
    val event_reminders: Boolean = true
)

data class ReminderResponse(
    val success: Boolean,
    val message: String
)

data class ReminderListResponse(
    val success: Boolean,
    val message: String,
    val reminders: List<Reminder>
)

data class Reminder(
    val id: String,
    val type: String, // "giving", "pledge", "event"
    val title: String,
    val message: String,
    val scheduled_time: String,
    val is_active: Boolean,
    val next_trigger: String
)

// Receipt Models
data class ReceiptListResponse(
    val success: Boolean,
    val message: String,
    val receipts: List<Receipt>
)

data class Receipt(
    val id: String,
    val transaction_id: String,
    val amount: Double,
    val category: String,
    val payment_method: String,
    val date: String,
    val receipt_number: String,
    val sent_via: List<String>, // ["sms", "email", "whatsapp"]
    val is_anonymous: Boolean
)

data class ReceiptResendResponse(
    val success: Boolean,
    val message: String,
    val resent_via: List<String>
)

// Enhanced Giving Models
data class GivingTransaction(
    val id: String,
    val amount: Double,
    val category_name: String,
    val payment_method: String,
    val status: String,
    val date: String,
    val receipt_number: String? = null,
    val is_anonymous: Boolean,
    val is_recurring: Boolean,
    val notes: String? = null
)
