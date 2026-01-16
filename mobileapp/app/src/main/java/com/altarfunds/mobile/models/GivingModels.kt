package com.altarfunds.mobile.models

data class LoginRequest(
    val email: String,
    val password: String,
    val device_token: String? = null,
    val device_type: String = "android",
    val device_id: String? = null,
    val app_version: String? = null,
    val os_version: String? = null
)

data class GoogleLoginRequest(
    val firebase_token: String,
    val device_token: String? = null,
    val device_type: String = "android",
    val device_id: String? = null,
    val app_version: String? = null,
    val os_version: String? = null
)

data class RegisterRequest(
    val email: String,
    val password: String,
    val password_confirm: String,
    val device_token: String? = null,
    val device_type: String = "android",
    val device_id: String? = null,
    val app_version: String? = null,
    val os_version: String? = null
)

data class LoginResponse(
    val access_token: String,
    val refresh_token: String,
    val session_id: String,
    val user: User,
    val member: Member?,
    val device: Device
)

data class DeviceRegistrationRequest(
    val device_token: String,
    val device_type: String = "android",
    val device_id: String? = null,
    val app_version: String? = null,
    val os_version: String? = null
)

data class DeviceRegistrationResponse(
    val message: String,
    val device: Device
)

data class ChurchJoinRequest(
    val church_name: String,
    val church_code: String,
    val user_id: String
)

data class AppConfigResponse(
    val app_name: String,
    val app_version: String,
    val api_base_url: String,
    val features: Map<String, Boolean>,
    val settings: Map<String, Any>,
    val update_info: UpdateInfo
)

data class UpdateInfo(
    val available: Boolean,
    val mandatory: Boolean,
    val latest_version: String?,
    val download_url: String?,
    val update_message: String?
)

data class UserProfileResponse(
    val user: User,
    val member: Member?,
    val devices: List<Device>,
    val church_info: ChurchInfo?,
    val permissions: List<String>
)

data class GivingSummaryResponse(
    val total_giving: Double,
    val this_month: Double,
    val this_year: Double,
    val last_transaction: LastTransaction?,
    val giving_categories: List<GivingCategorySummary>,
    val recurring_giving: List<RecurringGivingSummary>
)

data class LastTransaction(
    val id: String,
    val amount: Double,
    val category: String,
    val date: String,
    val status: String
)

data class GivingCategorySummary(
    val category__name: String,
    val category__id: Int,
    val total: Double,
    val count: Int
)

data class RecurringGivingSummary(
    val category__name: String,
    val frequency: String,
    val amount: Double,
    val next_payment_date: String
)

data class GivingTransactionRequest(
    val category: Int,
    val amount: Double,
    val payment_method: String = "mpesa",
    val note: String? = null,
    val is_anonymous: Boolean = false
)

data class GivingTransactionResponse(
    val transaction_id: String,
    val amount: Double,
    val category: GivingCategory,
    val status: String,
    val payment_method: String,
    val transaction_date: String,
    val note: String?
)

data class TransactionListResponse(
    val count: Int,
    val next: String?,
    val previous: String?,
    val results: List<GivingTransactionResponse>
)

data class PaymentRequest(
    val giving_transaction_id: String,
    val payment_method: String = "mpesa"
)

data class PaymentResponse(
    val message: String,
    val payment_request: PaymentRequestInfo
)

data class PaymentRequestInfo(
    val request_id: String,
    val status: String,
    val amount: Double
)

data class PaymentStatusResponse(
    val status: String,
    val message: String,
    val transaction_id: String,
    val amount: Double,
    val payment_method: String,
    val created_at: String,
    val processed_at: String?,
    val callback_data: Map<String, Any>?
)

data class ChurchInfoResponse(
    val id: String,
    val name: String,
    val code: String,
    val description: String,
    val logo: String?,
    val is_verified: Boolean,
    val is_active: Boolean,
    val contact_info: ContactInfo,
    val address: Address,
    val campuses: List<Campus>,
    val departments: List<Department>,
    val giving_categories: List<GivingCategory>,
    val upcoming_events: List<Event>
)

data class ContactInfo(
    val phone: String,
    val email: String,
    val website: String?
)

data class Address(
    val street: String,
    val city: String,
    val county: String,
    val country: String
)

data class Campus(
    val id: Int,
    val name: String,
    val address: String,
    val phone_number: String,
    val is_main_campus: Boolean
)

data class Department(
    val id: Int,
    val name: String,
    val description: String,
    val head_name: String
)

data class Event(
    val id: Int,
    val title: String,
    val description: String,
    val event_date: String,
    val location: String
)

data class QuickActionsResponse(
    val results: List<QuickAction>
)

data class QuickAction(
    val action_type: String,
    val title: String,
    val description: String,
    val icon: String,
    val color: String,
    val enabled: Boolean,
    val required_permissions: List<String>
)

data class NotificationListResponse(
    val count: Int,
    val next: String?,
    val previous: String?,
    val results: List<Notification>
)

data class Notification(
    val id: Int,
    val title: String,
    val message: String,
    val notification_type: String,
    val status: String,
    val created_at: String,
    val data: Map<String, Any>?
)

data class SuccessResponse(
    val message: String
)

data class AnalyticsRequest(
    val event_type: String,
    val event_name: String,
    val event_data: Map<String, Any>?,
    val screen_name: String?,
    val session_id: String?
)

data class FeedbackRequest(
    val feedback_type: String,
    val title: String,
    val description: String,
    val rating: Int?
)

data class FeedbackResponse(
    val message: String,
    val feedback_id: Int
)

// Base models
data class User(
    val id: String,
    val email: String,
    val first_name: String,
    val last_name: String,
    val phone_number: String?,
    val role: String,
    val is_active: Boolean
)

data class Member(
    val id: String,
    val membership_number: String,
    val member_type: String,
    val join_date: String,
    val is_active: Boolean,
    val church: ChurchInfo
)

data class Device(
    val id: Int,
    val device_token: String,
    val device_type: String,
    val device_id: String?,
    val app_version: String?,
    val os_version: String?,
    val status: String,
    val last_seen: String?
)

data class ChurchInfo(
    val id: String,
    val name: String,
    val code: String,
    val logo: String?,
    val is_verified: Boolean,
    val is_active: Boolean,
    val description: String
)

data class GivingCategory(
    val id: Int,
    val name: String,
    val description: String?,
    val is_tax_deductible: Boolean,
    val is_active: Boolean
)
