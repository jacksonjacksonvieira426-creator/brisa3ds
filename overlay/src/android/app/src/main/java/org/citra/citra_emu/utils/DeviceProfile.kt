// Copyright 2026 Brisa3DS contributors
// Licensed under GPLv2 or any later version
// Refer to the misc/licenses/gplv2.txt file included.

package org.citra.citra_emu.utils

import android.app.Activity
import android.app.ActivityManager
import android.content.Context
import android.os.Process
import android.widget.Toast
import org.citra.citra_emu.features.settings.model.BooleanSetting
import org.citra.citra_emu.features.settings.model.CitraSettings
import org.citra.citra_emu.features.settings.model.IntSetting
import org.citra.citra_emu.features.settings.utils.SettingsFile

/**
 * Picks a performance profile from the device's RAM, core count and GPU, applies it once on the
 * first launch, and falls back to the lightest profile when the app keeps dying during gameplay
 * (usually the Android low-memory killer).
 */
object DeviceProfile {
    enum class Tier { MINIMAL, LOW, MEDIUM, HIGH }

    private const val PREFS_NAME = "brisa3ds_profile"
    private const val KEY_APPLIED_VERSION = "applied_version"
    private const val KEY_SESSION_OPEN = "session_open"
    private const val KEY_UNCLEAN_COUNT = "unclean_count"
    private const val KEY_FORCE_MINIMAL = "force_minimal"
    private const val KEY_TIER = "tier"

    // Bump this to make every install re-apply the profile once after an update.
    private const val PROFILE_VERSION = 1

    // Consecutive sessions that ended without a clean exit before safe mode kicks in.
    private const val UNCLEAN_LIMIT = 2

    private const val GIB = 1024.0 * 1024.0 * 1024.0
    private const val GRAPHICS_API_OPENGL = 1

    // GPUs that either lack Vulkan or have poor Vulkan drivers. OpenGL ES is safer on these.
    private val LEGACY_GPU_PATTERNS = listOf(
        "Mali-4",
        "Mali-T",
        "Adreno (TM) 3",
        "Adreno (TM) 4",
        "PowerVR"
    )

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun detectTier(context: Context): Tier {
        val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val info = ActivityManager.MemoryInfo()
        am.getMemoryInfo(info)

        // totalMem is a little below the marketed size (a "4 GB" phone reports about 3.7 GiB).
        val ramGib = info.totalMem / GIB
        var tier = when {
            ramGib < 2.5 -> Tier.MINIMAL
            ramGib < 4.0 -> Tier.LOW
            ramGib < 6.0 -> Tier.MEDIUM
            else -> Tier.HIGH
        }

        val fewCores = Runtime.getRuntime().availableProcessors() <= 4
        if ((am.isLowRamDevice || fewCores) && tier != Tier.MINIMAL) {
            tier = Tier.values()[tier.ordinal - 1]
        }
        return tier
    }

    /** The tier chosen at the last profile apply, or a fresh detection if none was stored. */
    fun currentTier(context: Context): Tier {
        val stored = prefs(context).getString(KEY_TIER, null)
        return Tier.values().firstOrNull { it.name == stored } ?: detectTier(context)
    }

    /**
     * Call when a game starts. On weaker tiers this asks Android for sustained performance
     * mode, which keeps clocks steady instead of boosting and then throttling. Devices that
     * do not support it ignore the request.
     */
    fun applyRuntimeHints(activity: Activity) {
        if (currentTier(activity) == Tier.HIGH) {
            return
        }
        activity.window.setSustainedPerformanceMode(true)
    }

    private fun hasLegacyGpu(): Boolean {
        val renderer = GraphicsUtil.openGLRendererString
        return LEGACY_GPU_PATTERNS.any { renderer.contains(it, ignoreCase = true) }
    }

