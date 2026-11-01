// Copyright 2026 Brisa3DS contributors
// Licensed under GPLv3 or any later version
// Refer to the LICENSE.txt file included.

package org.citra.citra_emu.utils

import android.app.ActivityManager
import android.content.Context
import android.os.Handler
import android.os.Looper
import java.util.Locale
import org.citra.citra_emu.NativeLibrary

/**
 * Writes one line with the frame timings to the emulator log every 10 seconds while a game runs,
 * so that "Share log" is enough to see where the time goes (GPU, system calls or the CPU) on a
 * given phone. It reads the same numbers as the performance overlay.
 */
object PerfLogger {
    private const val INTERVAL_MS = 10_000L
    private const val STAT_FPS = 1
    private const val STAT_SPEED = 2
    private const val STAT_FRAMETIME = 3
    private const val STAT_SVC = 4
    private const val STAT_IPC = 5
    private const val STAT_GPU = 6
    private const val STAT_SWAP = 7
    private const val STAT_REST = 8
    private const val STAT_COUNT = 9
    private const val MIB = 1024L * 1024L

    private val handler = Handler(Looper.getMainLooper())
    private var task: Runnable? = null

    fun start(context: Context) {
        if (task != null) {
            return
        }
        val appContext = context.applicationContext
        val newTask = object : Runnable {
            override fun run() {
                logOnce(appContext)
                handler.postDelayed(this, INTERVAL_MS)
            }
        }
        task = newTask
        handler.postDelayed(newTask, INTERVAL_MS)
    }

    fun stop() {
        task?.let { handler.removeCallbacks(it) }
        task = null
    }

    private fun logOnce(context: Context) {
        val stats = NativeLibrary.getPerfStats()
        if (stats.size < STAT_COUNT || stats[STAT_FPS] <= 0.0) {
            return
        }

        val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val info = ActivityManager.MemoryInfo()
        am.getMemoryInfo(info)

        // Times are in milliseconds. "rest" is mostly the emulated CPU.
        val line = String.format(
            Locale.US,
            "[Brisa3DS perf] fps=%.1f speed=%d%% frame=%.1f gpu=%.1f swap=%.1f ipc=%.1f " +
                "svc=%.1f rest=%.1f ram_free=%dMB",
            stats[STAT_FPS],
            (stats[STAT_SPEED] * 100.0 + 0.5).toInt(),
            stats[STAT_FRAMETIME] * 1000.0,
            stats[STAT_GPU] * 1000.0,
            stats[STAT_SWAP] * 1000.0,
            stats[STAT_IPC] * 1000.0,
            stats[STAT_SVC] * 1000.0,
            stats[STAT_REST] * 1000.0,
            info.availMem / MIB
        )
        Log.info(line)
    }
}
