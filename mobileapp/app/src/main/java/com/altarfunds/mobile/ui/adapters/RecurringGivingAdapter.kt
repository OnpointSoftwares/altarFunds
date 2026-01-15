package com.altarfunds.mobile.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.altarfunds.mobile.R
import com.altarfunds.mobile.models.RecurringGiving
import java.text.SimpleDateFormat
import java.util.*

class RecurringGivingAdapter(private var recurringGivings: List<RecurringGiving>) : 
    RecyclerView.Adapter<RecurringGivingAdapter.RecurringGivingViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecurringGivingViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_recurring_giving, parent, false)
        return RecurringGivingViewHolder(view)
    }

    override fun onBindViewHolder(holder: RecurringGivingViewHolder, position: Int) {
        holder.bind(recurringGivings[position])
    }

    override fun getItemCount(): Int = recurringGivings.size

    fun updateRecurringGiving(newRecurringGivings: List<RecurringGiving>) {
        recurringGivings = newRecurringGivings
        notifyDataSetChanged()
    }

    class RecurringGivingViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvGivingTitle: TextView = itemView.findViewById(R.id.tv_giving_title)
        private val tvGivingAmount: TextView = itemView.findViewById(R.id.tv_giving_amount)
        private val tvGivingFrequency: TextView = itemView.findViewById(R.id.tv_giving_frequency)
        private val tvGivingNextDate: TextView = itemView.findViewById(R.id.tv_giving_next_date)
        private val tvGivingStatus: TextView = itemView.findViewById(R.id.tv_giving_status)

        fun bind(recurringGiving: RecurringGiving) {
            tvGivingTitle.text = recurringGiving.category_name ?: "General Giving"
            tvGivingAmount.text = "KES %.2f".format(recurringGiving.amount)
            tvGivingFrequency.text = "Frequency: " + recurringGiving.frequency.replace("_", " ").capitalize()
            
            val dateFormat = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
            tvGivingNextDate.text = "Next: " + dateFormat.format(recurringGiving.next_payment_date)
            
            tvGivingStatus.text = if (recurringGiving.status == "active") "Active" else "Paused"
            tvGivingStatus.setTextColor(
                if (recurringGiving.status == "active") 
                    itemView.context.getColor(android.R.color.holo_green_dark)
                else 
                    itemView.context.getColor(android.R.color.holo_red_dark)
            )
        }
    }
}
