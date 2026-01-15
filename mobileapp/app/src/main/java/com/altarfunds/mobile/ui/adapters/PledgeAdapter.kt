package com.altarfunds.mobile.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.altarfunds.mobile.R
import com.altarfunds.mobile.models.Pledge
import java.text.SimpleDateFormat
import java.util.*

class PledgeAdapter(private var pledges: List<Pledge>) : 
    RecyclerView.Adapter<PledgeAdapter.PledgeViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PledgeViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_pledge, parent, false)
        return PledgeViewHolder(view)
    }

    override fun onBindViewHolder(holder: PledgeViewHolder, position: Int) {
        holder.bind(pledges[position])
    }

    override fun getItemCount(): Int = pledges.size

    fun updatePledges(newPledges: List<Pledge>) {
        pledges = newPledges
        notifyDataSetChanged()
    }

    class PledgeViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvPledgeTitle: TextView = itemView.findViewById(R.id.tv_pledge_title)
        private val tvPledgeAmount: TextView = itemView.findViewById(R.id.tv_pledge_amount)
        private val tvPledgeProgress: TextView = itemView.findViewById(R.id.tv_pledge_progress)
        private val tvPledgeDeadline: TextView = itemView.findViewById(R.id.tv_pledge_deadline)

        fun bind(pledge: Pledge) {
            tvPledgeTitle.text = pledge.description
            tvPledgeAmount.text = "KES %.2f".format(pledge.amount)
            
            val progress = if (pledge.amount > 0) {
                (pledge.amount_paid / pledge.amount * 100).toInt()
            } else 0
            
            tvPledgeProgress.text = "$progress% (KES %.2f / KES %.2f)".format(pledge.amount_paid, pledge.amount)
            
            val dateFormat = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
            tvPledgeDeadline.text = "Target: " + dateFormat.format(pledge.target_date)
        }
    }
}