    private fun applyTier(settings: CitraSettings, tier: Tier, legacyGpu: Boolean) {
        if (tier == Tier.HIGH) {
            return
        }

        settings.setGlobal(IntSetting.RESOLUTION_FACTOR, 1)
        settings.setGlobal(IntSetting.TEXTURE_FILTER, 0)
        settings.setGlobal(BooleanSetting.ASYNC_SHADERS, true)
        settings.setGlobal(BooleanSetting.DISK_SHADER_CACHE, true)
        settings.setGlobal(BooleanSetting.SHADERS_ACCURATE_MUL, false)

        if (tier == Tier.MINIMAL) {
            // Old 3DS mode gives games the smaller memory layout. A few games need New 3DS and
            // will not run with this off; those can be fixed with a per-game setting.
            settings.setGlobal(BooleanSetting.NEW_3DS, false)
        }

        if (legacyGpu) {
            settings.setGlobal(IntSetting.GRAPHICS_API, GRAPHICS_API_OPENGL)
        }
    }

    /**
     * Call once at app start, after the global settings were loaded. Does nothing when the
     * profile was already applied, unless safe mode asked for a re-apply.
     */
    fun applyIfNeeded(context: Context, settings: CitraSettings) {
        val prefs = prefs(context)
        val forceMinimal = prefs.getBoolean(KEY_FORCE_MINIMAL, false)
        if (prefs.getInt(KEY_APPLIED_VERSION, 0) >= PROFILE_VERSION && !forceMinimal) {
            return
        }

        val tier = if (forceMinimal) Tier.MINIMAL else detectTier(context)
        applyTier(settings, tier, hasLegacyGpu())
        if (!Process.is64Bit()) {
            // The 32-bit build has no JIT recompiler, so it runs the interpreter.
            settings.setGlobal(BooleanSetting.CPU_JIT, false)
            settings.setGlobal(BooleanSetting.SHADER_JIT, false)
        }
        if (forceMinimal) {
            // Repeated crashes are often a Vulkan driver problem, so safe mode also moves to
            // OpenGL ES, whose drivers are the most widely tested.
            settings.setGlobal(IntSetting.GRAPHICS_API, GRAPHICS_API_OPENGL)
        }
        SettingsFile.saveGlobalFile(settings)

        prefs.edit()
            .putInt(KEY_APPLIED_VERSION, PROFILE_VERSION)
            .putString(KEY_TIER, tier.name)
            .putBoolean(KEY_FORCE_MINIMAL, false)
            .putInt(KEY_UNCLEAN_COUNT, 0)
            .apply()

        val message = if (forceMinimal) {
            "Brisa3DS: safe mode on, using the lightest settings"
        } else {
            "Brisa3DS: ${tier.name.lowercase()} profile applied"
        }
        Toast.makeText(context, message, Toast.LENGTH_LONG).show()
    }

    /** Call at app start, before [applyIfNeeded]. Detects sessions that died without exiting. */
    fun checkPreviousSession(context: Context) {
        val prefs = prefs(context)
        if (!prefs.getBoolean(KEY_SESSION_OPEN, false)) {
            return
        }

        val unclean = prefs.getInt(KEY_UNCLEAN_COUNT, 0) + 1
        val editor = prefs.edit().putBoolean(KEY_SESSION_OPEN, false)
        if (unclean >= UNCLEAN_LIMIT) {
            editor.putBoolean(KEY_FORCE_MINIMAL, true).putInt(KEY_UNCLEAN_COUNT, 0)
        } else {
            editor.putInt(KEY_UNCLEAN_COUNT, unclean)
        }
        editor.apply()
    }

    fun onSessionStart(context: Context) {
        // commit() so the flag is on disk even if the process is killed right after.
        prefs(context).edit().putBoolean(KEY_SESSION_OPEN, true).commit()
    }

    fun onSessionEnd(context: Context) {
        prefs(context).edit()
            .putBoolean(KEY_SESSION_OPEN, false)
            .putInt(KEY_UNCLEAN_COUNT, 0)
            .apply()
    }
}
