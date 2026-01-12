package com.altarfunds.mobile.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.altarfunds.mobile.data.dao.ChurchDao
import com.altarfunds.mobile.data.dao.GivingCategoryDao
import com.altarfunds.mobile.data.dao.GivingTransactionDao
import com.altarfunds.mobile.data.dao.NotificationDao
import com.altarfunds.mobile.data.entities.GivingTransactionEntity
import com.altarfunds.mobile.data.entities.GivingCategoryEntity
import com.altarfunds.mobile.data.entities.ChurchEntity
import com.altarfunds.mobile.data.entities.NotificationEntity

@Database(
    entities = [
        GivingTransactionEntity::class,
        GivingCategoryEntity::class,
        ChurchEntity::class,
        NotificationEntity::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun givingTransactionDao(): GivingTransactionDao
    abstract fun givingCategoryDao(): GivingCategoryDao
    abstract fun churchDao(): ChurchDao
    abstract fun notificationDao(): NotificationDao
    
    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "altar_funds_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
