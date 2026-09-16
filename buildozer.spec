[app]
title = ZP Polytechnic Schedule
package.name = zppolytechnic
package.domain = org.zp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.3.0,xlrd,requests,urllib3,charset-normalizer,idna,certifi,setuptools
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
