[app]
title = BlackJack PvP
package.name = blackjackpvp
package.domain = org.example
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy
orientation = landscape
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Добавь эти строки:
android.api = 33
android.minapi = 21
android.ndk = 25.2.9519653
android.sdk = 33
android.build_tools = 33.0.2

[buildozer]
log_level = 2
warn_on_root = 0
