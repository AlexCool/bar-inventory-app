[app]
title = Bar Inventory
package.name = barinventory
package.domain = org.bar
source.dir = .
source.include_exts = py, kv, db
version = 0.1
requirements = python3, kivy==2.3.0, kivymd==1.1.1, sqlite3
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.minapi = 21
android.api = 33
android.ndk_api = 21
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1