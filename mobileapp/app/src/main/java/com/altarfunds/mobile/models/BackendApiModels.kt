package com.altarfunds.mobile.models

// Generic API Response Wrapper for backend
data class ApiResponse<T>(
    val success: Boolean,
    val data: T?,
    val message: String?
)

// Authentication Models
data class LoginCredentials(
    val email: String,
    val password: String
)

data class TokenResponse(
    val access: String,
    val refresh: String
)

data class RefreshToken(
    val refresh: String
)

data class AccessTokenResponse(
    val access: String
)

// User Profile Models
data class UserProfile(
    val id: Int,
    val email: String,
    val first_name: String,
    val last_name: String,
    val phone_number: String?,
    val role: String,
    val church: ChurchBasic?
)

data class ProfileUpdate(
    val first_name: String,
    val last_name: String,
    val phone_number: String?
)

// Church Models
data class ChurchBasic(
    val id: Int,
    val name: String
)

data class ChurchList(
    val count: Int,
    val next: String?,
    val previous: String?,
    val results: List<ChurchDetail>
)

data class ChurchDetail(
    val id: Int,
    val name: String,
    val location: String?,
    val address: String?,
    val status: String,
    val member_count: Int?,
    val denomination: String?
)

data class JoinChurchResponse(
    val message: String,
    val church: ChurchDetail
)

data class TransferChurchRequest(
    val from_church_id: Int,
    val to_church_id: Int,
    val reason: String
)

data class TransferChurchResponse(
    val message: String,
    val reference: String
)

data class RejectReason(
    val reason: String
)

data class MemberList(
    val count: Int,
    val members: List<MemberDetail>
)

data class MemberDetail(
    val id: Int,
    val user: UserProfile,
    val joined_date: String
)

// Giving Models
data class GivingHistory(
    val total_given: Double,
    val transaction_count: Int,
    val givings: List<GivingTransactionDetail>
)

data class GivingTransactionDetail(
    val id: Int,
    val amount: Double,
    val category: GivingCategoryDetail,
    val transaction_date: String,
    val status: String,
    val payment_method: String?,
    val reference: String?
)

data class GivingCategoryDetail(
    val id: Int,
    val name: String,
    val description: String?,
    val is_active: Boolean
)

data class GivingSummary(
    val year: Int,
    val total_given: Double,
    val transaction_count: Int,
    val by_category: List<CategorySummary>,
    val monthly_totals: List<MonthlyTotal>
)

data class CategorySummary(
    val category__name: String,
    val total: Double,
    val count: Int
)

data class MonthlyTotal(
    val month: Int,
    val total: Double,
    val count: Int
)

data class CreateGiving(
    val amount: Double,
    val giving_type: String,
    val church_id: Int,
    val note: String?
)

// Payment Models
data class PaystackInitRequest(
    val amount: Double,
    val giving_type: String,
    val church_id: Int
)

data class PaystackInitResponse(
    val authorization_url: String,
    val access_code: String,
    val reference: String
)

data class PaymentVerification(
    val status: String,
    val amount: Double,
    val reference: String,
    val paid_at: String?
)

// Report Models
data class FinancialSummaryReport(
    val total_income: Double,
    val total_expenses: Double,
    val net_income: Double,
    val budget_utilization: Double,
    val income_by_category: List<CategorySummary>,
    val expenses_by_category: List<CategorySummary>
)

data class GivingTrends(
    val trends: List<TrendDataDetail>,
    val by_type: List<CategorySummary>
)

data class TrendDataDetail(
    val period: String,
    val total: Double,
    val count: Int
)

data class MemberStatistics(
    val total_members: Int,
    val active_members: Int,
    val new_members_this_month: Int,
    val tithe_payers: Int,
    val growth_trend: List<GrowthData>
)

data class GrowthData(
    val month: String,
    val count: Int
)

data class ChurchPerformance(
    val church_name: String,
    val total_giving: Double,
    val total_expenses: Double,
    val net_income: Double,
    val member_count: Int,
    val average_giving_per_member: Double
)

data class SystemOverview(
    val total_churches: Int,
    val active_churches: Int,
    val pending_churches: Int,
    val total_members: Int,
    val total_income: Double,
    val total_expenses: Double
)
