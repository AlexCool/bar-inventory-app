[app]
title = Bar Inventory
package.name = barinventory
package.domain = org.bar
source.dir = .
source.include_exts = py, kv, db
version = 0.1
requirements = python3, kivy==2.3.0, kivymd==1.1.1
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk/27.3.13750724
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1
# Важно: оставляем эти пути пустыми, чтобы Buildozer скачал свое
android.sdk_path = 
android.ndk_path =
