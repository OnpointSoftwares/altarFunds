package com.altarfunds.mobile.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ProgressBar
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.altarfunds.mobile.R
import com.altarfunds.mobile.models.Budget

class BudgetAdapter(
    private var budgets: List<Budget>,
    private val onBudgetClick: (Budget) -> Unit
) : RecyclerView.Adapter<BudgetAdapter.BudgetViewHolder>() {

    class BudgetViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val budgetName: TextView = itemView.findViewById(R.id.budget_name)
        val budgetCategory: TextView = itemView.findViewById(R.id.budget_category)
        val budgetAmount: TextView = itemView.findViewById(R.id.tv_budget_amount)
        val budgetSpent: TextView = itemView.findViewById(R.id.tv_spent_amount)
        val budgetRemaining: TextView = itemView.findViewById(R.id.tv_remaining_amount)
        val budgetProgress: ProgressBar = itemView.findViewById(R.id.budget_progress)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): BudgetViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_budget, parent, false)
        return BudgetViewHolder(view)
    }

    override fun onBindViewHolder(holder: BudgetViewHolder, position: Int) {
        val budget = budgets[position]
        holder.budgetName.text = budget.name
        holder.budgetCategory.text = budget.category
        holder.budgetAmount.text = "₦${String.format("%.2f", budget.amount)}"
        holder.budgetSpent.text = "Spent: ₦${String.format("%.2f", budget.spent)}"
        holder.budgetRemaining.text = "Remaining: ₦${String.format("%.2f", budget.remaining)}"
        
        val progress = if (budget.amount > 0) (budget.spent / budget.amount * 100).toInt() else 0
        holder.budgetProgress.progress = progress
        
        holder.itemView.setOnClickListener {
            onBudgetClick(budget)
        }
    }

    override fun getItemCount(): Int = budgets.size

    fun updateData(newBudgets: List<Budget>) {
        budgets = newBudgets
        notifyDataSetChanged()
    }
}
