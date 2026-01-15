package com.altarfunds.mobile.ui.adapters

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.altarfunds.mobile.databinding.ItemChurchBinding
import com.altarfunds.mobile.models.ChurchInfo

class ChurchInfoAdapter(
    private val onChurchClick: (ChurchInfo) -> Unit = {}
) : ListAdapter<ChurchInfo, ChurchInfoAdapter.ViewHolder>(DiffCallback) {

    // Constructor for SettingsActivity
    constructor(churches: List<ChurchInfo>) : this({}) {
        submitList(churches)
    }

    fun updateChurches(churches: List<ChurchInfo>) {
        submitList(churches)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemChurchBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(
        private val binding: ItemChurchBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(church: ChurchInfo) {
            binding.apply {
                tvChurchName.text = church.name
                tvChurchCode.text = church.code
                tvChurchDescription.text = church.description
                
                // Set verification status
                if (church.is_verified) {
                    tvVerificationStatus.text = "Verified"
                    tvVerificationStatus.setTextColor(android.graphics.Color.parseColor("#FFA500"))
                } else {
                    tvVerificationStatus.text = "Not Verified"
                    tvVerificationStatus.setTextColor(android.graphics.Color.YELLOW)
                }
                
                // Set active status
                if (church.is_active) {
                    tvActiveStatus.text = "Active"
                    tvActiveStatus.setTextColor(android.graphics.Color.GREEN)
                } else {
                    tvActiveStatus.text = "Inactive"
                    tvActiveStatus.setTextColor(android.graphics.Color.RED)
                }
                
                root.setOnClickListener {
                    onChurchClick(church)
                }
            }
        }
    }

    companion object {
        private val DiffCallback = object : DiffUtil.ItemCallback<ChurchInfo>() {
            override fun areItemsTheSame(
                oldItem: ChurchInfo,
                newItem: ChurchInfo
            ): Boolean {
                return oldItem.id == newItem.id
            }

            override fun areContentsTheSame(
                oldItem: ChurchInfo,
                newItem: ChurchInfo
            ): Boolean {
                return oldItem == newItem
            }
        }
    }
}
