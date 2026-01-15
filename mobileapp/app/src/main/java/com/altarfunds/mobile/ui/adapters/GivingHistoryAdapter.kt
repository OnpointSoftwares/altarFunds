package com.altarfunds.mobile.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.altarfunds.mobile.R
import com.altarfunds.mobile.models.GivingTransaction
import java.text.SimpleDateFormat
import java.util.*

class GivingHistoryAdapter(private var transactions: List<GivingTransaction>) : 
    RecyclerView.Adapter<GivingHistoryAdapter.TransactionViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TransactionViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_giving_history, parent, false)
        return TransactionViewHolder(view)
    }

    override fun onBindViewHolder(holder: TransactionViewHolder, position: Int) {
        holder.bind(transactions[position])
    }

    override fun getItemCount(): Int = transactions.size

    fun updateTransactions(newTransactions: List<GivingTransaction>) {
        transactions = newTransactions
        notifyDataSetChanged()
    }

    class TransactionViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvTransactionCategory: TextView = itemView.findViewById(R.id.tv_transaction_category)
        private val tvTransactionAmount: TextView = itemView.findViewById(R.id.tv_transaction_amount)
        private val tvTransactionDate: TextView = itemView.findViewById(R.id.tv_transaction_date)
        private val tvTransactionStatus: TextView = itemView.findViewById(R.id.tv_transaction_status)

        fun bind(transaction: GivingTransaction) {
            tvTransactionCategory.text = transaction.category_name ?: "General"
            tvTransactionAmount.text = "KES %.2f".format(transaction.amount)
            
            val dateFormat = SimpleDateFormat("MMM dd, yyyy HH:mm", Locale.getDefault())
            tvTransactionDate.text = dateFormat.format(transaction.date)
            
            tvTransactionStatus.text = transaction.status.replace("_", " ").capitalize()
            tvTransactionStatus.setTextColor(
                when (transaction.status) {
                    "completed" -> itemView.context.getColor(android.R.color.holo_green_dark)
                    "pending" -> itemView.context.getColor(android.R.color.holo_orange_dark)
                    "failed" -> itemView.context.getColor(android.R.color.holo_red_dark)
                    else -> itemView.context.getColor(android.R.color.darker_gray)
                }
            )
        }
    }
}
